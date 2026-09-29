"""
src/db.py — Camada de Carga (Load)

Persiste as camadas bronze/silver/gold em Parquet (formato colunar, o mesmo
princípio usado em data lakes como o que alimenta o AWS Athena/Glue) e
carrega as tabelas gold em um banco DuckDB local — um banco relacional real,
consultável por SQL puro, sem precisar de servidor, credencial ou serviço
externo. Isso substitui, de forma mais ágil, a carga em um banco gerenciado
(ex.: o padrão Oracle/FreeSQL usado em outras aulas do curso), que exige
credenciais e conectividade externas — inviável dentro do prazo deste projeto.
"""
from __future__ import annotations

import os

import duckdb
import pandas as pd


def salvar_parquet(df: pd.DataFrame, camada: str, nome: str, pasta_base="data") -> str:
    """
    Salva um DataFrame como Parquet dentro de data/<camada>/<nome>.parquet.

    :param df: DataFrame a salvar
    :param camada: 'bronze', 'silver' ou 'gold'
    :param nome: nome do arquivo, sem extensão
    :param pasta_base: pasta raiz onde vivem as camadas (padrão: 'data')
    :return: caminho do arquivo salvo
    """
    pasta = os.path.join(pasta_base, camada)
    os.makedirs(pasta, exist_ok=True)
    destino = os.path.join(pasta, f"{nome}.parquet")
    df.to_parquet(destino, index=False)
    return destino


def carregar_no_duckdb(tabelas: dict, caminho_banco="data/prf_acidentes.duckdb"):
    """
    Carrega um conjunto de DataFrames como tabelas em um arquivo DuckDB local.

    :param tabelas: dict {nome_da_tabela: DataFrame}
    :param caminho_banco: caminho do arquivo .duckdb a criar/atualizar
    :return: conexão duckdb aberta (para a célula seguinte já poder rodar SQL)
    """
    conexao = duckdb.connect(caminho_banco)
    for nome_tabela, df in tabelas.items():
        conexao.execute(f"CREATE OR REPLACE TABLE {nome_tabela} AS SELECT * FROM df")
        print(f"Tabela '{nome_tabela}' carregada no DuckDB ({len(df):,} linhas).".replace(",", "."))
    return conexao
