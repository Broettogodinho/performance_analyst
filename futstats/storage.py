"""Gravação da camada bronze (Parquet particionado) e consolidação das partidas (silver)."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

import pandas as pd

from .config import BRONZE_DIR, DATA_DIR
from .schema import COLUNAS_PARTIDA

log = logging.getLogger(__name__)

SILVER_DIR = DATA_DIR / "silver"
# Quanto menor, maior a prioridade quando duas fontes trazem o mesmo campo.
PRIORIDADE_FONTE = {"fdorg": 1, "statsbomb": 2, "fdcouk": 3}
TOLERANCIA_DIAS = 2


def gravar_bronze(df: pd.DataFrame, dataset: str, particoes: list[str]) -> int:
    """Grava um Parquet por partição, substituindo o que existia (recoletar é idempotente)."""
    if df is None or df.empty:
        return 0
    for valores, grupo in df.groupby(particoes, dropna=False):
        valores = valores if isinstance(valores, tuple) else (valores,)
        pasta = BRONZE_DIR / dataset
        for nome, valor in zip(particoes, valores):
            pasta = pasta / f"{nome}={valor}"
        if pasta.exists():
            shutil.rmtree(pasta)
        pasta.mkdir(parents=True)
        grupo.drop(columns=particoes).to_parquet(pasta / "part-0.parquet", index=False)
    log.info("bronze/%s: %s linhas gravadas", dataset, len(df))
    return len(df)


def ler_bronze(dataset: str) -> pd.DataFrame:
    pasta = BRONZE_DIR / dataset
    if not pasta.exists() or not any(pasta.rglob("*.parquet")):
        return pd.DataFrame()
    return pd.read_parquet(pasta)  # pyarrow reconstrói as colunas de partição (hive)


def consolidar_partidas(bruto: pd.DataFrame) -> pd.DataFrame:
    """Une as partidas de todas as fontes em uma linha por jogo.

    Mesmo jogo = mesma competição, temporada, mandante e visitante, com datas a até
    TOLERANCIA_DIAS de distância (datas UTC × locais). Cada campo vem da fonte de maior
    prioridade que o tenha preenchido; `fontes` registra de onde veio a partida.
    """
    if bruto.empty:
        return pd.DataFrame(columns=["partida_id", *COLUNAS_PARTIDA, "fontes"])
    df = bruto.copy()
    for col in ("competicao_id", "temporada", "fonte"):
        df[col] = df[col].astype(str)
    df["data"] = pd.to_datetime(df["data"])
    df["_prio"] = df["fonte"].map(PRIORIDADE_FONTE).fillna(9)
    df = df.sort_values(["competicao_id", "temporada", "mandante_id", "visitante_id", "data", "_prio"])

    chave = ["competicao_id", "temporada", "mandante_id", "visitante_id"]
    mudou_chave = df[chave].ne(df[chave].shift()).any(axis=1).fillna(True).astype(bool)
    datas_distantes = (df["data"] - df["data"].shift()).dt.days.gt(TOLERANCIA_DIAS).fillna(True).astype(bool)
    df["_grupo"] = (mudou_chave | datas_distantes).astype("int64").cumsum()

    df = df.sort_values(["_grupo", "_prio"])
    campos = [c for c in COLUNAS_PARTIDA if c not in ("fonte", "id_fonte")]
    consolidado = df.groupby("_grupo", sort=False)[campos].first()  # first() ignora nulos → coalesce por prioridade
    consolidado["fontes"] = df.groupby("_grupo", sort=False)["fonte"].agg(lambda s: ",".join(sorted(set(s))))
    consolidado["ids_fonte"] = df.groupby("_grupo", sort=False).apply(
        lambda g: ";".join(f"{f}:{i}" for f, i in zip(g["fonte"], g["id_fonte"])), include_groups=False)
    # Data oficial: a da fonte de maior prioridade que não usa UTC (fdcouk/statsbomb usam data local).
    datas_locais = df[df["fonte"] != "fdorg"].groupby("_grupo")["data"].first()
    consolidado["data"] = datas_locais.reindex(consolidado.index).fillna(consolidado["data"])

    consolidado = consolidado.reset_index(drop=True)
    consolidado["partida_id"] = (consolidado["competicao_id"] + "|" + consolidado["temporada"] + "|"
                                 + consolidado["data"].dt.strftime("%Y-%m-%d") + "|"
                                 + consolidado["mandante_id"] + "|" + consolidado["visitante_id"])
    return consolidado[["partida_id", *campos, "fontes", "ids_fonte"]]


def gravar_silver(df: pd.DataFrame, nome: str) -> Path:
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    destino = SILVER_DIR / f"{nome}.parquet"
    df.to_parquet(destino, index=False)
    return destino
