import pandas as pd

ESPECIE = "041"
IDADE_MINIMA = 50

ORIGEM = {
    "codigo_aps": "APS Concessão (Código)",
    "nome_aps": "APS Concessão (Nome)",
    "uf": "UF (Nome)",
    "competencia": "Competência Concessão",
    "especie": "Espécie (Código)",
    "codigo_despacho": "Despacho (Código)",
    "nome_despacho": "Despacho (Nome)",
    "nascimento": "Data Nascimento Titular",
    "sexo": "Sexo Titular (Nome)",
    "clientela": "Clientela (Nome)",
    "municipio": "Município Resid Titular (Código e Nome)",
    "forma_filiacao": "Forma Filiação (Nome)",
    "rmi": "Quantidade Salários Mínimos - RMI",
    "ramo_atividade": "Ramo Atividade (Nome)",
    "dcb": "DCB - Data Cessação Benefício",
    "ddb": "DDB - Data Despacho Benefício",
    "dib": "DIB - Data Início Benefício",
    "grau_instrucao": "Grau Instrução (Nome)",
    "anos_contribuicao": "Qt Anos Contribuição",
}

COLUNAS_FATO = [
    "competencia", "codigo_aps", "codigo_municipio", "codigo_despacho",
    "id_forma_filiacao", "ramo_atividade", "codigo_grau_instrucao",
    "sexo", "clientela", "ano_nascimento", "idade_na_dib",
    "dib", "ddb", "dcb", "qtd_salarios_minimos", "qt_anos_contribuicao",
]


def ler_planilha(caminho):
    bruto = pd.read_excel(caminho, header=None, engine="calamine")
    linha = bruto.index[bruto.iloc[:, 0].astype(str).str.startswith("APS Concessão")][0]
    df = bruto.iloc[linha + 1:].copy()
    df.columns = bruto.iloc[linha].tolist()
    return df.dropna(how="all").reset_index(drop=True)


def texto(serie):
    return serie.astype("string").str.strip()


def para_data(serie):
    if pd.api.types.is_datetime64_any_dtype(serie):
        return serie
    serie = serie.astype(object).replace("", None)
    numeros = pd.to_numeric(serie, errors="coerce")
    datas = pd.to_datetime(serie.where(numeros.isna()), errors="coerce")
    seriais = pd.to_datetime(numeros, unit="D", origin="1899-12-30")
    return datas.fillna(seriais)


def separar_codigo(serie):
    partes = texto(serie).str.split(" - ", n=1, expand=True)
    return partes[0].str.strip(), partes[1].str.strip()


def idade_em(nascimento, data):
    ainda_nao_fez = (data.dt.month < nascimento.dt.month) | (
        (data.dt.month == nascimento.dt.month) & (data.dt.day < nascimento.dt.day)
    )
    return data.dt.year - nascimento.dt.year - ainda_nao_fez.astype(int)


def filtrar_especie(df, especie=ESPECIE):
    return df[texto(df[ORIGEM["especie"]]).str.zfill(3) == especie].reset_index(drop=True)


def normalizar(df):
    o = ORIGEM
    n = pd.DataFrame(index=df.index)
    n["competencia"] = texto(df[o["competencia"]])
    n["codigo_aps"] = texto(df[o["codigo_aps"]]).str.zfill(8)
    n["nome_aps"] = texto(df[o["nome_aps"]])
    n["uf"] = texto(df[o["uf"]])
    n["codigo_despacho"] = texto(df[o["codigo_despacho"]]).str.zfill(3)
    n["nome_despacho"] = texto(df[o["nome_despacho"]])
    n["codigo_municipio"], n["nome_municipio"] = separar_codigo(df[o["municipio"]])
    codigo_forma, n["forma_filiacao"] = separar_codigo(df[o["forma_filiacao"]])
    n["id_forma_filiacao"] = pd.to_numeric(codigo_forma, errors="coerce").astype("Int64")
    n["ramo_atividade"] = texto(df[o["ramo_atividade"]])
    n["codigo_grau_instrucao"], n["grau_instrucao"] = separar_codigo(df[o["grau_instrucao"]])
    n["sexo"] = texto(df[o["sexo"]]).str.upper()
    n["clientela"] = texto(df[o["clientela"]]).str.upper()

    nascimento = para_data(df[o["nascimento"]])
    n["dib"] = para_data(df[o["dib"]])
    n["ddb"] = para_data(df[o["ddb"]])
    n["dcb"] = para_data(df[o["dcb"]])
    n["ano_nascimento"] = nascimento.dt.year.astype("Int64")
    n["idade_na_dib"] = idade_em(nascimento, n["dib"]).astype("Int64")

    n["qtd_salarios_minimos"] = pd.to_numeric(df[o["rmi"]], errors="coerce").round(2)
    n["qt_anos_contribuicao"] = pd.to_numeric(df[o["anos_contribuicao"]], errors="coerce").astype("Int64")
    return n


def separar_rejeitadas(n, duplicadas):
    obrigatorias = [c for c in COLUNAS_FATO if c != "dcb"]
    motivo = pd.Series(pd.NA, index=n.index, dtype="string")
    motivo[n[obrigatorias].isna().any(axis=1)] = "dado_ausente"
    motivo[motivo.isna() & (n["idade_na_dib"] < IDADE_MINIMA)] = "idade_implausivel"
    motivo[motivo.isna() & duplicadas] = "duplicada"

    rejeitadas = n[motivo.notna()].assign(motivo=motivo[motivo.notna()])
    return n[motivo.isna()].reset_index(drop=True), rejeitadas.reset_index(drop=True)


def montar_dimensoes(n):
    nome_mais_comum = lambda s: s.value_counts().index[0]
    return {
        "dim_agencia": n.groupby("codigo_aps", as_index=False)
        .agg(nome=("nome_aps", nome_mais_comum), uf=("uf", nome_mais_comum)),
        "dim_municipio": n.groupby("codigo_municipio", as_index=False)
        .agg(nome=("nome_municipio", nome_mais_comum)),
        "dim_despacho": n.groupby("codigo_despacho", as_index=False)
        .agg(nome=("nome_despacho", nome_mais_comum)),
        "dim_forma_filiacao": n.groupby("id_forma_filiacao", as_index=False)
        .agg(descricao=("forma_filiacao", nome_mais_comum))
        .rename(columns={"id_forma_filiacao": "id"}),
        "dim_ramo_atividade": n[["ramo_atividade"]].drop_duplicates()
        .rename(columns={"ramo_atividade": "descricao"}),
        "dim_grau_instrucao": n.groupby("codigo_grau_instrucao", as_index=False)
        .agg(descricao=("grau_instrucao", nome_mais_comum))
        .rename(columns={"codigo_grau_instrucao": "codigo"}),
    }


def transformar(df_bruto, especie=ESPECIE):
    filtrado = filtrar_especie(df_bruto, especie)
    duplicadas = filtrado.astype(str).duplicated(keep="first")
    normalizado = normalizar(filtrado)
    aceitas, rejeitadas = separar_rejeitadas(normalizado, duplicadas)
    return {
        "dimensoes": montar_dimensoes(aceitas),
        "fato": aceitas[COLUNAS_FATO],
        "rejeitadas": rejeitadas,
        "linhas_origem": len(normalizado),
    }
