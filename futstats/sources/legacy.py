"""Importa os dados já coletados antes desta reestruturação (pasta legacy/).

- legacy/dados_football_data_org: partidas 2023-2025 (Brasileirão, Bundesliga, Eredivisie,
  Primeira Liga, Championship) → esquema padrão de partidas.
- legacy/fbref_soccerdata/dados_times: estatísticas avançadas de times do FBref (Big 5,
  2016-17 a 2024-25, incluindo xG). Esses dados não podem mais ser coletados: o FBref
  perdeu o feed avançado da Opta em jan/2026. A liga de cada time vem das páginas em
  cache em raw_data/.

Os CSVs de jogadores (legacy/fbref_soccerdata/Big 5 ...) foram salvos sem as colunas de
jogador/time/temporada e por isso não são importados.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd

from ..config import COMPETICOES, ROOT, competicao_por_codigo
from ..teams import resolver
from . import football_data_org

log = logging.getLogger(__name__)

LEGACY = ROOT / "legacy"
FBREF_LIGAS = {"ENG-Premier League": "ENG1", "ESP-La Liga": "ESP1", "ITA-Serie A": "ITA1",
               "GER-Bundesliga": "GER1", "FRA-Ligue 1": "FRA1"}


def partidas_fdorg(pasta: Path = LEGACY / "dados_football_data_org" / "partidas_competicao") -> pd.DataFrame:
    frames = []
    for arquivo in sorted(pasta.glob("*/*/*.csv")):
        comp = competicao_por_codigo("fdorg", arquivo.parts[-3])
        if comp is None:
            log.warning("legacy: competição desconhecida em %s", arquivo)
            continue
        frames.append(football_data_org.de_csv_legado(pd.read_csv(arquivo, encoding="utf-8-sig"), comp))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _liga_por_squad(pasta_html: Path) -> dict[tuple[str, str], str]:
    """(temporada 'AAAA-AAAA', squad_id) → competicao_id, a partir das páginas em cache do FBref."""
    mapa = {}
    for arquivo in pasta_html.glob("teams_*_stats.html"):
        m = re.match(r"teams_(.+)_(\d{2})(\d{2})_stats\.html", arquivo.name)
        if not m or m.group(1) not in FBREF_LIGAS:
            continue
        temporada = f"20{m.group(2)}-20{m.group(3)}"
        html = arquivo.read_text(encoding="utf-8", errors="ignore")
        tabela = re.search(r'<table[^>]*id="stats_squads_standard_for".*?</table>', html, re.S)
        for squad in set(re.findall(r"/en/squads/([0-9a-f]{8})/", tabela.group(0) if tabela else "")):
            mapa[(temporada, squad)] = FBREF_LIGAS[m.group(1)]
    return mapa


def _achatar_colunas(colunas: pd.MultiIndex) -> list[str]:
    nomes = []
    for nivel0, nivel1 in colunas:
        n0 = "" if str(nivel0).startswith("Unnamed") else str(nivel0)
        n1 = "" if str(nivel1).startswith("Unnamed") else str(nivel1)
        nomes.append(f"{n0} | {n1}" if n0 and n1 and n0 != n1 else (n1 or n0))
    return nomes


def fbref_times(pasta: Path = LEGACY / "fbref_soccerdata") -> pd.DataFrame:
    """Formato longo: competicao_id, temporada, squad_id, time_id, time_nome, tabela, metrica, valor."""
    ligas = _liga_por_squad(pasta / "raw_data")
    frames = []
    for arquivo in sorted((pasta / "dados_times" / "Big 5 European Leagues Combined").glob("*/*.csv")):
        temporada, tabela = arquivo.parent.name, arquivo.stem
        df = pd.read_csv(arquivo, header=[0, 1])
        df.columns = _achatar_colunas(df.columns)
        if "url" not in df.columns:
            continue
        partes = df["url"].str.extract(r"/en/squads/([0-9a-f]{8})/(?:\d{4}-\d{4}/)?(.+)-Stats")
        df["squad_id"], df["time_nome"] = partes[0], partes[1].str.replace("-", " ", regex=False)
        longo = df.drop(columns=["url"]).melt(id_vars=["squad_id", "time_nome"], var_name="metrica", value_name="valor")
        longo["valor"] = pd.to_numeric(longo["valor"], errors="coerce")
        longo["temporada"], longo["tabela"] = temporada, tabela
        frames.append(longo.dropna(subset=["valor", "squad_id"]))
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    df["competicao_id"] = [ligas.get((t, s)) for t, s in zip(df["temporada"], df["squad_id"])]
    nomes = df[["time_nome"]].drop_duplicates()
    nomes["time_id"] = nomes["time_nome"].map(lambda n: resolver(n)[0])
    df = df.merge(nomes, on="time_nome", how="left")
    sem_liga = df.loc[df["competicao_id"].isna(), ["temporada", "time_nome"]].drop_duplicates()
    if not sem_liga.empty:
        log.warning("FBref: %s time-temporada sem liga identificada (página em cache ausente).", len(sem_liga))
    cols = ["competicao_id", "temporada", "squad_id", "time_id", "time_nome", "tabela", "metrica", "valor"]
    return df[cols]


def disponivel() -> bool:
    return LEGACY.exists()


__all__ = ["partidas_fdorg", "fbref_times", "disponivel", "COMPETICOES"]
