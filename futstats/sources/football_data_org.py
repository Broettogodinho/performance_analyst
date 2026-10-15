"""football-data.org (API v4): partidas com ids estáveis, rodada e fase.

Precisa de token gratuito (https://www.football-data.org/client/register) na variável
FOOTBALL_DATA_TOKEN ou no arquivo .env. O plano grátis permite 10 requisições/min e
cobre, entre outras, Brasileirão (BSA), Champions (CL), Big 5, Eredivisie, Primeira Liga,
Championship, Copa do Mundo e Eurocopa. Libertadores (CLI) exige plano pago.
"""

from __future__ import annotations

import json
import logging
import os

import pandas as pd

from ..config import Competicao, rotulo_temporada
from ..http import Fetcher
from ..schema import padronizar_partidas

log = logging.getLogger(__name__)

BASE = "https://api.football-data.org/v4"


def _fetcher() -> Fetcher:
    token = os.environ.get("FOOTBALL_DATA_TOKEN")
    if not token:
        raise RuntimeError("Defina FOOTBALL_DATA_TOKEN (token gratuito em football-data.org) no ambiente ou no .env.")
    return Fetcher("fdorg", pausa_s=6.5, headers={"X-Auth-Token": token})


def _de_partidas(partidas: list[dict], comp: Competicao, temporada: str) -> pd.DataFrame:
    linhas = []
    for p in partidas:
        placar = p.get("score") or {}
        ft, ht = placar.get("fullTime") or {}, placar.get("halfTime") or {}
        linhas.append({
            "id_fonte": str(p.get("id")),
            "data": p.get("utcDate"),
            "rodada": p.get("matchday"),
            "fase": p.get("stage"),
            "mandante_nome": (p.get("homeTeam") or {}).get("name"),
            "visitante_nome": (p.get("awayTeam") or {}).get("name"),
            "gols_mandante": ft.get("home"),
            "gols_visitante": ft.get("away"),
            "gols_mandante_1t": ht.get("home"),
            "gols_visitante_1t": ht.get("away"),
            "arbitro": next((r.get("name") for r in p.get("referees") or [] if r.get("type") == "REFEREE"), None),
        })
    df = pd.DataFrame(linhas)
    if df.empty:
        return padronizar_partidas(df)
    datas = pd.to_datetime(df["data"], utc=True)
    df["hora"] = datas.dt.strftime("%H:%M")  # UTC
    df["data"] = datas.dt.tz_localize(None).dt.normalize()
    df["fonte"], df["competicao_id"], df["temporada"] = "fdorg", comp.id, temporada
    return padronizar_partidas(df)


def coletar(comp: Competicao, anos_inicio: list[int]) -> pd.DataFrame:
    if not comp.fdorg:
        return padronizar_partidas(pd.DataFrame())
    fetcher = _fetcher()
    frames = []
    ultimo = max(anos_inicio)
    for ano in anos_inicio:
        conteudo = fetcher.get(f"{BASE}/competitions/{comp.fdorg}/matches", params={"season": ano, "status": "FINISHED"},
                               refresh=ano == ultimo)
        if not conteudo:
            log.info("fdorg: sem dados para %s %s (fora do plano ou inexistente)", comp.id, ano)
            continue
        dados = json.loads(conteudo)
        frames.append(_de_partidas(dados.get("matches", []), comp, rotulo_temporada(comp, ano)))
    return pd.concat(frames, ignore_index=True) if frames else padronizar_partidas(pd.DataFrame())


def de_csv_legado(df: pd.DataFrame, comp: Competicao) -> pd.DataFrame:
    """Converte os CSVs antigos (legacy/dados_football_data_org) para o esquema padrão."""
    out = pd.DataFrame({
        "id_fonte": df["id"].astype(str),
        "data": df["utcDate"],
        "rodada": df.get("matchday"),
        "fase": df.get("stage"),
        "mandante_nome": df["homeTeam_name"],
        "visitante_nome": df["awayTeam_name"],
        "gols_mandante": df["score_fullTime_home"],
        "gols_visitante": df["score_fullTime_away"],
        "gols_mandante_1t": df.get("score_halfTime_home"),
        "gols_visitante_1t": df.get("score_halfTime_away"),
    })
    datas = pd.to_datetime(out["data"], utc=True)
    out["hora"] = datas.dt.strftime("%H:%M")
    out["data"] = datas.dt.tz_localize(None).dt.normalize()
    anos = pd.to_datetime(df["season_startDate"]).dt.year
    out["temporada"] = anos.map(lambda a: rotulo_temporada(comp, int(a)))
    out["fonte"], out["competicao_id"] = "fdorg", comp.id
    return padronizar_partidas(out)
