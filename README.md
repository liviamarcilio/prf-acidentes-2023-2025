# Análise de Acidentes em Rodovias Federais (PRF) — 2023-2025

Análise exploratória, engenharia de dados e visualização sobre os acidentes
registrados pela Polícia Rodoviária Federal (PRF) nas rodovias federais
brasileiras, entre 2023 e 2025.

## Contexto

Os dados vêm do Boletim de Acidente de Trânsito (BAT), sistema usado pela
PRF para registrar cada ocorrência atendida em rodovia federal, e são
publicados pela PRF em conformidade com a Lei de Acesso à Informação (Lei
nº 12.527/2011) e o Decreto nº 8.777/2016 (Política de Dados Abertos do
Executivo Federal).

Este projeto usa a extração "agrupada por pessoa, com todas as causas e
tipos de acidentes" — a granularidade mais fina disponibilizada pela PRF:
uma linha por combinação de pessoa envolvida, causa e tipo de acidente
dentro de uma mesma ocorrência. Essa escolha de granularidade é tratada
explicitamente ao longo do pipeline (ver `notebooks/`), porque contar
acidentes, pessoas e causas nesse formato exige agregações diferentes das
de um dataset "1 linha = 1 acidente".

## Perguntas respondidas

1. Quais são as principais causas registradas dos acidentes entre 2023 e 2025?
2. Houve aumento ou redução na quantidade e na gravidade dos acidentes ao longo dos três anos?
3. Quais dias da semana e horários concentram mais acidentes e acidentes graves?
4. Quais condições meteorológicas estão presentes nos acidentes de maior gravidade?
5. Quais fatores comportamentais do condutor aparecem com mais frequência (álcool, sono, celular, velocidade, ultrapassagem)?
6. Quais condições da via aparecem com maior frequência nos acidentes?
7. Quais BRs, estados, municípios ou trechos concentram mais acidentes graves e fatais?
8. A idade dos condutores está associada às causas ou à gravidade dos acidentes?
9. Quais tipos de veículos estão mais envolvidos nos acidentes registrados?
10. Feriados apresentam padrões diferentes dos demais dias?

## Arquitetura do pipeline

```
Extract                Transform                  Load
--------                ---------                  ----
Google Drive     -->    Bronze (bruto)       -->   data/bronze/*.parquet
(gdown, IDs da           |
página oficial           v
da PRF; fallback     Quarentena (auditoria)  -->   data/quarantine/*.csv
p/ cópia local)          |
                          v
                     Silver (limpo/tipado)    -->   data/silver/*.parquet
                          |
                          v
                     Gold (agregado por       -->   data/gold/*.parquet
                     acidente, pronto p/           + DuckDB (data/*.duckdb)
                     dashboard e relatório)
```

- **Extract**: coleta automatizada por requisição direta ao Google Drive
  (via `gdown`), a partir dos links publicados na página oficial de dados
  abertos da PRF — que não expõe uma API REST própria para essas bases, e
  cujo próprio portal (`portal.prf.gov.br`) bloqueia acesso automatizado via
  robots.txt. Se a coleta automática falhar por qualquer motivo (o ID do
  arquivo mudou, sem internet), o pipeline cai para uma cópia local (ex.:
  Google Drive pessoal) sem interromper o restante do processamento — o
  motivo da falha é sempre registrado, nunca escondido. Código em
  [`src/data_loader.py`](src/data_loader.py).
- **Transform com quarentena**: em vez de descartar silenciosamente um
  registro problemático, ele é marcado com o motivo e mantido à parte para
  auditoria (`data/quarantine/`), sem sumir do dataset principal sem
  explicação. Código em [`src/quarantine.py`](src/quarantine.py).
- **Load**: as três camadas (bronze/silver/gold) são persistidas em
  Parquet, e as tabelas gold também carregadas em um banco DuckDB local —
  relacional de verdade, consultável por SQL puro, sem servidor externo.
  Código em [`src/db.py`](src/db.py).
- **Reconciliação**: uma célula final confere que nenhuma linha sumiu sem
  explicação entre as camadas.

## Estrutura do repositório

```
.
├── notebooks/
│   └── EDA_PRF_2023_2024_2025.ipynb   # pipeline completo: EDA + engenharia de dados
├── src/
│   ├── data_loader.py                  # Extract (coleta automática + fallback)
│   ├── quarantine.py                   # Transform com quarentena + reconciliação
│   └── db.py                           # Load (Parquet + DuckDB)
├── data/
│   ├── gold/                           # tabelas agregadas, versionadas (pequenas)
│   ├── bronze/ silver/ quarantine/     # geradas ao rodar o notebook (não versionadas)
│   └── *.duckdb                        # gerado ao rodar o notebook (não versionado)
├── reports/                            # relatório executivo (gerado via nbconvert)
├── dashboards/                         # link/print do dashboard (Looker Studio)
├── requirements.txt
└── README.md
```

## Como rodar

**Google Colab (recomendado):**
1. Abra `notebooks/EDA_PRF_2023_2024_2025.ipynb` no Colab.
2. Rode as células em ordem, de cima para baixo. A célula de coleta baixa
   os 3 arquivos automaticamente do Google Drive; se falhar (ex.: o ID do
   arquivo mudou), ela cai para uma pasta do seu Google Drive pessoal com
   os 3 CSVs já baixados manualmente.

**Local:**
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
jupyter notebook notebooks/EDA_PRF_2023_2024_2025.ipynb
```

## Dashboard

🔗 *[link do Looker Studio — a adicionar]*

## Relatório executivo

📄 *[a adicionar em `reports/` — gerado automaticamente a partir do notebook via `jupyter nbconvert --no-input`]*

## Fonte dos dados

Polícia Rodoviária Federal — Dados Abertos:
https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf

Dicionário oficial de variáveis (acidentes agrupados por pessoa, com todas
as causas e tipos): reproduzido e explicado na seção 1 do notebook.

## Stack

Python · pandas · DuckDB · Parquet · Matplotlib/Seaborn · GeoPandas/`geobr` ·
Google Colab · Looker Studio

---

Projeto acadêmico — Lívia Marcilio Lopes.
