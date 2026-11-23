import os
import warnings
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

RAIZ = Path(__file__).resolve().parent.parent

COLUNAS_FATO_BANCO = [
    "id_carga", "competencia", "codigo_aps", "codigo_municipio", "codigo_despacho",
    "id_forma_filiacao", "id_ramo_atividade", "id_grau_instrucao",
    "sexo", "clientela", "ano_nascimento", "idade_na_dib",
    "dib", "ddb", "dcb", "qtd_salarios_minimos", "qt_anos_contribuicao",
]

UPSERTS = {
    "dim_agencia": (
        "INSERT INTO dim_agencia (codigo_aps, nome, uf) VALUES (:codigo_aps, :nome, :uf) "
        "ON CONFLICT (codigo_aps) DO UPDATE SET nome = EXCLUDED.nome, uf = EXCLUDED.uf"
    ),
    "dim_municipio": (
        "INSERT INTO dim_municipio (codigo_municipio, nome) VALUES (:codigo_municipio, :nome) "
        "ON CONFLICT (codigo_municipio) DO UPDATE SET nome = EXCLUDED.nome"
    ),
    "dim_despacho": (
        "INSERT INTO dim_despacho (codigo_despacho, nome) VALUES (:codigo_despacho, :nome) "
        "ON CONFLICT (codigo_despacho) DO UPDATE SET nome = EXCLUDED.nome"
    ),
    "dim_forma_filiacao": (
        "INSERT INTO dim_forma_filiacao (id, descricao) VALUES (:id, :descricao) "
        "ON CONFLICT (id) DO UPDATE SET descricao = EXCLUDED.descricao"
    ),
    "dim_ramo_atividade": (
        "INSERT INTO dim_ramo_atividade (descricao) VALUES (:descricao) "
        "ON CONFLICT (descricao) DO NOTHING"
    ),
    "dim_grau_instrucao": (
        "INSERT INTO dim_grau_instrucao (codigo, descricao) VALUES (:codigo, :descricao) "
        "ON CONFLICT (codigo) DO UPDATE SET descricao = EXCLUDED.descricao"
    ),
}


class CargaDesatualizada(UserWarning):
    pass


class CargaInconsistente(Exception):
    pass


def url_banco():
    load_dotenv(RAIZ / ".env")
    url = os.environ["DATABASE_URL"]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


def criar_engine():
    return create_engine(url_banco())


def registrar_carga(conn, competencia, arquivo, etag, tamanho_bytes, linhas_carregadas):
    return conn.execute(
        text(
            """
            INSERT INTO controle_carga (competencia, arquivo, etag, tamanho_bytes, linhas_carregadas)
            VALUES (:competencia, :arquivo, :etag, :tamanho_bytes, :linhas_carregadas)
            RETURNING id_carga
            """
        ),
        {
            "competencia": competencia,
            "arquivo": arquivo,
            "etag": etag,
            "tamanho_bytes": tamanho_bytes,
            "linhas_carregadas": linhas_carregadas,
        },
    ).scalar_one()


def verificar_atualizacao(conn, competencia, etag_portal):
    etag_banco = conn.execute(
        text("SELECT etag FROM controle_carga WHERE competencia = :competencia"),
        {"competencia": competencia},
    ).scalar_one_or_none()

    if etag_banco is None:
        return "nova"
    if etag_banco == etag_portal:
        return "em_dia"

    warnings.warn(
        f"Competência {competencia} desatualizada: a ETag no banco ({etag_banco}) "
        f"não está de acordo com o portal do INSS ({etag_portal})",
        CargaDesatualizada,
    )
    return "desatualizada"


def apagar_carga(conn, competencia):
    conn.execute(
        text(
            "DELETE FROM fato_concessao WHERE id_carga IN "
            "(SELECT id_carga FROM controle_carga WHERE competencia = :c)"
        ),
        {"c": competencia},
    )
    conn.execute(text("DELETE FROM controle_carga WHERE competencia = :c"), {"c": competencia})


def para_registros(df):
    return df.astype(object).where(df.notna(), None).to_dict("records")


def gravar_dimensoes(conn, dimensoes):
    for tabela, sql in UPSERTS.items():
        conn.execute(text(sql), para_registros(dimensoes[tabela]))


def mapa(conn, tabela, chave):
    return dict(conn.execute(text(f"SELECT {chave}, id FROM {tabela}")).all())


def gravar_fato(conn, fato, id_carga):
    fato = fato.copy()
    fato["id_carga"] = id_carga
    fato["id_ramo_atividade"] = fato["ramo_atividade"].map(mapa(conn, "dim_ramo_atividade", "descricao"))
    fato["id_grau_instrucao"] = fato["codigo_grau_instrucao"].map(mapa(conn, "dim_grau_instrucao", "codigo"))
    for coluna in ("dib", "ddb", "dcb"):
        fato[coluna] = fato[coluna].dt.date
    fato = fato[COLUNAS_FATO_BANCO]

    colunas = [fato[c].astype(object).where(fato[c].notna(), None).tolist() for c in COLUNAS_FATO_BANCO]
    cursor = conn.connection.driver_connection.cursor()
    with cursor.copy(f"COPY fato_concessao ({', '.join(COLUNAS_FATO_BANCO)}) FROM STDIN") as copia:
        for linha in zip(*colunas):
            copia.write_row(linha)


def carregar_competencia(conn, competencia, extraido, transformado):
    fato = transformado["fato"]
    competencias = set(fato["competencia"].unique())
    if competencias != {competencia}:
        raise CargaInconsistente(f"O arquivo traz as competências {competencias}, esperado {competencia}")

    status = verificar_atualizacao(conn, competencia, extraido["etag"])
    if status == "em_dia":
        return {"status": status, "linhas": 0}
    if status == "desatualizada":
        apagar_carga(conn, competencia)

    gravar_dimensoes(conn, transformado["dimensoes"])
    id_carga = registrar_carga(
        conn, competencia, extraido["arquivo"], extraido["etag"], extraido["tamanho"], len(fato)
    )
    gravar_fato(conn, fato, id_carga)

    gravadas = conn.execute(
        text("SELECT count(*) FROM fato_concessao WHERE id_carga = :id"), {"id": id_carga}
    ).scalar_one()
    if gravadas != len(fato):
        raise CargaInconsistente(f"Gravadas {gravadas} linhas, esperado {len(fato)}")
    return {"status": status, "id_carga": id_carga, "linhas": gravadas}
