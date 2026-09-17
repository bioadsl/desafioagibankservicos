# Desafio Agibank — QA Automação (Web + API)

Framework unificado de automação de testes cobrindo **UI (Playwright + POM)** e **API (requests)**.
Suíte executável localmente e via **GitHub Actions** com relatório consolidado em HTML.

## Stack

- **Python 3.11+**
- **pytest** — execução e marcação de testes
- **Playwright** — E2E Web com **POM (Page Object Model)**
- **requests** — cliente HTTP para API
- **pytest-html** — relatório consolidado

## Estrutura

```
.
├── .github/workflows/e2e-api-tests.yml   # Pipeline CI/CD (push/PR)
├── pages/                                 # Page Objects (Playwright)
│   ├── base_page.py                      # helpers + waits explícitos
│   ├── calculadora_dias_uteis_page.py
│   ├── calculadora_juros_page.py
│   └── blog_agi_search_page.py
├── tests/
│   ├── conftest.py                       # fixtures + pytest-html hooks
│   ├── web/                              # Testes E2E (Agibank + Blog do Agi)
│   └── api/test_dog_api.py               # Testes Dog API (funcionais + contrato)
├── utils/api_logger.py                   # Interceptor HTTP + validadores + logs
├── reports/                              # relatório HTML e logs de API
├── requirements.txt
├── pytest.ini
└── .gitignore
```

## Setup local

```bash
# 1. Ambiente virtual (opcional mas recomendado)
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# 2. Dependências
pip install -r requirements.txt

# 3. Browser do Playwright
playwright install chromium
```

## Como rodar os testes

```bash
# Suíte completa (Web + API)
pytest

# Apenas Web
pytest tests/web -v

# Apenas API
pytest tests/api -v

# Por marcador (ex: só testes de contrato de API)
pytest -m contrato -v
```

O **relatório consolidado** é gerado automaticamente em `reports/report.html`
(configuração padrão em `pytest.ini`) e já inclui, para cada teste de API:

- os blocos `<details>` expandíveis com **toda a transação HTTP**
  (headers/body request + response + tempo gasto)
- badges de **FALHA(S)** em vermelho para cada critério não atendido

### Logs legíveis da camada API

Toda requisição é persistida em 3 formatos dentro de `reports/api_logs/`:

| Arquivo | Uso |
|---|---|
| `api_transactions_*.log` | Texto colunar humano-legível, 1 transação por bloco |
| `api_transactions_*.json` | Estruturado, ideal para parsing |
| `*_tx.html` | Detalhe por teste (mesmo HTML anexado ao report) |

## Marcadores (`@pytest.mark`)

| Marcador | Finalidade |
|---|---|
| `web` | Todos os testes E2E Web |
| `api` | Todos os testes de API |
| `contrato` | Testes focados em schema/estrutura JSON |
| `funcional` | Testes focados em comportamento de negócio |
| `erro` | Cenários negativos / fluxo de erro |
| `happy_path` | Fluxo principal / sem erros |
| `blog_agi`, `calculadora_dias_uteis`, `calculadora_juros`, `dog_api` | Por módulo/sistema |

## CI/CD — GitHub Actions

O workflow `.github/workflows/e2e-api-tests.yml` roda automaticamente em
**push** e **pull_request** para `main`, `master`, `develop`:

1. Checkout do código
2. Setup Python 3.11
3. Instala dependências e browsers do Playwright
4. Executa `pytest` (Web + API)
5. Faz **upload de `reports/` como artefato** por 7 dias
   (inclui `report.html` + `api_logs/`), independente de sucesso/falha (`if: always()`).

## Cobertura dos desafios

### 🧪 Camada Web (3 suítes)

| Page Object | Cenários |
|---|---|
| `CalculadoraDiasUteisPage` | ✅ Cálculo feliz; ✅ validação de campos obrigatórios vazios |
| `CalculadoraJurosPage` | ✅ Modo **Dívida** (cenário feliz); ✅ Modo **Investimento** (cenário feliz) |
| `BlogAgiSearchPage` | ✅ Busca por termo existente (`Empréstimo`); ✅ busca sem resultados |

### 🌐 Camada API — Dog API (https://dog.ceo/dog-api)

| Endpoint | Status |
|---|---|
| `GET /breeds/list/all` | ✅ HTTP 200, `status=success`, lista não-vazia, contrato completo (`dict[str, list[str]]`) |
| `GET /breed/{hound}/images` | ✅ HTTP 200, lista de URLs válidas (regex formato imagem), pelo menos 10 itens |
| `GET /breeds/image/random` | ✅ HTTP 200, **URL única** no formato esperado |
| `GET /breed/{invalida}/images` | ✅ Cenário de erro: `404` **ou** `200` com `status=error` |

### 🛡️ Validações automáticas por transação API (ApiLogger)

1. **Status code** esperado por cenário
2. **Headers obrigatórios** em request/response
3. **Content-Type** (ex: `application/json`)
4. **Payload request**: campos obrigatórios + tipos + não-vazios
5. **Payload response**: campos obrigatórios + tipos + não-vazios
6. **Headers de segurança** (opcional via `check_sec=True`)
7. **Schema completo** (`schema=...`, callable user)
8. **Validadores customizados** (`validators=[fn1, fn2]`)
9. **Consistência de fluxo HTTP** (ex: `201` só com POST/PUT, `204` sem body, `4xx/5xx` com campos padrão)

## Enviando para o GitHub

O repositório destino é `https://github.com/bioadsl/desafioagibankservicos.git`.
Sugestão de commits organizados (histórico avaliado pelos avaliadores):

```bash
git init
git remote add origin https://github.com/bioadsl/desafioagibankservicos.git

git add .gitignore requirements.txt pytest.ini README.md
git commit -m "chore: config base do projeto e documentação"

git add pages/ tests/web/
git commit -m "feat(web): page objects e testes e2e do agibank + blog do agi"

git add utils/ tests/api/ tests/conftest.py
git commit -m "feat(api): client dog api, interceptor, schemas e testes de contrato"

git add .github/workflows/
git commit -m "ci: pipeline github actions web+api com artefato de relatório"

git branch -M main
git push -u origin main
```

> Qualquer commit adicional (ajuste em seletores, novas categorizações, melhorias)
> ajuda a demonstrar a evolução natural da solução.
