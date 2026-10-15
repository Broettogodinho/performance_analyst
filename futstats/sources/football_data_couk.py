"""football-data.co.uk: resultados, estatísticas básicas e odds (CSV gratuito).

Dois formatos:
- principal: https://www.football-data.co.uk/mmz4281/{AAaa}/{cod}.csv, um arquivo por temporada
  (ligas europeias; inclui chutes, escanteios, cartões, árbitro e várias casas de aposta);
- extra:     https://www.football-data.co.uk/new/{cod}.csv, todas as temporadas num arquivo
  (Brasil, Argentina, MLS...; resultados e odds de fechamento).

Uso pessoal/pesquisa; o site pede apenas que a fonte seja citada.
"""

from __future__ import annotations

import io
import logging

import pandas as pd

from ..config import Competicao, rotulo_temporada
from ..http import Fetcher
from ..schema import padronizar_partidas

log = logging.getLogger(__name__)

BASE = "https://www.football-data.co.uk"
_fetcher = Fetcher("fdcouk", pausa_s=1.5)

MAPA_PRINCIPAL = {
    "HomeTeam": "mandante_nome", "AwayTeam": "visitante_nome",
    "FTHG": "gols_mandante", "FTAG": "gols_visitante", "HTHG": "gols_mandante_1t", "HTAG": "gols_visitante_1t",
    "HS": "chutes_mandante", "AS": "chutes_visitante", "HST": "chutes_alvo_mandante", "AST": "chutes_alvo_visitante",
    "HC": "escanteios_mandante", "AC": "escanteios_visitante", "HF": "faltas_mandante", "AF": "faltas_visitante",
    "HY": "amarelos_mandante", "AY": "amarelos_visitante", "HR": "vermelhos_mandante", "AR": "vermelhos_visitante",
    "Referee": "arbitro", "Time": "hora",
}
MAPA_EXTRA = {
    "Home": "mandante_nome", "Away": "visitante_nome", "HG": "gols_mandante", "AG": "gols_visitante", "Time": "hora",
}
# Preferência de odds: média de mercado > Bet365 > Pinnacle (abertura); Pinnacle > média > Bet365 (fechamento).
ODDS_PRE = [("AvgH", "AvgD", "AvgA"), ("BbAvH", "BbAvD", "BbAvA"), ("B365H", "B365D", "B365A"), ("PSH", "PSD", "PSA")]
ODDS_FECH = [("PSCH", "PSCD", "PSCA"), ("AvgCH", "AvgCD", "AvgCA"), ("B365CH", "B365CD", "B365CA")]


def _ler_csv(conteudo: bytes) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            df = pd.read_csv(io.BytesIO(conteudo), encoding=encoding, on_bad_lines="skip")
            break
        except UnicodeDecodeError:
            continue
    df = df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]
    return df.dropna(how="all")


def _primeiro_disponivel(df: pd.DataFrame, opcoes, destino: tuple[str, str, str]) -> pd.DataFrame:
    """Preenche as colunas destino com a primeira casa de aposta disponível, jogo a jogo."""
    for alvo in destino:
        df[alvo] = float("nan")
    for trio in opcoes:
        if not all(c in df.columns for c in trio):
            continue
        valores = df[list(trio)].apply(pd.to_numeric, errors="coerce")
        vazio = df[list(destino)].isna().all(axis=1) & valores.notna().all(axis=1)
        df.loc[vazio, list(destino)] = valores.loc[vazio].to_numpy()
    return df


def _parse_datas(serie: pd.Series) -> pd.Series:
    """Datas vêm como dd/mm/aa (antigas) ou dd/mm/aaaa."""
    longas = pd.to_datetime(serie, format="%d/%m/%Y", errors="coerce")
    curtas = pd.to_datetime(serie, format="%d/%m/%y", errors="coerce")
    return longas.fillna(curtas)


def parse(conteudo: bytes, comp: Competicao, temporada: str | None = None) -> pd.DataFrame:
    """Converte o CSV (qualquer um dos dois formatos) para o esquema padrão."""
    bruto = _ler_csv(conteudo)
    extra = "Home" in bruto.columns and "HomeTeam" not in bruto.columns
    df = bruto.rename(columns=MAPA_EXTRA if extra else MAPA_PRINCIPAL)
    df["data"] = _parse_datas(df["Date"].astype(str))

    if extra:
        # "2024" ou "2012/2013" → rótulo padrão da competição
        df["temporada"] = df["Season"].astype(str).str.slice(0, 4).astype(int).map(lambda a: rotulo_temporada(comp, a))
    else:
        df["temporada"] = temporada

    df = _primeiro_disponivel(df, ODDS_PRE, ("odd_mandante", "odd_empate", "odd_visitante"))
    df = _primeiro_disponivel(df, ODDS_FECH, ("odd_fech_mandante", "odd_fech_empate", "odd_fech_visitante"))
    df["fonte"] = "fdcouk"
    df["competicao_id"] = comp.id
    df["id_fonte"] = (comp.fdcouk + "_" + df["data"].dt.strftime("%Y%m%d") + "_"
                      + df["mandante_nome"].astype(str) + "_" + df["visitante_nome"].astype(str))
    return padronizar_partidas(df)


def coletar(comp: Competicao, anos_inicio: list[int], refresh_atual: bool = True) -> pd.DataFrame:
    """Baixa e padroniza as temporadas pedidas. Retorna DataFrame vazio se a competição não tem código."""
    if not comp.fdcouk:
        return padronizar_partidas(pd.DataFrame())

    if comp.fdcouk_formato == "extra":
        conteudo = _fetcher.get(f"{BASE}/new/{comp.fdcouk}.csv", ext="csv", refresh=refresh_atual)
        if conteudo is None:
            return padronizar_partidas(pd.DataFrame())
        df = parse(conteudo, comp)
        rotulos = {rotulo_temporada(comp, a) for a in anos_inicio}
        return df[df["temporada"].isin(rotulos)].reset_index(drop=True)

    frames = []
    ultimo = max(anos_inicio)
    for ano in anos_inicio:
        codigo_temp = f"{ano % 100:02d}{(ano + 1) % 100:02d}"
        url = f"{BASE}/mmz4281/{codigo_temp}/{comp.fdcouk}.csv"
        conteudo = _fetcher.get(url, ext="csv", refresh=refresh_atual and ano == ultimo)
        if conteudo:
            frames.append(parse(conteudo, comp, rotulo_temporada(comp, ano)))
        else:
            log.info("fdcouk: sem arquivo para %s %s", comp.id, ano)
    return pd.concat(frames, ignore_index=True) if frames else padronizar_partidas(pd.DataFrame())
