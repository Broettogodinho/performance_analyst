"""Monta a base: bronze → silver (partidas consolidadas) → gold (DuckDB + Parquet para o Power BI)."""

from __future__ import annotations

import csv
import logging
from dataclasses import asdict

import duckdb
import pandas as pd

from .config import COMPETICOES, DB_PATH, GOLD_DIR, SEEDS_DIR, SQL_DIR
from .storage import consolidar_partidas, gravar_silver, ler_bronze
from .teams import chave, resolver

log = logging.getLogger(__name__)

TABELAS_GOLD = ["dim_competicao", "dim_time", "dim_temporada", "dim_data", "fato_partida", "fato_time_partida",
                "classificacao", "fato_chute", "fbref_time_temporada", "fbref_resumo"]


def _dim_competicao() -> pd.DataFrame:
    linhas = []
    for c in COMPETICOES.values():
        d = asdict(c)
        d["statsbomb"] = ",".join(map(str, c.statsbomb))
        linhas.append(d)
    return pd.DataFrame(linhas).rename(columns={"id": "competicao_id"})


def _dim_time(partidas: pd.DataFrame, chutes: pd.DataFrame, fbref: pd.DataFrame) -> pd.DataFrame:
    """Um registro por time_id, com nome de exibição, país e se veio de alias curado."""
    nomes = []
    if not partidas.empty:
        for lado in ("mandante", "visitante"):
            nomes.append(partidas[[f"{lado}_id", f"{lado}_nome", "competicao_id"]].set_axis(["time_id", "nome", "competicao_id"], axis=1))
    if not fbref.empty:
        nomes.append(fbref[["time_id", "time_nome", "competicao_id"]].set_axis(["time_id", "nome", "competicao_id"], axis=1))
    if not chutes.empty:
        nomes.append(chutes[["time_id", "time_nome", "competicao_id"]].set_axis(["time_id", "nome", "competicao_id"], axis=1))
    if not nomes:
        return pd.DataFrame(columns=["time_id", "nome_exibicao", "pais", "alias_curado"])
    todos = pd.concat(nomes, ignore_index=True).dropna(subset=["time_id"])

    seed = {}
    with (SEEDS_DIR / "team_aliases.csv").open(encoding="utf-8") as fh:
        for linha in csv.DictReader(fh):
            seed[linha["time_id"]] = (linha["nome_exibicao"], linha["pais"])

    paises = {c.id: c.pais for c in COMPETICOES.values()}
    linhas = []
    for time_id, grupo in todos.groupby("time_id"):
        if time_id in seed:
            nome, pais, curado = *seed[time_id], True
        else:
            nome = grupo["nome"].mode().iat[0]
            ligas = grupo["competicao_id"].map(paises).dropna()
            ligas = ligas[~ligas.isin(["Europa", "Mundo", "América do Sul"])]
            pais, curado = (ligas.mode().iat[0] if not ligas.empty else None), False
        linhas.append({"time_id": time_id, "nome_exibicao": nome, "pais": pais, "alias_curado": curado})
    return pd.DataFrame(linhas)


def relatorio_times(partidas: pd.DataFrame) -> pd.DataFrame:
    """Nomes que não casaram com nenhum alias, por fonte e competição (para revisar o seed)."""
    if partidas.empty:
        return pd.DataFrame()
    linhas = []
    for lado in ("mandante", "visitante"):
        linhas.append(partidas[["fonte", "competicao_id", f"{lado}_nome"]].set_axis(["fonte", "competicao_id", "nome"], axis=1))
    df = pd.concat(linhas).drop_duplicates()
    df["chave"] = df["nome"].map(chave)
    df["time_id"], df["casou_alias"] = zip(*df["nome"].map(lambda n: resolver(n)[::2]))
    # Um time_id visto em só uma fonte de uma competição com várias fontes é suspeito de não ter casado.
    fontes_comp = df.groupby("competicao_id")["fonte"].nunique()
    fontes_time = df.groupby(["competicao_id", "time_id"])["fonte"].nunique()
    df["fontes_do_time"] = [fontes_time[(c, t)] for c, t in zip(df["competicao_id"], df["time_id"])]
    df["fontes_da_comp"] = df["competicao_id"].map(fontes_comp)
    df["suspeito"] = ~df["casou_alias"] & (df["fontes_do_time"] < df["fontes_da_comp"])
    return df.sort_values(["suspeito", "competicao_id", "chave"], ascending=[False, True, True])


def construir() -> dict[str, int]:
    bruto = ler_bronze("partidas")
    partidas = consolidar_partidas(bruto)
    gravar_silver(partidas, "partidas")

    chutes = ler_bronze("chutes")
    if not chutes.empty:
        chutes["time_id"] = chutes["time_nome"].map(lambda n: resolver(n)[0])
        mapa_partida = bruto[bruto["fonte"] == "statsbomb"][["id_fonte", "competicao_id", "temporada", "mandante_id", "visitante_id", "data"]]
        mapa_partida = mapa_partida.assign(partida_id=lambda d: d["competicao_id"].astype(str) + "|" + d["temporada"].astype(str) + "|"
                                           + pd.to_datetime(d["data"]).dt.strftime("%Y-%m-%d") + "|" + d["mandante_id"] + "|" + d["visitante_id"])
        chutes = chutes.merge(mapa_partida[["id_fonte", "partida_id"]], left_on="match_id", right_on="id_fonte", how="left").drop(columns="id_fonte")
    fbref = ler_bronze("fbref_times")

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))
    try:
        con.register("silver_partidas", partidas)
        con.register("bronze_chutes", chutes if not chutes.empty else pd.DataFrame({"partida_id": pd.Series(dtype="string")}))
        con.register("bronze_fbref_times", fbref if not fbref.empty else pd.DataFrame(
            {c: pd.Series(dtype="string") for c in ["competicao_id", "temporada", "squad_id", "time_id", "time_nome", "tabela", "metrica"]}
            | {"valor": pd.Series(dtype="float64")}))
        con.register("dim_competicao", _dim_competicao())
        con.register("dim_time", _dim_time(partidas, chutes, fbref))
        con.execute((SQL_DIR / "gold.sql").read_text(encoding="utf-8"))

        GOLD_DIR.mkdir(parents=True, exist_ok=True)
        contagem = {}
        for tabela in TABELAS_GOLD:
            destino = GOLD_DIR / f"{tabela}.parquet"
            con.execute(f"COPY gold.{tabela} TO '{destino.as_posix()}' (FORMAT parquet)")
            contagem[tabela] = con.execute(f"SELECT COUNT(*) FROM gold.{tabela}").fetchone()[0]
    finally:
        con.close()
    log.info("gold: %s", contagem)
    return contagem
