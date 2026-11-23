# Fonte: Aposentadoria por idade (espécie 041)

## O que é ingerido

Benefícios concedidos pelo INSS, filtrados apenas pela **espécie 041 — Aposentadoria por idade**.

| Item | Valor |
|---|---|
| Portal | Dados Abertos do INSS |
| Conjunto | Benefícios concedidos — Plano de Dados Abertos Jun/2023 a dez/2027 |
| Responsável | CGMAIND/DIRBEN |
| Periodicidade | Mensal |
| Formato | XLSX (de 2026 em diante não há versão CSV) |
| Competência atual | 202610 (outubro de 2026), publicada em 18/11/2026 |
| Recorte | `Espécie (Código) = 041` → 99.850 de 749.312 linhas |

## Links

- **API CKAN (lista oficial dos arquivos mensais):**
  https://dadosabertos.inss.gov.br/api/3/action/package_show?id=beneficios-concedidos-plano-de-dados-abertos-jun-2023-a-dez-2027
- **Arquivo de outubro/2026:**
  https://armazenamento-dadosabertos.s3.sa-east-1.amazonaws.com/PDA_2025_2027/Grupos_de_dados/Benef%C3%ADcios+concedidos/CONCEDIDOS_DADOS+ABERTOS_OUTUBRO+2026.xlsx
- **Glossário dos campos:**
  https://armazenamento-dadosabertos.s3.sa-east-1.amazonaws.com/PDA_2023_2025/PDA+e+Inventario/Glossarios/Gloss%C3%A1rio+de+dados+dos+benef%C3%ADcios+concedidos.xlsx

## Cópia local

| Item | Valor |
|---|---|
| Caminho | `data/raw/CONCEDIDOS_DADOS+ABERTOS_OUTUBRO+2026.xlsx` (fora do git) |
| Tamanho | 106.989.664 bytes |
| MD5 / ETag S3 | `bc8079e4e736e3a09e605b9732d28d8e` |

## Protocolo

Download HTTPS do S3, sem autenticação. O nome do arquivo muda a cada mês, então a URL é descoberta pela API CKAN.

## Idempotência

Por competência (`competencia=202610`). O manifesto guarda ETag e tamanho; se não mudaram, o arquivo não é baixado de novo.
