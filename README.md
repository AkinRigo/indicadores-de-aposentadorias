<div align="center">

# 📊 Indicadores de Aposentadorias

**Aposentadoria por idade (INSS, espécie 041) com dados confiáveis do portal até a tela.**

![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-150458?logo=pandas&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-4169E1?logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?logo=sqlalchemy&logoColor=white)
![Alembic](https://img.shields.io/badge/Alembic-migrations-6BA81E)
![pytest](https://img.shields.io/badge/pytest-92_testes-0A9EDC?logo=pytest&logoColor=white)
![Power BI](https://img.shields.io/badge/Power_BI-F2C811?logo=powerbi&logoColor=black)
![License](https://img.shields.io/badge/Licença-MIT-green)

</div>

---

## 📑 Sumário

- [Sobre o projeto](#-sobre-o-projeto)
- [Principais funcionalidades](#-principais-funcionalidades)
- [Regras de negócio](#-regras-de-negócio)
- [Tecnologias utilizadas](#-tecnologias-utilizadas)
- [Estrutura do projeto](#-estrutura-do-projeto)
- [Pré-requisitos](#-pré-requisitos)
- [Configuração e instalação](#-configuração-e-instalação)
- [Documentação da API](#-documentação-da-api)
- [Painel (Power BI)](#-painel-power-bi)
- [Frontend](#-frontend)
- [Endpoints consumidos](#-endpoints-consumidos)
- [Banco de dados e migrations](#-banco-de-dados-e-migrations)
- [Testes](#-testes)
- [Licença](#-licença)
- [Autor](#-autor)

---

## 📖 Sobre o projeto

Painel de indicadores de **aposentadoria por idade (espécie 041)** com dados oficiais do INSS.

Grande parte de quem se aposenta por idade tem até o ensino fundamental completo: **52,4%** em out/2026. Este projeto mostra o perfil dessas concessões para apoiar quem atende e orienta esse público, com **dados confiáveis do portal até a tela**.

Comecei por uma única espécie para validar a arquitetura completa antes de expandir:

- **Fonte oficial:** Dados Abertos do INSS, com conferência de ETag e MD5 do arquivo.
- **ETL idempotente:** rodar a carga duas vezes não duplica dados.
- **Testes** em 3 critérios: conformidade, integridade referencial e detecção de anomalias.
- **Estrutura do banco versionada** com migrações (Alembic).
- **Minimização de dados (LGPD):** só o ano de nascimento é armazenado.

---

## ✨ Principais funcionalidades

- Ver **quantas aposentadorias por idade** o INSS concedeu no mês.
- Conhecer o **perfil de escolaridade** de quem se aposenta: quanto chega até o ensino fundamental e qual é o maior grupo.
- Saber **quanto da informação veio incompleta** do próprio INSS (escolaridade não informada).
- Comparar as escolaridades em um **gráfico**, ordenando por nível ou por quantidade, com o percentual de cada uma.
- **Escolher a competência** (mês) que deseja analisar.
- **Baixar o painel do Power BI** para criar suas próprias análises com os mesmos dados.
- Acessar pelo **computador ou celular**.
- **Confiar nos números:** cada valor vem do arquivo oficial do INSS, conferido e sem duplicidade, e as linhas descartadas ficam registradas com o motivo.

---

## 📋 Regras de negócio

### Escopo

- Apenas a espécie **041 (aposentadoria por idade)**.
- Uma carga por **competência** (mês). Todas as linhas do arquivo precisam ser da competência informada.

### Aceite das linhas

- **Campos obrigatórios:** linha sem DIB, DDB, agência, município ou outro campo essencial é rejeitada (`dado_ausente`). A DCB (cessação) pode ficar vazia.
- **Idade plausível:** idade na DIB de no mínimo **50 anos**. Não é a regra da lei, é uma margem abaixo da menor idade legal (55) para pegar erros óbvios, como nascimento depois do início do benefício (`idade_implausivel`).
- **Duplicadas:** linhas idênticas na planilha **original** ficam só uma vez (`duplicada`). A comparação é feita antes da transformação, porque depois dela pessoas diferentes nascidas no mesmo ano ficariam iguais.
- Toda linha rejeitada vai para `data/rejeitadas/<competencia>.csv` com o motivo.

### Regras no banco (CHECK constraints)

- Sexo: `FEMININO` ou `MASCULINO`. Clientela: `URBANA` ou `RURAL`.
- Cessação nunca antes do início (`dcb >= dib`).
- Valor em salários mínimos maior que zero, e anos de contribuição entre 0 e 90.
- No `controle_carga`: competência no formato `AAAAMM`, uma única carga por competência, e arquivo, ETag, tamanho e linhas sempre preenchidos.

### Atualização

- Se a ETag do portal for igual à do banco, nada é recarregado.
- Se for diferente, o sistema **avisa** que o banco não está de acordo com o portal do INSS e recarrega a competência.
- A carga é **transacional**: se algo falhar no meio, nada fica gravado pela metade.

### Privacidade (LGPD)

- Só o **ano** de nascimento é armazenado (minimização de dados).

### Qualidade da fonte

- Dados ruins que **vêm do próprio INSS**, como escolaridade `INVÁLIDO` (16,4%), são **mantidos e expostos** no painel, não apagados.

---

## 🛠️ Tecnologias utilizadas

| Tecnologia | Uso |
|---|---|
| **Python** | Linguagem principal do ETL |
| **requests** | Consulta à API CKAN e download do arquivo |
| **pandas** + **python-calamine** | Leitura e transformação da planilha XLSX |
| **PostgreSQL** | Banco de dados (modelo estrela) |
| **SQLAlchemy** + **psycopg** | Conexão com o banco e carga em massa (`COPY`) |
| **Alembic** | Migrations |
| **python-dotenv** | Leitura da conexão no `.env` |
| **pytest** | Testes automatizados |
| **Power BI Desktop** | Painel de indicadores |

---

## 🗂️ Estrutura do projeto

```text
indicadores-aposentadorias/
├── api/
│   └── ckan.py
├── data/                      (fora do git)
│   ├── raw/
│   └── rejeitadas/
├── docs/
│   └── fontes/
│       └── aposentadoria-por-idade.md
├── frontend/
│   ├── index.html
│   ├── dados.js
│   └── exportar.py
├── etl/
│   ├── __main__.py
│   ├── extrair.py
│   ├── transformar.py
│   └── carregar.py
├── migrations/
│   ├── env.py
│   └── versions/
│       ├── 001_cria_controle_carga.py
│       ├── 002_cria_dimensoes.py
│       ├── 003_cria_fato_concessao.py
│       └── 004_regras_controle_carga.py
├── powerbi/
│   ├── kpis-pb.pbix
│   └── tema.json
├── sql/
│   └── 02_integridade.sql
├── tests/
│   ├── conftest.py
│   ├── test_ckan.py
│   ├── test_controle_carga.py
│   ├── test_integridade.py
│   └── test_transformar.py
├── .env
├── .env.example
├── .gitignore
├── alembic.ini
├── pyproject.toml
└── README.md
```

### Pastas

| Pasta | Conteúdo |
|---|---|
| `api/` | Cliente da API CKAN do portal de Dados Abertos do INSS |
| `etl/` | Etapas do ETL: extrair, transformar e carregar |
| `data/raw/` | Planilha original baixada do portal e manifesto da extração |
| `data/rejeitadas/` | Linhas recusadas pelo ETL, com o motivo, por competência |
| `docs/fontes/` | Documentação da fonte: links, recorte, protocolo e idempotência |
| `migrations/` | Migrations que criam e versionam a estrutura do banco |
| `sql/` | Consultas de integridade (dimensões sem uso na fato) |
| `powerbi/` | Painel e tema visual do Power BI |
| `frontend/` | Página web com os indicadores (desenvolvida por IA sob supervisão) e o script que exporta os dados do banco |
| `tests/` | Testes automatizados. O `conftest.py` prepara o banco de teste; os `test_*.py` testam a API, a transformação, o controle de carga e a integridade |

### Arquivos principais

| Arquivo | Função |
|---|---|
| `etl/__main__.py` | Executa o ETL completo de uma competência: `python -m etl AAAAMM` |
| `api/ckan.py` | Descobre o arquivo da competência, com ETag e tamanho |
| `etl/extrair.py` | Baixa o arquivo e confere tamanho e MD5 |
| `etl/transformar.py` | Filtra a espécie 041, padroniza, calcula a idade e separa as rejeitadas |
| `etl/carregar.py` | Grava dimensões, fato e controle de carga, de forma idempotente |
| `alembic.ini` | Configura o Alembic |
| `.env` | Guarda a URL do banco; **não deve ser compartilhado** |
| `.env.example` | Modelo do `.env`, sem senha real |
| `.gitignore` | Lista arquivos que o Git deve ignorar |
| `pyproject.toml` | Define dependências e configurações do projeto |
| `powerbi/tema.json` | Tema visual do painel (cores, fontes e rótulos) |
| `README.md` | Documentação do projeto |

---

## ✅ Pré-requisitos

### 💻 Para executar o ETL

- Git
- Python 3.13 ou superior
- PostgreSQL 18 ou superior
- Acesso à internet para baixar a planilha do INSS (cerca de 107 MB)

### 📊 Para abrir o painel

- Power BI Desktop (Windows)

---

## ⚙️ Configuração e instalação

### 1. Variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto, a partir do `.env.example`. Ele contém a conexão com o PostgreSQL e **não deve ser compartilhado nem enviado ao Git**.

```env
DATABASE_URL=postgresql://seu_usuario:sua_senha@localhost:5432/kpis
```

> ⚠️ Crie o banco `kpis` no PostgreSQL antes de continuar.

### 2. Instalação local

Na pasta do projeto, crie e ative o ambiente virtual e instale as dependências:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### 3. Criar as tabelas

```bash
alembic upgrade head
```

### 4. Carregar uma competência

```bash
python -m etl 202610
```

Rodar o mesmo comando de novo não duplica nada: se o arquivo do portal não mudou, o ETL responde que a competência está em dia.

---

## 📚 Documentação da API

Nesse projeto eu utilizei a **API CKAN** do portal de Dados Abertos do INSS. Ela lista os arquivos mensais do conjunto *Benefícios concedidos*; como o nome do arquivo muda a cada mês, a URL é descoberta pela API.

👉 **https://dadosabertos.inss.gov.br/api/3/action/package_show?id=beneficios-concedidos-plano-de-dados-abertos-jun-2023-a-dez-2027**

A documentação completa da fonte, com glossário dos campos, está em [docs/fontes/aposentadoria-por-idade.md](docs/fontes/aposentadoria-por-idade.md).

---

## 🎨 Painel (Power BI)

O painel lê o banco `kpis` no modo **Importar**: os dados mudam uma vez por mês, então basta rodar o ETL e clicar em **Atualizar** no Power BI.

### 📐 Modelo

Modelo estrela com a `fato_concessao` no centro, ligada às 6 dimensões (agência, município, despacho, forma de filiação, escolaridade e ramo de atividade) e ao `controle_carga`, todas em relação **muitos para um**.

### 📊 Indicadores

| Indicador | Out/2026 |
|---|---|
| Total concedido | 99.704 |
| Até fundamental completo | 52,4% |
| Maior grupo | 6º ao 9º ano incompleto |
| Escolaridade não informada | 16,4% |

Além dos cartões, um gráfico mostra as concessões por escolaridade, com o % do total ao passar o mouse e a categoria `INVÁLIDO` em cinza.

### ⚙️ Abrir localmente

1. Abra `powerbi/kpis-pb.pbix` no Power BI Desktop.
2. Se pedir, informe o servidor `localhost:5432`, o banco `kpis` e as credenciais do PostgreSQL.
3. Clique em **Atualizar**.

O tema visual está em `powerbi/tema.json` (**Exibição → Temas → Procurar temas**).

---

## 🖥️ Frontend

O frontend foi desenvolvido por IA **sob minha supervisão**, a partir de um prompt curto e de um **protótipo de referência** que aprovei antes da implementação. Ele apresenta os mesmos indicadores do painel do Power BI em uma página web responsiva.

### 🛠️ Tecnologias

- **HTML, CSS e JavaScript puros**, sem framework
- **Apache ECharts** para o gráfico de concessões por escolaridade
- **Python** (`frontend/exportar.py`) para gerar os dados da página a partir do banco

### ✨ O que a página mostra

- Os 4 indicadores: total concedido, % até fundamental completo, maior grupo e % sem escolaridade informada.
- Gráfico de barras por escolaridade, ordenável por nível ou por quantidade, com o % do total.
- Seletor de competência. Os meses anteriores a out/2026 aparecem como **em construção**, porque o INSS alterou o layout dos dados abertos a partir dessa competência.
- Botão para **baixar o `.pbix`** e editar o painel no Power BI Desktop.

### ⚙️ Executar localmente

Depois de carregar uma competência com o ETL, gere os dados da página:

```bash
python -m frontend.exportar
```

Na raiz do projeto, inicie um servidor local:

```bash
python -m http.server 8000
```

Acesse **http://localhost:8000/frontend/**. A página precisa ser servida a partir da raiz para que o botão de download encontre `powerbi/kpis-pb.pbix`.

---

## 🔌 Endpoints consumidos

| Método | Endereço | Descrição |
|---|---|---|
| `GET` | `dadosabertos.inss.gov.br/api/3/action/package_show` | Lista os arquivos do conjunto e a competência de cada um |
| `HEAD` | Arquivo no S3 (`armazenamento-dadosabertos.s3.sa-east-1.amazonaws.com`) | Lê a ETag e o tamanho sem baixar o arquivo |
| `GET` | Arquivo no S3 | Baixa a planilha da competência |

---

## 🗄️ Banco de dados e migrations

O projeto utiliza **PostgreSQL** com um **modelo estrela**. Configure no arquivo `.env` a URL de conexão com o banco, sem compartilhá-lo.

| Migration | O que cria |
|---|---|
| `001` | `controle_carga`: uma linha por competência carregada, com arquivo, ETag, tamanho e quantidade de linhas |
| `002` | As 6 dimensões |
| `003` | `fato_concessao`, com as chaves estrangeiras e as regras de validação |
| `004` | Regras de validação do `controle_carga` |

Para aplicar as migrations:

```bash
alembic upgrade head
```

Para desfazer a última:

```bash
alembic downgrade -1
```

As consultas em `sql/02_integridade.sql` procuram dimensões sem uso na fato e também rodam como teste.

---

## 🧪 Testes

O projeto usa **pytest**. Os testes rodam no banco configurado no `.env`; os que gravam dados são desfeitos ao final (rollback). Em ambiente virtual, rode:

```bash
pytest -v   # saída detalhada
pytest -q   # resumo mais curto
```

### API CKAN (`test_ckan.py`, 13 testes)

| Cenário | Resultado esperado |
|---|---|
| Nome do recurso com mês e ano | Competência `AAAAMM` correta, inclusive "março" e "marco" |
| Competência existente | URL, ETag e tamanho do arquivo |
| Competência inexistente | `RecursoNaoEncontrado` |
| Portal fora do ar ou resposta sem sucesso | Erro, sem continuar a carga |

### Transformação (`test_transformar.py`, 15 testes)

| Cenário | Resultado esperado |
|---|---|
| Planilha com título e linha vazia | Lê só os dados |
| Espécies diferentes de 041 | Filtradas |
| Idade na véspera e no dia do aniversário | 64 e 65 anos |
| Idade abaixo de 50 ou nascimento depois da DIB | `idade_implausivel` |
| Três linhas idênticas | Fica a primeira; duas `duplicada` |
| Linhas que diferem só no dia de nascimento | **Não** são duplicadas |
| Linha sem DIB | `dado_ausente`; sem DCB é aceita |

### Controle de carga (`test_controle_carga.py`, 16 testes)

| Cenário | Resultado esperado |
|---|---|
| Primeira carga | Registrada |
| Mesma competência duas vezes | Recusada pelo banco |
| Competência, arquivo, ETag, tamanho ou linhas inválidos | Recusados pelo banco |
| Mesma ETag do portal | `em_dia` |
| ETag diferente | `desatualizada`, com aviso de que não está de acordo com o portal do INSS |
| Arquivo local com tamanho ou MD5 diferente | `ArquivoDivergente` |

### Integridade (`test_integridade.py`, 48 testes)

| Critério | O que é verificado |
|---|---|
| **Precisão e conformidade** | Nenhum campo obrigatório vazio; formato dos códigos; idade, nascimento, valor e datas dentro dos intervalos |
| **Integridade referencial** | Banco na última migration; as 7 chaves estrangeiras existem; consultas de `sql/02_integridade.sql` vazias; competência da fato igual à da carga |
| **Detecção de anomalias** | Linhas gravadas iguais às do controle; arquivo local com MD5 igual à ETag; banco idêntico ao que o ETL gera do arquivo oficial |

---

## 📄 Licença

Distribuído sob a **Licença MIT**. Confira o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 👨‍💻 Autor

Construído e desenvolvido por **Akin Rigo**.
