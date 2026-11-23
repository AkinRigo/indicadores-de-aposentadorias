import requests

URL_PACOTE = (
    "https://dadosabertos.inss.gov.br/api/3/action/package_show"
    "?id=beneficios-concedidos-plano-de-dados-abertos-jun-2023-a-dez-2027"
)
TIMEOUT = 30

MESES = {
    "janeiro": "01", "fevereiro": "02", "março": "03", "marco": "03",
    "abril": "04", "maio": "05", "junho": "06", "julho": "07",
    "agosto": "08", "setembro": "09", "outubro": "10",
    "novembro": "11", "dezembro": "12",
}


class RecursoNaoEncontrado(Exception):
    pass


def listar_recursos():
    resposta = requests.get(URL_PACOTE, timeout=TIMEOUT)
    resposta.raise_for_status()
    dados = resposta.json()
    if not dados.get("success"):
        raise RuntimeError("A API do CKAN do INSS respondeu sem sucesso")
    return dados["result"]["resources"]


def competencia_do_nome(nome):
    partes = nome.lower().split()
    if len(partes) < 2:
        return None
    mes, ano = partes[-2], partes[-1]
    if mes not in MESES or not (ano.isdigit() and len(ano) == 4):
        return None
    return ano + MESES[mes]


def metadados_do_arquivo(url):
    resposta = requests.head(url, timeout=TIMEOUT, allow_redirects=True)
    resposta.raise_for_status()
    return {
        "etag": resposta.headers["ETag"].strip('"'),
        "tamanho": int(resposta.headers["Content-Length"]),
    }


def recurso_da_competencia(competencia):
    for recurso in listar_recursos():
        if competencia_do_nome(recurso["name"]) == competencia:
            return {
                "competencia": competencia,
                "nome": recurso["name"],
                "url": recurso["url"],
                **metadados_do_arquivo(recurso["url"]),
            }
    raise RecursoNaoEncontrado(f"Competência {competencia} não encontrada no portal do INSS")
