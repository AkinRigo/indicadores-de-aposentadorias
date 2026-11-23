import pytest
import requests

from api import ckan

URL_OUTUBRO = "https://exemplo.s3/CONCEDIDOS_DADOS+ABERTOS_OUTUBRO+2026.xlsx"
RECURSOS = [
    {"name": "Benefícios concedidos Setembro 2026", "url": "https://exemplo.s3/setembro.xlsx"},
    {"name": "Benefícios concedidos Outubro 2026", "url": URL_OUTUBRO},
]


class RespostaFalsa:
    def __init__(self, status=200, json=None, headers=None):
        self.status_code = status
        self._json = json
        self.headers = headers or {}

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


@pytest.fixture
def portal(monkeypatch):
    chamadas = {"get": [], "head": []}

    def get_falso(url, timeout):
        chamadas["get"].append(url)
        return RespostaFalsa(json={"success": True, "result": {"resources": RECURSOS}})

    def head_falso(url, timeout, allow_redirects):
        chamadas["head"].append(url)
        return RespostaFalsa(headers={"ETag": '"bc8079e4e736e3a09e605b9732d28d8e"', "Content-Length": "106989664"})

    monkeypatch.setattr(ckan.requests, "get", get_falso)
    monkeypatch.setattr(ckan.requests, "head", head_falso)
    return chamadas


def test_listar_recursos(portal):
    recursos = ckan.listar_recursos()

    assert recursos == RECURSOS
    assert portal["get"] == [ckan.URL_PACOTE]


def test_listar_recursos_sem_sucesso(monkeypatch):
    monkeypatch.setattr(ckan.requests, "get", lambda url, timeout: RespostaFalsa(json={"success": False}))

    with pytest.raises(RuntimeError):
        ckan.listar_recursos()


def test_listar_recursos_erro_http(monkeypatch):
    monkeypatch.setattr(ckan.requests, "get", lambda url, timeout: RespostaFalsa(status=503))

    with pytest.raises(requests.HTTPError):
        ckan.listar_recursos()


@pytest.mark.parametrize(
    "nome, esperado",
    [
        ("Benefícios concedidos Outubro 2026", "202610"),
        ("Benefícios concedidos Março 2024", "202403"),
        ("Benefícios concedidos Marco 2024", "202403"),
        ("Benefícios concedidos JANEIRO 2025", "202501"),
        ("Benefícios concedidos 2026", None),
        ("Benefícios concedidos Outubro 26", None),
        ("Glossário", None),
    ],
)
def test_competencia_do_nome(nome, esperado):
    assert ckan.competencia_do_nome(nome) == esperado


def test_metadados_do_arquivo(portal):
    metadados = ckan.metadados_do_arquivo(URL_OUTUBRO)

    assert metadados == {"etag": "bc8079e4e736e3a09e605b9732d28d8e", "tamanho": 106989664}
    assert portal["head"] == [URL_OUTUBRO]


def test_recurso_da_competencia(portal):
    recurso = ckan.recurso_da_competencia("202610")

    assert recurso == {
        "competencia": "202610",
        "nome": "Benefícios concedidos Outubro 2026",
        "url": URL_OUTUBRO,
        "etag": "bc8079e4e736e3a09e605b9732d28d8e",
        "tamanho": 106989664,
    }
    assert portal["head"] == [URL_OUTUBRO]


def test_recurso_da_competencia_inexistente(portal):
    with pytest.raises(ckan.RecursoNaoEncontrado, match="209912"):
        ckan.recurso_da_competencia("209912")

    assert portal["head"] == []
