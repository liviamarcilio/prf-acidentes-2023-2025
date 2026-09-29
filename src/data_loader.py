"""
src/data_loader.py — Camada de Extração (Bronze)

Coleta os arquivos de acidentes da PRF por requisição HTTP, em vez de
download manual pelo navegador.

A PRF não expõe uma API REST própria para essas bases: os arquivos ficam
hospedados no Google Drive e linkados a partir da página oficial de dados
abertos (https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf).
O portal da própria PRF (portal.prf.gov.br) bloqueia acesso automatizado via
robots.txt, então a coleta aqui vai direto na origem real dos arquivos.

Os IDs abaixo foram coletados manualmente da página oficial em 27/09/2026,
localizando a linha "Documento CSV de Acidentes AAAA (Agrupados por pessoa -
Todas as causas e tipos de acidentes)". A PRF costuma trocar o ID do arquivo
sem aviso quando atualiza uma base — se o download falhar, confira o ID
atual na página e atualize aqui. Por isso toda função de coleta tem uma
queda (fallback) explícita para uma cópia já baixada manualmente (ex.: no
seu Google Drive): se o Drive mudar o link, o pipeline continua funcionando
a partir do fallback, e o motivo da falha fica sempre registrado, nunca
escondido.
"""
from __future__ import annotations

import os
import subprocess

import pandas as pd

try:
    import gdown
except ImportError:
    subprocess.run(["pip", "install", "gdown", "-q"], check=True)
    import gdown

ANOS_PADRAO = (2023, 2024, 2025)

# Referência: "Acidentes AAAA (Agrupados por pessoa - Todas as causas e
# tipos de acidentes)" na página de Dados Abertos da PRF.
DRIVE_FILE_IDS = {
    2023: "1-caam_dahYOf2eorq4mez04Om6DD5d_3",
    2024: "14qBOhrE1gioVtuXgxkCJ9kCA8YtUGXKA",
    2025: "1-PJGRbfSe7PVjU37A3wTCls_NRXyVGRD",
}

TENTATIVAS_LEITURA = [
    {"sep": ";", "encoding": "latin1"},
    {"sep": ";", "encoding": "utf-8"},
    {"sep": ",", "encoding": "utf-8"},
    {"sep": ",", "encoding": "latin1"},
]


def _nome_arquivo(ano: int) -> str:
    return f"acidentes{ano}_todas_causas_tipos.csv"


def coletar_bases(
    anos=ANOS_PADRAO,
    pasta_destino: str = "data/bronze",
    pasta_fallback: str | None = None,
    forcar_download: bool = False,
) -> dict:
    """
    Coleta os arquivos de acidentes da PRF para os anos pedidos, por
    requisição direta ao Google Drive (via gdown).

    Se o download de um ano falhar por qualquer motivo (ID mudou, sem
    internet, limite de download do Drive), cai para uma cópia já existente
    em `pasta_fallback` — o motivo da falha é sempre impresso, nunca escondido.

    :param anos: anos a coletar
    :param pasta_destino: pasta local onde salvar os CSVs baixados (bronze)
    :param pasta_fallback: pasta com cópias manuais, usada só se o download
        automático falhar para algum ano
    :param forcar_download: se True, baixa de novo mesmo que já exista localmente
    :return: dict {ano: caminho_do_arquivo_local}
    """
    os.makedirs(pasta_destino, exist_ok=True)
    caminhos = {}

    for ano in anos:
        destino = os.path.join(pasta_destino, _nome_arquivo(ano))

        if os.path.exists(destino) and not forcar_download:
            print(f"{ano}: já baixado em {destino} (pulando download)")
            caminhos[ano] = destino
            continue

        if ano not in DRIVE_FILE_IDS:
            raise ValueError(f"Não tenho o ID do Drive para o ano {ano}.")

        url = f"https://drive.google.com/uc?id={DRIVE_FILE_IDS[ano]}"
        try:
            print(f"{ano}: baixando de {url} ...")
            gdown.download(url, destino, quiet=False)
            if not os.path.exists(destino) or os.path.getsize(destino) == 0:
                raise RuntimeError("gdown não produziu um arquivo válido.")
            caminhos[ano] = destino
        except Exception as erro:  # noqa: BLE001 -- queremos cair pro fallback, não travar
            print(f"{ano}: coleta automática falhou ({erro!r}).")
            if not pasta_fallback:
                raise RuntimeError(
                    f"Coleta automática falhou para {ano} e nenhuma "
                    f"pasta_fallback foi informada."
                ) from erro
            candidato = os.path.join(pasta_fallback, _nome_arquivo(ano))
            if not os.path.exists(candidato):
                raise FileNotFoundError(
                    f"Fallback também não encontrou o arquivo de {ano} em {candidato}."
                ) from erro
            print(f"{ano}: usando fallback local em {candidato}")
            caminhos[ano] = candidato

    return caminhos


def ler_csv_prf(caminho: str) -> pd.DataFrame:
    """
    Lê um CSV de acidentes da PRF, tentando as combinações mais comuns de
    separador e encoding usadas pelo portal de dados abertos.
    """
    ultimo_erro = None
    for opcoes in TENTATIVAS_LEITURA:
        try:
            df = pd.read_csv(caminho, **opcoes, low_memory=False)
            if df.shape[1] > 1:
                df.columns = df.columns.str.strip().str.lower()
                return df
        except Exception as erro:
            ultimo_erro = erro
    raise ValueError(f"Não foi possível ler {caminho} com as combinações testadas.") from ultimo_erro


def montar_bronze(anos=ANOS_PADRAO, pasta_destino="data/bronze", pasta_fallback=None) -> pd.DataFrame:
    """
    Função de conveniência: coleta os anos pedidos e retorna o DataFrame
    bronze consolidado (concatenado, com 'ano_base' e os tipos estruturais
    id/pesid/id_veiculo já corrigidos para Int64).
    """
    caminhos = coletar_bases(anos, pasta_destino, pasta_fallback)

    dfs = []
    for ano, caminho in caminhos.items():
        df = ler_csv_prf(caminho)
        df["ano_base"] = ano
        for coluna in ("id", "pesid", "id_veiculo"):
            if coluna in df.columns:
                df[coluna] = pd.to_numeric(df[coluna], errors="coerce").astype("Int64")
        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)
