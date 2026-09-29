# Camada Gold

Tabelas agregadas (uma linha por acidente, ou por pessoa), geradas pela
seção "Camada de Engenharia de Dados" do notebook. São pequenas o
suficiente para versionar no Git — commit `ocorrencias_gold.parquet` e
`pessoas_silver.parquet` (camada gold/silver leve) aqui depois de rodar o
notebook com as 3 bases reais.

As camadas bronze e silver completas (data/bronze/, data/silver/) e o
banco DuckDB (*.duckdb) NÃO são versionadas (ver .gitignore) — são grandes
e 100% reproduzíveis rodando o notebook do início.
