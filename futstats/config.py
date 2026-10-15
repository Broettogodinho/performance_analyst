"""Configuração central: caminhos e catálogo de competições.

Cada competição tem um id interno estável (ex.: "BRA1") e os códigos usados
por cada fonte. Para incluir uma competição nova, adicione uma entrada em
COMPETICOES; nada mais precisa mudar.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.environ.get("FUTSTATS_DATA_DIR", ROOT / "data"))
RAW_DIR = DATA_DIR / "raw"          # respostas originais das fontes (cache)
BRONZE_DIR = DATA_DIR / "bronze"    # Parquet padronizado por fonte
GOLD_DIR = DATA_DIR / "gold"        # Parquet final, lido pelo Power BI
DB_PATH = Path(os.environ.get("FUTSTATS_DB", DATA_DIR / "futstats.duckdb"))
SQL_DIR = Path(__file__).resolve().parent / "sql"
SEEDS_DIR = Path(__file__).resolve().parent / "seeds"


@dataclass(frozen=True)
class Competicao:
    id: str
    nome: str
    pais: str
    tipo: str                      # "liga" ou "copa"
    calendario: str                # "europeu" (ago-mai, temporada 2024-2025) ou "anual" (temporada 2025)
    fdcouk: str | None = None      # código football-data.co.uk
    fdcouk_formato: str = "principal"  # "principal" (mmz4281/{temporada}/{cod}.csv) ou "extra" (new/{cod}.csv)
    fdorg: str | None = None       # código football-data.org
    statsbomb: tuple[int, ...] = field(default_factory=tuple)  # competition_id(s) StatsBomb


COMPETICOES: dict[str, Competicao] = {c.id: c for c in [
    # Brasil e América do Sul
    Competicao("BRA1", "Brasileirão Série A", "Brasil", "liga", "anual", fdcouk="BRA", fdcouk_formato="extra", fdorg="BSA"),
    Competicao("ARG1", "Liga Profesional Argentina", "Argentina", "liga", "anual", fdcouk="ARG", fdcouk_formato="extra"),
    Competicao("LIB", "Copa Libertadores", "América do Sul", "copa", "anual", fdorg="CLI"),
    # Big 5
    Competicao("ENG1", "Premier League", "Inglaterra", "liga", "europeu", fdcouk="E0", fdorg="PL", statsbomb=(2,)),
    Competicao("ESP1", "La Liga", "Espanha", "liga", "europeu", fdcouk="SP1", fdorg="PD", statsbomb=(11,)),
    Competicao("ITA1", "Serie A", "Itália", "liga", "europeu", fdcouk="I1", fdorg="SA", statsbomb=(12,)),
    Competicao("GER1", "Bundesliga", "Alemanha", "liga", "europeu", fdcouk="D1", fdorg="BL1", statsbomb=(9,)),
    Competicao("FRA1", "Ligue 1", "França", "liga", "europeu", fdcouk="F1", fdorg="FL1", statsbomb=(7,)),
    # Outras
    Competicao("ENG2", "Championship", "Inglaterra", "liga", "europeu", fdcouk="E1", fdorg="ELC"),
    Competicao("POR1", "Primeira Liga", "Portugal", "liga", "europeu", fdcouk="P1", fdorg="PPL"),
    Competicao("NED1", "Eredivisie", "Holanda", "liga", "europeu", fdcouk="N1", fdorg="DED"),
    Competicao("USA1", "MLS", "Estados Unidos", "liga", "anual", fdcouk="USA", fdcouk_formato="extra", statsbomb=(44,)),
    # Continentais / seleções
    Competicao("UCL", "UEFA Champions League", "Europa", "copa", "europeu", fdorg="CL", statsbomb=(16,)),
    Competicao("WC", "Copa do Mundo FIFA", "Mundo", "copa", "anual", fdorg="WC", statsbomb=(43,)),
    Competicao("EURO", "Eurocopa", "Europa", "copa", "anual", fdorg="EC", statsbomb=(55,)),
]}


def competicao_por_codigo(fonte: str, codigo: str) -> Competicao | None:
    """Encontra a competição pelo código de uma fonte ("fdcouk", "fdorg")."""
    for comp in COMPETICOES.values():
        if getattr(comp, fonte) == codigo:
            return comp
    return None


def rotulo_temporada(comp: Competicao, ano_inicio: int) -> str:
    """'2024-2025' para calendário europeu, '2025' para ligas anuais."""
    return f"{ano_inicio}-{ano_inicio + 1}" if comp.calendario == "europeu" else str(ano_inicio)


def ano_inicio_temporada(comp: Competicao, data) -> int:
    """Ano de início da temporada a que uma data pertence (europeu: vira em julho)."""
    if comp.calendario == "europeu":
        return data.year if data.month >= 7 else data.year - 1
    return data.year
