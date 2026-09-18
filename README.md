# Desafio Agibank — QA Automação de Serviços (API)

Framework de automação focado **exclusivamente em testes de serviços/API REST**
(nenhum teste de interface web, nenhum cálculo de simulações ou calculadoras).

Suíte executável localmente e via **GitHub Actions** com relatório consolidado
em HTML contendo transações HTTP detalhadas por teste.

---

## Stack

- **Python 3.11+**
- **pytest** — executor + marcação (markers)
- **requests** — cliente HTTP padrão
- **pytest-html** — relatório consolidado (self-contained, opcional)
- **utils/api_logger** — interceptor HTTP com validação automática + schemas + validadores customizados

---

## Estrutura

```
.
├── .github/workflows/api-tests.yml   # Pipeline CI/CD (push/PR → apenas testes de API)
├── tests/
│   ├── conftest.py                   # fixtures, marcadores, hooks pytest-html
│   └── api/test_dog_api.py           # 22 testes servicos Dog CEO API
├── utils/api_logger.py               # ApiLogger + schemas + validadores + regex URL
├── reports/                          # relatório HTML + logs de API (não versionados)
├── requirements.txt
├── pytest.ini
└── .gitignore
```

---

## Setup local

```bash
# 1. Ambiente virtual (opcional mas recomendado)
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# 2. Dependências
pip install -r requirements.txt
```

---

## Como rodar os testes de SERVIÇOS (API Dog CEO)

```bash
# Toda a suíte de API (todos os 22 testes)
pytest -m api -vv
# ou:  pytest tests/api -vv

# Apenas testes de contrato / schema
pytest -m contrato -v

# Apenas testes de erro / cenários negativos
pytest -m erro -v

# Apenas happy path / fluxo principal
pytest -m happy_path -v

# Gera o relatório HTML consolidado (OPCIONAL)
pytest -m api -vv --html=reports/report.html --self-contained-html
```

O relatório HTML — quando gerado com `--html=...` — traz, para cada teste de API:

- blocos `<details>` expandíveis com **transação HTTP completa**
  (headers request/response + bodies + status + tempo gasto)
- badges em vermelho com **contagem de FALHA(S)** de validação

---

### Logs estruturados da camada de serviços

Toda requisição HTTP do `ApiLogger` é salva em `reports/api_logs/`
(pasta **não versionada**, vide `.gitignore`):

| Arquivo | Finalidade |
|---|---|
| `api_transactions_*.log` | Texto colunar, humano-legível, 1 transação por bloco |
| `api_transactions_*.json` | Estruturado, ideal para integração / parsing |
| `*_tx.html` | Detalhe por teste (mesmo HTML anexado ao report global) |

---

## Marcadores (`@pytest.mark`)

Apenas marcadores de SERVIÇOS estão ativos no README:

| Marcador | Finalidade |
|---|---|
| `api` | Todos os testes de API / serviços |
| `dog_api` | Suíte Dog CEO (https://dog.ceo/dog-api) |
| `contrato` | Testes de schema / estrutura JSON |
| `funcional` | Testes focados em comportamento de negócio |
| `erro` | Cenários negativos / fluxo de erro |
| `happy_path` | Fluxo principal / sem erros |
| `validacao` | Foco em validação de input/contrato |

---

## CI/CD — GitHub Actions

O workflow `.github/workflows/e2e-api-tests.yml` roda automaticamente em
**push** e **pull_request** para `main`, `master`, `develop`. Fluxo:

1. Checkout do código
2. Setup Python 3.11
3. Instala dependências (apenas de serviços)
4. Executa `pytest -vv --html=reports/report.html --self-contained-html`
5. Faz **upload de `reports/` como artefato** por 7 dias (`if: always()`),
   independentemente de sucesso ou falha

---

## Cobertura de SERVIÇOS — Dog API (Dog CEO)

### Endpoints de raças (`/breed/{breed}/...`)

| # | Endpoint | Status | Cenários |
|---|---|---|---|
| 1 | `GET /breeds/list/all` | ✅ | HTTP 200, `status=success`, lista **não-vazia**, contrato `dict[str, list[str]]` |
| 2 | `GET /breed/{hound}/images` | ✅ | 200 + lista URLs válidas (regex imagem) + `>= 10 itens` |
| 3 | `GET /breeds/image/random` | ✅ | 200 + **1 URL única** no formato padrão |
| 4 | `GET /breed/{raca_invalida}/images` | ✅ | **Cenário de erro**: 404 **ou** 200 + `status=error` |
| 5 | `GET /breed/{hound}/images/random` | ✅ | 200 + 1 URL aleatória **pertencente** à raça (`/breeds/{breed}/` no path) |
| 6 | `GET /breed/{hound}/images/random/3` | ✅ | 200 + **exatamente 3 URLs**, todas pertencentes à raça |

### Endpoints de **sub-raças** (`/breed/{breed}/{sub}/...`)

| # | Endpoint | Status | Cenários |
|---|---|---|---|
| 7 | `GET /breed/hound/list` | ✅ | 200 + array com **7 sub-raças exatas**: {`afghan`, `basset`, `blood`, `english`, `ibizan`, `plott`, `walker`} |
| 8 | `GET /breed/hound/afghan/images` | ✅ | 200 + lista URLs válidas + **todas contêm `/breeds/hound-afghan/`** (pertencimento) + `>= 5` itens |
| 9 | `GET /breed/hound/afghan/images/random` | ✅ | 200 + **1 URL aleatória da sub-raça** (path confere) |
| 10 | `GET /breed/hound/afghan/images/random/3` | ✅ | 200 + **3 URLs exatas**, todas pertencentes à sub-raça `hound-afghan` |
| 11 | `GET /breed/hound/{sub_invalida}/images` | ✅ | **Cenário de erro**: 404 **ou** 200 + `status=error` |

**Total: 22 testes aprovados (11 endpoints + 11 testes de contrato/negócio).**

---

### Validações automáticas por transação de serviço (ApiLogger)

São aplicadas **em toda requisição** (válido para qualquer serviço REST integrado):

1. **Status code** exato por cenário
2. **Headers obrigatórios** em request/response (via listas)
3. **Content-Type** esperado (ex: `application/json`)
4. **Payload request**: campos obrigatórios + tipagem primitiva + não-vazios
5. **Payload response**: campos obrigatórios + tipagem + não-vazios
6. **Headers de segurança** (opcional, `check_sec=True`)
7. **Schema completo** via callable user (`schema=...`)
8. **Validadores cross-campo** customizados (`validators=[fn1, fn2]`)
9. **Consistência HTTP** (ex: 201 só com POST/PUT; 204 sem body; 4xx/5xx com campos padrão)

---

## Enviando para o GitHub

Repositório destino: `https://github.com/bioadsl/desafioagibankservicos.git`.

```bash
git init
git remote add origin https://github.com/bioadsl/desafioagibankservicos.git

git add .gitignore requirements.txt pytest.ini README.md
git commit -m "chore: config base do projeto e documentacao"

git add utils/ tests/api/ tests/conftest.py
git commit -m "feat(api): cliente dog api, interceptor HTTP, schemas e 22 testes de servico"

git add .github/workflows/
git commit -m "ci: pipeline github actions (apenas testes de servico/API) com artefato de relatorio"

git branch -M main
git push -u origin main
```

> Commits atômicos e semânticos ajudam a demonstrar a evolução natural da
> cobertura de serviços (novos endpoints adicionados em blocos separados).
