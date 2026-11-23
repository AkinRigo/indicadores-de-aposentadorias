from datetime import datetime

import openpyxl
import pandas as pd
import pytest

from etl import transformar as t


def linha(**mudancas):
    base = {
        "APS Concessão (Código)": "04022070",
        "APS Concessão (Nome)": "AGÊNCIA DA PREVIDÊNCIA SOCIAL ITABERABA",
        "Competência Concessão": "202610",
        "Espécie (Código)": "041",
        "Espécie (Nome)": "APOSENTADORIA POR IDADE",
        "CID 10 (Código)": "000000",
        "CID 10 (Nome)": "ZERADO",
        "Despacho (Código)": "000",
        "Despacho (Nome)": "CONCESSAO NORMAL",
        "Data Nascimento Titular": datetime(1961, 5, 20),
        "Sexo Titular (Nome)": "FEMININO",
        "Clientela (Nome)": "URBANA",
        "Município Resid Titular (Código e Nome)": "21504 - SAO PAULO",
        "Vínculo Dependente Recebedor (Nome)": "NÃO INFORMADO",
        "Forma Filiação (Nome)": "8 - AUTONOMO",
        "UF (Nome)": "BAHIA",
        "Quantidade Salários Mínimos - RMI": 4.3129999999999997,
        "Ramo Atividade (Nome)": "COMERCIARIO",
        "DCB - Data Cessação Benefício": None,
        "DDB - Data Despacho Benefício": datetime(2026, 10, 1),
        "DIB - Data Início Benefício": datetime(2026, 5, 19),
        "País Acordo Internacional (Nome)": "NÃO INFORMADO",
        "Classificador de PA (Nome)": "00 - SEM PENSÃO ALIMENTÍCIA",
        "CNAE 2.0": "9999",
        "Grau Instrução (Nome)": "05 - FUNDAMENTAL COMPLETO",
        "Qt Anos Contribuição": 15,
    }
    base.update(mudancas)
    return base


def planilha(*linhas):
    return pd.DataFrame(list(linhas))


def test_ler_planilha_pula_titulo_e_linha_vazia(tmp_path):
    caminho = tmp_path / "concedidos.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    dados = linha()
    ws.append(["CONCEDIDOS - DADOS ABERTOS - OUTUBRO DE 2026"])
    ws.append(list(dados))
    ws.append(list(dados.values()))
    ws.append([])
    wb.save(caminho)

    df = t.ler_planilha(caminho)

    assert len(df) == 1
    assert df.columns[0] == "APS Concessão (Código)"
    assert df.iloc[0]["Espécie (Código)"] == "041"


def test_filtrar_especie_mantem_so_041():
    df = planilha(linha(), linha(**{"Espécie (Código)": "080"}), linha(**{"Espécie (Código)": "41"}))

    assert len(t.filtrar_especie(df)) == 2


def test_para_data_aceita_data_serial_e_vazio():
    serie = pd.Series([datetime(2026, 10, 1), "46296", "", None], dtype=object)

    datas = t.para_data(serie)

    assert datas[0] == pd.Timestamp(2026, 10, 1)
    assert datas[1] == pd.Timestamp(2026, 10, 1)
    assert pd.isna(datas[2]) and pd.isna(datas[3])


def test_separar_codigo_e_nome():
    codigo, nome = t.separar_codigo(pd.Series(["21504 - SAO PAULO", "05045 - FORTALEZA"]))

    assert codigo.tolist() == ["21504", "05045"]
    assert nome.tolist() == ["SAO PAULO", "FORTALEZA"]


@pytest.mark.parametrize(
    "nascimento, data, esperado",
    [
        (datetime(1961, 5, 20), datetime(2026, 5, 19), 64),
        (datetime(1961, 5, 20), datetime(2026, 5, 20), 65),
        (datetime(1961, 5, 20), datetime(2026, 12, 31), 65),
    ],
)
def test_idade_considera_se_ja_fez_aniversario(nascimento, data, esperado):
    idade = t.idade_em(pd.Series([pd.Timestamp(nascimento)]), pd.Series([pd.Timestamp(data)]))

    assert idade[0] == esperado


def test_normalizar_formata_campos():
    df = planilha(linha(**{"APS Concessão (Código)": "4022070", "Despacho (Código)": "4"}))

    n = t.normalizar(df).iloc[0]

    assert n["codigo_aps"] == "04022070"
    assert n["codigo_despacho"] == "004"
    assert n["codigo_municipio"] == "21504" and n["nome_municipio"] == "SAO PAULO"
    assert n["id_forma_filiacao"] == 8 and n["forma_filiacao"] == "AUTONOMO"
    assert n["codigo_grau_instrucao"] == "05" and n["grau_instrucao"] == "FUNDAMENTAL COMPLETO"
    assert n["qtd_salarios_minimos"] == 4.31
    assert n["ano_nascimento"] == 1961
    assert n["idade_na_dib"] == 64
    assert pd.isna(n["dcb"])


def test_linha_valida_e_aceita():
    resultado = t.transformar(planilha(linha()))

    assert len(resultado["fato"]) == 1
    assert len(resultado["rejeitadas"]) == 0
    assert resultado["linhas_origem"] == 1
    assert list(resultado["fato"].columns) == t.COLUNAS_FATO


def test_idade_abaixo_do_minimo_e_rejeitada():
    jovem = linha(**{"Data Nascimento Titular": datetime(1990, 1, 1)})
    nasceu_depois = linha(**{"Data Nascimento Titular": datetime(2026, 8, 1)})

    resultado = t.transformar(planilha(linha(), jovem, nasceu_depois))

    assert len(resultado["fato"]) == 1
    assert resultado["rejeitadas"]["motivo"].tolist() == ["idade_implausivel", "idade_implausivel"]


def test_duplicada_mantem_a_primeira():
    resultado = t.transformar(planilha(linha(), linha(), linha()))

    assert len(resultado["fato"]) == 1
    assert resultado["rejeitadas"]["motivo"].tolist() == ["duplicada", "duplicada"]


def test_diferenca_so_em_coluna_descartada_nao_e_duplicada():
    outro_dia = linha(**{"Data Nascimento Titular": datetime(1961, 5, 21)})
    outro_vinculo = linha(**{"Vínculo Dependente Recebedor (Nome)": "FILHO"})

    resultado = t.transformar(planilha(linha(), outro_dia, outro_vinculo))

    assert len(resultado["fato"]) == 3
    assert len(resultado["rejeitadas"]) == 0


def test_dado_obrigatorio_ausente_e_rejeitado():
    sem_dib = linha(**{"DIB - Data Início Benefício": None})

    resultado = t.transformar(planilha(linha(), sem_dib))

    assert len(resultado["fato"]) == 1
    assert resultado["rejeitadas"]["motivo"].tolist() == ["dado_ausente"]


def test_dcb_vazia_nao_rejeita():
    cessado = linha(**{"DCB - Data Cessação Benefício": datetime(2026, 10, 20)})

    resultado = t.transformar(planilha(linha(), cessado))

    assert len(resultado["fato"]) == 2
    assert resultado["fato"]["dcb"].isna().sum() == 1


def test_dimensoes_sem_repeticao_e_com_nome_mais_comum():
    df = planilha(
        linha(),
        linha(**{"Município Resid Titular (Código e Nome)": "18002 - ACU", "Qt Anos Contribuição": 16}),
        linha(**{"Município Resid Titular (Código e Nome)": "18002 - ASSU", "Qt Anos Contribuição": 17}),
        linha(**{"Município Resid Titular (Código e Nome)": "18002 - ASSU", "Qt Anos Contribuição": 18}),
    )

    dims = t.transformar(df)["dimensoes"]

    municipios = dims["dim_municipio"].set_index("codigo_municipio")["nome"].to_dict()
    assert municipios == {"18002": "ASSU", "21504": "SAO PAULO"}
    assert dims["dim_agencia"].to_dict("records") == [
        {"codigo_aps": "04022070", "nome": "AGÊNCIA DA PREVIDÊNCIA SOCIAL ITABERABA", "uf": "BAHIA"}
    ]
    assert dims["dim_forma_filiacao"].to_dict("records") == [{"id": 8, "descricao": "AUTONOMO"}]
    assert len(dims["dim_ramo_atividade"]) == 1
    assert len(dims["dim_grau_instrucao"]) == 1
