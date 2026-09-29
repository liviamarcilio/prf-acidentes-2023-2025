"""
src/quarantine.py — Camada de Transformação com Quarentena

Implementa o padrão de quarentena de dados: em vez de descartar ou corrigir
silenciosamente um registro problemático, ele é marcado com o motivo e
mantido à parte, para auditoria. Nada desaparece sem explicação.

Neste conjunto de dados, o único caso em que não é possível determinar a
gravidade de um acidente com confiança é quando NENHUMA linha daquele
acidente tem informação de vítima (mortos/feridos/ilesos todos nulos) — o
que acontece em registros de veículo sem pessoa associada. Esses casos já
são rotulados como 'Ignorado' no notebook principal (a 4ª categoria oficial
do dicionário da PRF); este módulo apenas separa esses casos para um
relatório de auditoria, sem alterar o dataset principal.
"""
from __future__ import annotations

import os

import pandas as pd


def extrair_quarentena_classificacao(df_prf: pd.DataFrame) -> pd.DataFrame:
    """
    Extrai, para auditoria, as linhas cujo acidente ficou classificado como
    'Ignorado' — ou seja, nenhuma pessoa envolvida tinha informação de
    gravidade (mortos/feridos/ilesos) preenchida em nenhuma linha daquele id.

    :param df_prf: DataFrame já passado pela reclassificação de
        classificacao_acidente (deve conter a categoria 'Ignorado' quando
        aplicável)
    :return: DataFrame só com as linhas em quarentena, com a coluna
        'motivo_quarentena' explicando o motivo
    """
    em_quarentena = df_prf["classificacao_acidente"] == "Ignorado"
    df_quarentena = df_prf[em_quarentena].copy()
    df_quarentena["motivo_quarentena"] = (
        "Nenhuma linha do acidente tinha informação de gravidade "
        "(mortos/feridos/ilesos) preenchida — classificação indeterminada."
    )
    return df_quarentena


def salvar_quarentena(df_quarentena: pd.DataFrame, pasta_destino="data/quarantine") -> str:
    """Salva o relatório de quarentena em CSV e retorna o caminho salvo."""
    os.makedirs(pasta_destino, exist_ok=True)
    destino = os.path.join(pasta_destino, "classificacao_indeterminada.csv")
    df_quarentena.to_csv(destino, index=False, encoding="utf-8")
    return destino


def reconciliar(df_bronze: pd.DataFrame, df_silver: pd.DataFrame, df_quarentena: pd.DataFrame) -> dict:
    """
    Confere que nenhuma linha sumiu sem explicação entre bronze e silver, e
    reporta quantas linhas silver estão sinalizadas em quarentena (elas
    continuam no dataset principal, só ficam também auditadas à parte).

    :return: dict com as contagens, para registro/print no notebook
    """
    return {
        "linhas_bronze": len(df_bronze),
        "linhas_silver": len(df_silver),
        "bronze_igual_silver": len(df_bronze) == len(df_silver),
        "linhas_em_quarentena": len(df_quarentena),
        "acidentes_em_quarentena": df_quarentena["id"].nunique() if len(df_quarentena) else 0,
    }
