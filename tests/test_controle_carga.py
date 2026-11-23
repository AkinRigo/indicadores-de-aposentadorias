import hashlib

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DataError, IntegrityError

from etl.carregar import CargaDesatualizada, registrar_carga, verificar_atualizacao
from etl.extrair import ArquivoDivergente, conferir_arquivo

COMPETENCIA = "209912"
ETAG = "bc8079e4e736e3a09e605b9732d28d8e"
CARGA_VALIDA = {
    "competencia": COMPETENCIA,
    "arquivo": "CONCEDIDOS_DADOS+ABERTOS_DEZEMBRO+2099.xlsx",
    "etag": ETAG,
    "tamanho_bytes": 106_989_664,
    "linhas_carregadas": 99_850,
}


def contar(conn, competencia):
    return conn.execute(
        text("SELECT count(*) FROM controle_carga WHERE competencia = :c"), {"c": competencia}
    ).scalar_one()


def test_primeira_carga(conn):
    assert verificar_atualizacao(conn, COMPETENCIA, ETAG) == "nova"

    id_carga = registrar_carga(conn, **CARGA_VALIDA)

    assert id_carga > 0
    assert contar(conn, COMPETENCIA) == 1
    linha = conn.execute(
        text("SELECT etag, tamanho_bytes, linhas_carregadas, carregado_em FROM controle_carga WHERE id_carga = :id"),
        {"id": id_carga},
    ).one()
    assert linha.etag == ETAG
    assert linha.tamanho_bytes == 106_989_664
    assert linha.linhas_carregadas == 99_850
    assert linha.carregado_em is not None


def test_carga_duplicada_e_recusada(conn):
    registrar_carga(conn, **CARGA_VALIDA)

    with pytest.raises(IntegrityError):
        registrar_carga(conn, **CARGA_VALIDA)


@pytest.mark.parametrize(
    "campo, valor",
    [
        ("competencia", "209913"),
        ("competencia", "209900"),
        ("competencia", "2099-1"),
        ("competencia", "abcdef"),
        ("arquivo", "   "),
        ("etag", ""),
        ("tamanho_bytes", 0),
        ("tamanho_bytes", -1),
        ("linhas_carregadas", 0),
    ],
)
def test_dado_incorreto_e_recusado(conn, campo, valor):
    carga = {**CARGA_VALIDA, campo: valor}

    with pytest.raises((IntegrityError, DataError)):
        registrar_carga(conn, **carga)


def test_carga_em_dia_com_o_portal(conn):
    registrar_carga(conn, **CARGA_VALIDA)

    assert verificar_atualizacao(conn, COMPETENCIA, ETAG) == "em_dia"


def test_carga_desatualizada_avisa(conn):
    registrar_carga(conn, **CARGA_VALIDA)
    etag_nova_no_portal = "0" * 32

    with pytest.warns(CargaDesatualizada, match="não está de acordo com o portal do INSS"):
        assert verificar_atualizacao(conn, COMPETENCIA, etag_nova_no_portal) == "desatualizada"


@pytest.fixture
def arquivo_baixado(tmp_path):
    conteudo = b"conteudo de teste do arquivo do INSS"
    caminho = tmp_path / "CONCEDIDOS.xlsx"
    caminho.write_bytes(conteudo)
    return caminho, hashlib.md5(conteudo).hexdigest(), len(conteudo)


def test_cruzamento_arquivo_confere_com_portal(arquivo_baixado):
    caminho, md5, tamanho = arquivo_baixado

    assert conferir_arquivo(caminho, f'"{md5}"', tamanho) == md5


def test_cruzamento_tamanho_divergente_e_recusado(arquivo_baixado):
    caminho, md5, tamanho = arquivo_baixado

    with pytest.raises(ArquivoDivergente, match="tamanho"):
        conferir_arquivo(caminho, md5, tamanho + 1)


def test_cruzamento_md5_divergente_e_recusado(arquivo_baixado):
    caminho, _, tamanho = arquivo_baixado

    with pytest.raises(ArquivoDivergente, match="MD5"):
        conferir_arquivo(caminho, "0" * 32, tamanho)
