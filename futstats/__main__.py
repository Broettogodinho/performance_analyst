"""Linha de comando do futstats.

    python -m futstats coletar fdcouk --comp BRA1 ENG1 --desde 2015
    python -m futstats coletar fdorg  --comp BRA1 UCL --desde 2023
    python -m futstats coletar statsbomb --comp GER1 --temporadas 2023-2024
    python -m futstats importar-legado
    python -m futstats construir
    python -m futstats times            # nomes de times sem alias (para revisar o seed)
    python -m futstats competicoes
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import date
from pathlib import Path

import pandas as pd

from .config import COMPETICOES, DATA_DIR, ROOT, ano_inicio_temporada


def _carregar_env(caminho: Path = ROOT / ".env") -> None:
    if caminho.exists():
        for linha in caminho.read_text(encoding="utf-8").splitlines():
            if "=" in linha and not linha.lstrip().startswith("#"):
                k, v = linha.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))


def _anos(comp, desde: int | None, ate: int | None) -> list[int]:
    atual = ano_inicio_temporada(comp, date.today())
    return list(range(desde or atual, (ate or atual) + 1))


def cmd_coletar(args) -> int:
    from .storage import gravar_bronze
    comps = [COMPETICOES[c] for c in (args.comp or COMPETICOES)]
    total = 0
    for comp in comps:
        if args.fonte == "fdcouk":
            from .sources import football_data_couk as src
            df = src.coletar(comp, _anos(comp, args.desde, args.ate))
        elif args.fonte == "fdorg":
            from .sources import football_data_org as src
            df = src.coletar(comp, _anos(comp, args.desde, args.ate))
        else:
            from .sources import statsbomb as src
            df, chutes = src.coletar(comp, args.temporadas)
            gravar_bronze(chutes, "chutes", ["competicao_id", "temporada"])
        if df.empty:
            logging.info("%s: nada coletado para %s", args.fonte, comp.id)
            continue
        total += gravar_bronze(df, "partidas", ["fonte", "competicao_id", "temporada"])
    print(f"{total} partidas gravadas na camada bronze.")
    return 0


def cmd_importar_legado(_args) -> int:
    from .sources import legacy
    from .storage import gravar_bronze
    partidas = legacy.partidas_fdorg()
    n1 = gravar_bronze(partidas, "partidas", ["fonte", "competicao_id", "temporada"])
    fbref = legacy.fbref_times()
    n2 = gravar_bronze(fbref, "fbref_times", ["temporada"])
    print(f"Legado importado: {n1} partidas (football-data.org) e {n2} métricas de times (FBref).")
    return 0


def cmd_construir(_args) -> int:
    from .build import construir
    for tabela, linhas in construir().items():
        print(f"  gold.{tabela:<22} {linhas:>9,} linhas".replace(",", "."))
    print(f"\nBase: {DATA_DIR / 'futstats.duckdb'}\nParquet para o Power BI: {DATA_DIR / 'gold'}")
    return 0


def cmd_times(args) -> int:
    from .build import relatorio_times
    from .storage import ler_bronze
    rel = relatorio_times(ler_bronze("partidas"))
    if rel.empty:
        print("Nenhuma partida na base ainda.")
        return 0
    if not args.todos:
        rel = rel[rel["suspeito"]]
    with pd.option_context("display.max_rows", 500, "display.width", 160):
        print(rel[["competicao_id", "fonte", "nome", "chave", "time_id"]].to_string(index=False) if not rel.empty
              else "Nenhum nome suspeito: todas as fontes casaram.")
    return 0


def cmd_competicoes(_args) -> int:
    for c in COMPETICOES.values():
        fontes = [f for f, v in (("fdcouk", c.fdcouk), ("fdorg", c.fdorg), ("statsbomb", c.statsbomb)) if v]
        print(f"{c.id:<6} {c.nome:<30} {c.pais:<16} fontes: {', '.join(fontes)}")
    return 0


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    _carregar_env()
    parser = argparse.ArgumentParser(prog="futstats", description="Base de dados de futebol")
    sub = parser.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("coletar", help="coleta partidas de uma fonte para a camada bronze")
    p.add_argument("fonte", choices=["fdcouk", "fdorg", "statsbomb"])
    p.add_argument("--comp", nargs="+", choices=sorted(COMPETICOES), help="competições (padrão: todas da fonte)")
    p.add_argument("--desde", type=int, help="ano de início da primeira temporada (padrão: temporada atual)")
    p.add_argument("--ate", type=int, help="ano de início da última temporada (padrão: temporada atual)")
    p.add_argument("--temporadas", nargs="+", help="statsbomb: temporadas no formato 2023-2024 (padrão: todas)")
    p.set_defaults(func=cmd_coletar)

    sub.add_parser("importar-legado", help="importa os CSVs da pasta legacy/").set_defaults(func=cmd_importar_legado)
    sub.add_parser("construir", help="monta silver/gold e exporta Parquet").set_defaults(func=cmd_construir)
    p = sub.add_parser("times", help="lista nomes de times sem alias")
    p.add_argument("--todos", action="store_true", help="mostra todos os nomes, não só os suspeitos")
    p.set_defaults(func=cmd_times)
    sub.add_parser("competicoes", help="lista o catálogo").set_defaults(func=cmd_competicoes)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
