from datetime import date, datetime
from decimal import Decimal

import pandas as pd
import pytest
from alembic.script import ScriptDirectory
from sqlalchemy import text

from etl import transformar as t
from etl.extrair import PASTA_RAW, md5_arquivo

from conftest import RAIZ


@pytest.fixture
def cargas(conn):
    linhas = conn.execute(text("SELECT * FROM controle_carga")).mappings().all()
    if not linhas:
        pytest.skip("Banco sem carga: rode python -m etl AAAAMM antes")
    return linhas


def contar(conn, sql):
    return conn.execute(text(sql)).scalar_one()


# 1 - Precisão e conformidade

OBRIGATORIAS = [
    "id_carga", "competencia", "codigo_aps", "codigo_municipio", "codigo_despacho",
    "id_forma_filiacao", "id_ramo_atividade", "id_grau_instrucao", "sexo", "clientela",
    "ano_nascimento", "idade_na_dib", "dib", "ddb", "qtd_salarios_minimos", "qt_anos_contribuicao",
]


@pytest.mark.parametrize("coluna", OBRIGATORIAS)
def test_sem_valor_ausente(conn, cargas, coluna):
    assert contar(conn, f"SELECT count(*) FROM fato_concessao WHERE {coluna} IS NULL") == 0


@pytest.mark.parametrize(
    "tabela, coluna, formato",
    [
        ("fato_concessao", "competencia", "^[0-9]{4}(0[1-9]|1[0-2])$"),
        ("fato_concessao", "codigo_aps", "^[0-9]{8}$"),
        ("fato_concessao", "codigo_municipio", "^[0-9]{5}$"),
        ("fato_concessao", "codigo_despacho", "^[0-9]{3}$"),
        ("dim_grau_instrucao", "codigo", "^[0-9]{2}$"),
    ],
)
def test_formato_dos_codigos(conn, cargas, tabela, coluna, formato):
    assert contar(conn, f"SELECT count(*) FROM {tabela} WHERE {coluna} !~ '{formato}'") == 0


@pytest.mark.parametrize(
    "regra, condicao_invalida",
    [
        ("idade entre o mínimo e 120", f"idade_na_dib NOT BETWEEN {t.IDADE_MINIMA} AND 120"),
        ("nascimento entre 1900 e a DIB", "ano_nascimento NOT BETWEEN 1900 AND extract(year FROM dib)"),
        ("idade bate com o ano de nascimento",
         "extract(year FROM dib) - ano_nascimento - idade_na_dib NOT IN (0, 1)"),
        ("RMI entre 0,01 e 100 salários", "qtd_salarios_minimos NOT BETWEEN 0.01 AND 100"),
        ("despacho não antes do início", "ddb < dib"),
        ("despacho dentro da competência", "to_char(ddb, 'YYYYMM') <> competencia"),
        ("cessação não antes do início", "dcb < dib"),
    ],
)
def test_valores_dentro_do_intervalo(conn, cargas, regra, condicao_invalida):
    assert contar(conn, f"SELECT count(*) FROM fato_concessao WHERE {condicao_invalida}") == 0, regra


@pytest.mark.parametrize(
    "tabela, coluna",
    [
        ("dim_agencia", "nome"), ("dim_agencia", "uf"), ("dim_municipio", "nome"),
        ("dim_despacho", "nome"), ("dim_forma_filiacao", "descricao"),
        ("dim_ramo_atividade", "descricao"), ("dim_grau_instrucao", "descricao"),
    ],
)
def test_dimensao_sem_texto_vazio(conn, cargas, tabela, coluna):
    assert contar(conn, f"SELECT count(*) FROM {tabela} WHERE {coluna} IS NULL OR trim({coluna}) = ''") == 0


# 2 - Integridade referencial

def test_banco_na_ultima_migracao(conn):
    cabeca = ScriptDirectory(str(RAIZ / "migrations")).get_current_head()

    assert contar(conn, "SELECT version_num FROM alembic_version") == cabeca


def test_fato_tem_as_7_chaves_estrangeiras(conn):
    fks = conn.execute(
        text(
            "SELECT confrelid::regclass::text FROM pg_constraint "
            "WHERE conrelid = 'fato_concessao'::regclass AND contype = 'f'"
        )
    ).scalars().all()

    assert sorted(fks) == sorted([
        "controle_carga", "dim_agencia", "dim_municipio", "dim_despacho",
        "dim_forma_filiacao", "dim_ramo_atividade", "dim_grau_instrucao",
    ])


def consultas_do_arquivo():
    blocos = (RAIZ / "sql" / "02_integridade.sql").read_text(encoding="utf-8").split(";")
    consultas = [b.strip() for b in blocos if b.strip()]
    return [pytest.param(c, id=c.splitlines()[0].lstrip("- ")) for c in consultas]


@pytest.mark.parametrize("consulta", consultas_do_arquivo())
def test_consultas_de_integridade_voltam_vazias(conn, cargas, consulta):
    assert conn.execute(text(consulta)).all() == []


def test_competencia_da_fato_bate_com_a_carga(conn, cargas):
    assert contar(
        conn,
        "SELECT count(*) FROM fato_concessao f JOIN controle_carga c USING (id_carga) "
        "WHERE f.competencia <> c.competencia",
    ) == 0


# 3 - Detecção de anomalias

def test_linhas_gravadas_batem_com_o_controle(conn, cargas):
    for carga in cargas:
        gravadas = contar(conn, f"SELECT count(*) FROM fato_concessao WHERE id_carga = {carga['id_carga']}")
        assert gravadas == carga["linhas_carregadas"], carga["competencia"]


def test_carga_nao_esta_no_futuro(conn, cargas):
    assert contar(conn, "SELECT count(*) FROM controle_carga WHERE carregado_em > now()") == 0


def arquivo_local(carga):
    caminho = PASTA_RAW / carga["arquivo"]
    if not caminho.exists():
        pytest.skip(f"Arquivo {carga['arquivo']} não está em data/raw")
    return caminho


def test_arquivo_local_nao_foi_alterado(cargas):
    for carga in cargas:
        assert md5_arquivo(arquivo_local(carga)) == carga["etag"], carga["arquivo"]


def assinatura(df):
    def valor(v):
        if v is None or v is pd.NA or v is pd.NaT or (isinstance(v, float) and pd.isna(v)):
            return ""
        if isinstance(v, (pd.Timestamp, datetime)):
            return v.date().isoformat()
        if isinstance(v, date):
            return v.isoformat()
        if isinstance(v, (float, Decimal)):
            return f"{v:.2f}"
        return str(v)

    return df.astype(object).map(valor).value_counts()


def test_banco_igual_ao_arquivo_oficial(conn, cargas):
    for carga in cargas:
        esperado = t.transformar(t.ler_planilha(arquivo_local(carga)))["fato"]
        banco = pd.DataFrame(
            conn.execute(
                text(
                    "SELECT f.competencia, f.codigo_aps, f.codigo_municipio, f.codigo_despacho, "
                    "f.id_forma_filiacao, r.descricao AS ramo_atividade, g.codigo AS codigo_grau_instrucao, "
                    "f.sexo, f.clientela, f.ano_nascimento, f.idade_na_dib, f.dib, f.ddb, f.dcb, "
                    "f.qtd_salarios_minimos, f.qt_anos_contribuicao "
                    "FROM fato_concessao f "
                    "JOIN dim_ramo_atividade r ON r.id = f.id_ramo_atividade "
                    "JOIN dim_grau_instrucao g ON g.id = f.id_grau_instrucao "
                    "WHERE f.id_carga = :id"
                ),
                {"id": carga["id_carga"]},
            ).all(),
            columns=t.COLUNAS_FATO,
        )

        diferenca = assinatura(banco).sub(assinatura(esperado), fill_value=0)
        assert (diferenca == 0).all(), diferenca[diferenca != 0].head(10)
