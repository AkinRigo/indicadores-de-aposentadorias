import json
from pathlib import Path

from sqlalchemy import text

from etl.carregar import criar_engine

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "frontend" / "dados.js"
PASTA_REJEITADAS = RAIZ / "data" / "rejeitadas"

CONSULTA_CARGAS = """
SELECT competencia, arquivo, linhas_carregadas, carregado_em
FROM controle_carga
ORDER BY competencia DESC
"""

CONSULTA_ESCOLARIDADE = """
SELECT c.competencia, g.codigo, g.descricao, count(*) AS quantidade
FROM fato_concessao f
JOIN controle_carga c ON c.id_carga = f.id_carga
JOIN dim_grau_instrucao g ON g.id = f.id_grau_instrucao
GROUP BY c.competencia, g.codigo, g.descricao
ORDER BY c.competencia, g.codigo
"""


def contar_rejeitadas(competencia):
    arquivo = PASTA_REJEITADAS / f"{competencia}.csv"
    if not arquivo.exists():
        return None
    with arquivo.open(encoding="utf-8") as f:
        return sum(1 for _ in f) - 1


def exportar():
    with criar_engine().connect() as conn:
        cargas = conn.execute(text(CONSULTA_CARGAS)).mappings().all()
        linhas = conn.execute(text(CONSULTA_ESCOLARIDADE)).mappings().all()

    competencias = []
    for carga in cargas:
        escolaridade = [
            {"codigo": l["codigo"], "descricao": l["descricao"], "quantidade": l["quantidade"]}
            for l in linhas
            if l["competencia"] == carga["competencia"]
        ]
        total = sum(e["quantidade"] for e in escolaridade)
        if total != carga["linhas_carregadas"]:
            raise ValueError(
                f"{carga['competencia']}: {total} linhas na fato, {carga['linhas_carregadas']} no controle"
            )
        competencias.append({
            "competencia": carga["competencia"],
            "arquivo": carga["arquivo"],
            "carregado_em": carga["carregado_em"].isoformat(timespec="minutes"),
            "total": total,
            "rejeitadas": contar_rejeitadas(carga["competencia"]),
            "escolaridade": escolaridade,
        })

    DESTINO.write_text(
        "window.DADOS = " + json.dumps({"competencias": competencias}, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )
    print(f"{len(competencias)} competência(s) exportada(s) para {DESTINO}")


if __name__ == "__main__":
    exportar()
