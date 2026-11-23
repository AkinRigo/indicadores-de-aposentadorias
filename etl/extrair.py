import hashlib
import json
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests

from api.ckan import recurso_da_competencia

PASTA_RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
TIMEOUT_DOWNLOAD = 120


class ArquivoDivergente(Exception):
    pass


def md5_arquivo(caminho):
    h = hashlib.md5()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloco)
    return h.hexdigest()


def conferir_arquivo(caminho, etag_portal, tamanho_portal):
    caminho = Path(caminho)
    tamanho = caminho.stat().st_size
    if tamanho != tamanho_portal:
        raise ArquivoDivergente(
            f"{caminho.name}: tamanho local {tamanho} difere do portal do INSS ({tamanho_portal})"
        )
    md5 = md5_arquivo(caminho)
    etag = etag_portal.strip('"')
    if md5 != etag:
        raise ArquivoDivergente(
            f"{caminho.name}: MD5 local {md5} difere da ETag do portal do INSS ({etag})"
        )
    return md5


def nome_do_arquivo(url):
    return unquote(Path(urlparse(url).path).name)


def baixar(url, destino):
    parcial = destino.with_name(destino.name + ".parcial")
    with requests.get(url, stream=True, timeout=TIMEOUT_DOWNLOAD) as resposta:
        resposta.raise_for_status()
        with open(parcial, "wb") as f:
            for bloco in resposta.iter_content(1024 * 1024):
                f.write(bloco)
    parcial.replace(destino)


def atualizar_manifesto(pasta, competencia, dados):
    manifesto = pasta / "manifesto.json"
    conteudo = json.loads(manifesto.read_text(encoding="utf-8")) if manifesto.exists() else {}
    conteudo[competencia] = dados
    manifesto.write_text(json.dumps(conteudo, ensure_ascii=False, indent=2), encoding="utf-8")


def extrair(competencia, pasta=PASTA_RAW):
    recurso = recurso_da_competencia(competencia)
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / nome_do_arquivo(recurso["url"])

    baixado = False
    try:
        conferir_arquivo(caminho, recurso["etag"], recurso["tamanho"])
    except (FileNotFoundError, ArquivoDivergente):
        baixar(recurso["url"], caminho)
        baixado = True
        conferir_arquivo(caminho, recurso["etag"], recurso["tamanho"])

    atualizar_manifesto(pasta, competencia, {
        "arquivo": caminho.name,
        "url": recurso["url"],
        "etag": recurso["etag"],
        "tamanho": recurso["tamanho"],
    })
    return {**recurso, "arquivo": caminho.name, "caminho": caminho, "baixado": baixado}
