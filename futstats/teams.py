"""Normalização de nomes de times entre fontes.

Cada fonte escreve os nomes de um jeito ("CA Paranaense", "Athletico-PR",
"Athletico Paranaense"). A estratégia é:

1. `chave()` gera uma forma canônica sem acentos, pontuação e siglas comuns
   (FC, EC, SC, AFC...). Muitas variações já convergem aqui.
2. `seeds/team_aliases.csv` resolve o resto: mapeia chaves para um `time_id`
   estável e um nome de exibição. Esse arquivo é versionado e editável.
3. O que não casar em nenhum dos dois vira um id próprio e aparece no relatório
   `python -m futstats times`, para você decidir se precisa de alias.

Não há casamento aproximado ("fuzzy") de propósito: errar um cruzamento
(Man City × Man United) é pior do que deixar um nome sem casar.
"""

from __future__ import annotations

import csv
import re
import unicodedata
from functools import lru_cache

from .config import SEEDS_DIR

# Siglas e palavras que não ajudam a distinguir times.
_RUIDO = {
    "fc", "cf", "sc", "ac", "afc", "ec", "se", "cr", "fbpa", "fbc", "sad", "cd", "ud", "sd", "rc",
    "club", "clube", "futebol", "football", "calcio", "de", "da", "do", "the", "and",
    "esporte", "sport", "ssc", "as", "ss", "us", "vfb", "vfl", "tsg", "sv", "bv", "fk", "sk",
    "fsv", "bc", "cfc", "acf", "aj", "ogc", "osc", "hsc", "sco",
}


def _sem_acentos(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def chave(nome: str) -> str:
    """Forma canônica de comparação: 'Grêmio FBPA' → 'gremio'; 'Nott'm Forest' → 'nottm forest'."""
    texto = _sem_acentos(str(nome or "")).lower().replace("'", "")
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    tokens = [t for t in texto.split() if t not in _RUIDO and not t.isdigit()]
    # Se tudo era "ruído" (ex.: "AZ", "AVS"), mantém o texto original limpo.
    return " ".join(tokens) or texto.strip()


def slug(texto: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", _sem_acentos(texto).lower()).strip("-")


@lru_cache(maxsize=1)
def _aliases() -> dict[str, tuple[str, str]]:
    """chave → (time_id, nome de exibição), lido de seeds/team_aliases.csv."""
    mapa: dict[str, tuple[str, str]] = {}
    caminho = SEEDS_DIR / "team_aliases.csv"
    with caminho.open(encoding="utf-8") as fh:
        for linha in csv.DictReader(fh):
            time_id, exibicao = linha["time_id"].strip(), linha["nome_exibicao"].strip()
            for alias in [exibicao, *linha["aliases"].split("|")]:
                if alias.strip():
                    mapa[chave(alias)] = (time_id, exibicao)
    return mapa


def resolver(nome: str) -> tuple[str, str, bool]:
    """Retorna (time_id, nome_exibicao, casou_alias)."""
    k = chave(nome)
    if k in _aliases():
        time_id, exibicao = _aliases()[k]
        return time_id, exibicao, True
    return slug(k), str(nome).strip(), False


def recarregar_aliases() -> None:
    _aliases.cache_clear()
