import sys
from pathlib import Path

from etl.carregar import carregar_competencia, criar_engine
from etl.extrair import extrair
from etl.transformar import ler_planilha, transformar

PASTA_REJEITADAS = Path(__file__).resolve().parent.parent / "data" / "rejeitadas"


def main(competencia):
    print(f"[1/3] Extraindo {competencia} do portal do INSS...")
    extraido = extrair(competencia)
    print(f"      {extraido['arquivo']} ({'baixado' if extraido['baixado'] else 'já estava em data/raw'}, ETag conferida)")

    print("[2/3] Transformando...")
    transformado = transformar(ler_planilha(extraido["caminho"]))
    rejeitadas = transformado["rejeitadas"]
    print(f"      {transformado['linhas_origem']} linhas da espécie 041, "
          f"{len(transformado['fato'])} aceitas, {len(rejeitadas)} rejeitadas")
    if len(rejeitadas):
        PASTA_REJEITADAS.mkdir(parents=True, exist_ok=True)
        destino = PASTA_REJEITADAS / f"{competencia}.csv"
        rejeitadas.to_csv(destino, index=False, encoding="utf-8")
        for motivo, total in rejeitadas["motivo"].value_counts().items():
            print(f"      - {motivo}: {total}")
        print(f"      detalhes em {destino}")

    print("[3/3] Carregando no PostgreSQL...")
    engine = criar_engine()
    with engine.begin() as conn:
        resumo = carregar_competencia(conn, competencia, extraido, transformado)
    engine.dispose()

    if resumo["status"] == "em_dia":
        print("      Competência já carregada e em dia com o portal. Nada a fazer.")
    else:
        print(f"      Carga {resumo['id_carga']} ({resumo['status']}): {resumo['linhas']} linhas gravadas")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Uso: python -m etl AAAAMM   (ex.: python -m etl 202610)")
    main(sys.argv[1])
