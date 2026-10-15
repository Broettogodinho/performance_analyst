"""Esquema padrão de partidas, comum a todas as fontes (camada bronze)."""

from __future__ import annotations

import pandas as pd

from .teams import resolver

# Ordem e tipos das colunas de partidas. Colunas que a fonte não fornece ficam nulas.
COLUNAS_PARTIDA: dict[str, str] = {
    "fonte": "string",
    "id_fonte": "string",
    "competicao_id": "string",
    "temporada": "string",
    "data": "datetime64[ns]",
    "hora": "string",
    "rodada": "Int64",
    "fase": "string",
    "mandante_nome": "string",
    "visitante_nome": "string",
    "mandante_id": "string",
    "visitante_id": "string",
    "gols_mandante": "Int64",
    "gols_visitante": "Int64",
    "gols_mandante_1t": "Int64",
    "gols_visitante_1t": "Int64",
    "chutes_mandante": "Int64",
    "chutes_visitante": "Int64",
    "chutes_alvo_mandante": "Int64",
    "chutes_alvo_visitante": "Int64",
    "escanteios_mandante": "Int64",
    "escanteios_visitante": "Int64",
    "faltas_mandante": "Int64",
    "faltas_visitante": "Int64",
    "amarelos_mandante": "Int64",
    "amarelos_visitante": "Int64",
    "vermelhos_mandante": "Int64",
    "vermelhos_visitante": "Int64",
    "xg_mandante": "float64",
    "xg_visitante": "float64",
    "arbitro": "string",
    # Odds decimais 1X2. "abertura" = média de mercado pré-jogo; "fechamento" = Pinnacle ou média no fechamento.
    "odd_mandante": "float64",
    "odd_empate": "float64",
    "odd_visitante": "float64",
    "odd_fech_mandante": "float64",
    "odd_fech_empate": "float64",
    "odd_fech_visitante": "float64",
}


def padronizar_partidas(df: pd.DataFrame) -> pd.DataFrame:
    """Garante todas as colunas, tipos corretos e ids de times resolvidos."""
    df = df.copy()
    for coluna in COLUNAS_PARTIDA:
        if coluna not in df.columns:
            df[coluna] = pd.NA
    for lado in ("mandante", "visitante"):
        resolvidos = df[f"{lado}_nome"].map(lambda n: resolver(n)[0] if pd.notna(n) else pd.NA)
        df[f"{lado}_id"] = df[f"{lado}_id"].where(df[f"{lado}_id"].notna(), resolvidos)
    df = df[list(COLUNAS_PARTIDA)]
    for coluna, tipo in COLUNAS_PARTIDA.items():
        if tipo == "Int64":
            df[coluna] = pd.to_numeric(df[coluna], errors="coerce").round().astype("Int64")
        elif tipo == "float64":
            df[coluna] = pd.to_numeric(df[coluna], errors="coerce").astype("float64")
        elif tipo.startswith("datetime"):
            df[coluna] = pd.to_datetime(df[coluna], errors="coerce")
        else:
            df[coluna] = df[coluna].astype("string")
    return df.dropna(subset=["data", "mandante_nome", "visitante_nome"]).reset_index(drop=True)
