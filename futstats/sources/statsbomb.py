"""StatsBomb Open Data: eventos lance a lance (com xG) de competições selecionadas.

Fonte: https://github.com/statsbomb/open-data. Uso gratuito com atribuição
("Data provided by StatsBomb" + logo em publicações). A cobertura é parcial
(temporadas escolhidas pela StatsBomb), mas ideal para modelos de xG e análise tática.
"""

from __future__ import annotations

import json
import logging

import pandas as pd

from ..config import COMPETICOES, Competicao
from ..http import Fetcher
from ..schema import padronizar_partidas

log = logging.getLogger(__name__)

BASE = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
_fetcher = Fetcher("statsbomb", pausa_s=0.2)


def competicoes_disponiveis() -> pd.DataFrame:
    dados = json.loads(_fetcher.get(f"{BASE}/competitions.json", refresh=True))
    df = pd.DataFrame(dados)
    mapa = {sb: c.id for c in COMPETICOES.values() for sb in c.statsbomb}
    df["competicao_id"] = df["competition_id"].map(mapa)
    return df


def _temporada_padrao(nome_sb: str) -> str:
    """'2023/2024' → '2023-2024'; '2022' → '2022'."""
    return nome_sb.replace("/", "-")


def partidas(comp: Competicao, season_id: int, season_name: str) -> pd.DataFrame:
    dados = json.loads(_fetcher.get(f"{BASE}/matches/{comp.statsbomb[0]}/{season_id}.json") or b"[]")
    df = pd.DataFrame({
        "id_fonte": [str(m["match_id"]) for m in dados],
        "data": [m["match_date"] for m in dados],
        "hora": [(m.get("kick_off") or "")[:5] for m in dados],
        "rodada": [m.get("match_week") for m in dados],
        "fase": [(m.get("competition_stage") or {}).get("name") for m in dados],
        "mandante_nome": [m["home_team"]["home_team_name"] for m in dados],
        "visitante_nome": [m["away_team"]["away_team_name"] for m in dados],
        "gols_mandante": [m.get("home_score") for m in dados],
        "gols_visitante": [m.get("away_score") for m in dados],
        "arbitro": [(m.get("referee") or {}).get("name") for m in dados],
    })
    df["fonte"], df["competicao_id"], df["temporada"] = "statsbomb", comp.id, _temporada_padrao(season_name)
    return df


def chutes_da_partida(match_id: str) -> pd.DataFrame:
    """Todos os chutes da partida, com xG StatsBomb, local e contexto."""
    eventos = json.loads(_fetcher.get(f"{BASE}/events/{match_id}.json") or b"[]")
    linhas = []
    for e in eventos:
        if e.get("type", {}).get("name") != "Shot":
            continue
        chute = e.get("shot", {})
        x, y = (e.get("location") or [None, None])[:2]
        linhas.append({
            "match_id": str(match_id),
            "evento_id": e["id"],
            "periodo": e.get("period"),
            "minuto": e.get("minute"),
            "segundo": e.get("second"),
            "time_nome": e.get("team", {}).get("name"),
            "jogador_nome": e.get("player", {}).get("name"),
            "jogador_sb_id": e.get("player", {}).get("id"),
            "posicao": e.get("position", {}).get("name"),
            "x": x, "y": y,
            "xg": chute.get("statsbomb_xg"),
            "resultado": chute.get("outcome", {}).get("name"),
            "gol": chute.get("outcome", {}).get("name") == "Goal",
            "parte_corpo": chute.get("body_part", {}).get("name"),
            "tecnica": chute.get("technique", {}).get("name"),
            "tipo": chute.get("type", {}).get("name"),
            "jogada": e.get("play_pattern", {}).get("name"),
            "primeiro_toque": bool(chute.get("first_time", False)),
            "sob_pressao": bool(e.get("under_pressure", False)),
        })
    return pd.DataFrame(linhas)


def coletar(comp: Competicao, temporadas: list[str] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Retorna (partidas padronizadas com xG, chutes). `temporadas` no formato '2023-2024'; None = todas."""
    if not comp.statsbomb:
        return padronizar_partidas(pd.DataFrame()), pd.DataFrame()
    disp = competicoes_disponiveis()
    disp = disp[(disp["competition_id"] == comp.statsbomb[0]) & (disp["competition_gender"] == "male")]
    if temporadas:
        disp = disp[disp["season_name"].map(_temporada_padrao).isin(temporadas)]

    frames_p, frames_c = [], []
    for _, temp in disp.iterrows():
        df_p = partidas(comp, int(temp["season_id"]), temp["season_name"])
        log.info("statsbomb: %s %s, %s partidas", comp.id, temp["season_name"], len(df_p))
        chutes = [chutes_da_partida(mid) for mid in df_p["id_fonte"]]
        df_c = pd.concat([c for c in chutes if not c.empty], ignore_index=True) if any(not c.empty for c in chutes) else pd.DataFrame()
        if not df_c.empty:
            df_c["competicao_id"], df_c["temporada"] = comp.id, _temporada_padrao(temp["season_name"])
            xg = df_c.groupby(["match_id", "time_nome"])["xg"].sum()
            df_p["xg_mandante"] = [xg.get((m, t)) for m, t in zip(df_p["id_fonte"], df_p["mandante_nome"])]
            df_p["xg_visitante"] = [xg.get((m, t)) for m, t in zip(df_p["id_fonte"], df_p["visitante_nome"])]
            chutes_por_time = df_c.groupby(["match_id", "time_nome"]).size()
            df_p["chutes_mandante"] = [chutes_por_time.get((m, t), 0) for m, t in zip(df_p["id_fonte"], df_p["mandante_nome"])]
            df_p["chutes_visitante"] = [chutes_por_time.get((m, t), 0) for m, t in zip(df_p["id_fonte"], df_p["visitante_nome"])]
        frames_p.append(padronizar_partidas(df_p))
        frames_c.append(df_c)
    partidas_df = pd.concat(frames_p, ignore_index=True) if frames_p else padronizar_partidas(pd.DataFrame())
    chutes_df = pd.concat([c for c in frames_c if not c.empty], ignore_index=True) if any(not c.empty for c in frames_c) else pd.DataFrame()
    return partidas_df, chutes_df
