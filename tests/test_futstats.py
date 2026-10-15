import csv
import json

import duckdb
import pandas as pd
import pytest

from conftest import FIXTURES
from futstats.config import COMPETICOES, SEEDS_DIR, ano_inicio_temporada, rotulo_temporada
from futstats.sources import football_data_couk as fdcouk
from futstats.sources import football_data_org as fdorg
from futstats.storage import consolidar_partidas, gravar_bronze
from futstats.teams import chave, resolver

BRA, ENG = COMPETICOES["BRA1"], COMPETICOES["ENG1"]


# ---------------------------------------------------------------- times
@pytest.mark.parametrize("a,b", [
    ("CA Paranaense", "Athletico-PR"), ("CR Flamengo", "Flamengo RJ"), ("São Paulo FC", "Sao Paulo"),
    ("AC Goianiense", "Atletico GO"), ("Botafogo FR", "Botafogo RJ"), ("SC Recife", "Sport Recife"),
    ("Manchester United FC", "Man United"), ("Nottingham Forest FC", "Nott'm Forest"),
    ("Bayer 04 Leverkusen", "Leverkusen"), ("1. FC Köln", "FC Koln"), ("Paris Saint-Germain FC", "Paris SG"),
    ("Grêmio FBPA", "Gremio"), ("Fluminense FC", "Fluminense"), ("Juventus FC", "Juventus"),
])
def test_variacoes_de_nome_resolvem_para_o_mesmo_time(a, b):
    assert resolver(a)[0] == resolver(b)[0]


@pytest.mark.parametrize("a,b", [("Man City", "Man United"), ("Atletico-MG", "Athletico-PR"),
                                 ("Atletico-MG", "Atletico GO"), ("Inter", "Internacional")])
def test_times_diferentes_nao_se_confundem(a, b):
    assert resolver(a)[0] != resolver(b)[0]


def test_seed_sem_alias_ambiguo():
    vistos = {}
    with (SEEDS_DIR / "team_aliases.csv").open(encoding="utf-8") as fh:
        for linha in csv.DictReader(fh):
            for alias in [linha["nome_exibicao"], *linha["aliases"].split("|")]:
                k = chave(alias)
                assert vistos.setdefault(k, linha["time_id"]) == linha["time_id"], f"'{alias}' em dois times"


def test_rotulos_de_temporada():
    assert rotulo_temporada(ENG, 2024) == "2024-2025" and rotulo_temporada(BRA, 2024) == "2024"
    assert ano_inicio_temporada(ENG, pd.Timestamp("2025-03-01")) == 2024
    assert ano_inicio_temporada(ENG, pd.Timestamp("2025-08-16")) == 2025


# ---------------------------------------------------------------- fontes
def test_fdcouk_formato_principal():
    df = fdcouk.parse((FIXTURES / "fdcouk_E0_2425.csv").read_bytes(), ENG, "2024-2025")
    assert len(df) == 3
    primeiro = df.iloc[0]
    assert (primeiro.mandante_id, primeiro.gols_mandante, primeiro.chutes_alvo_mandante) == ("man-united", 1, 5)
    assert primeiro.odd_mandante == 1.59 and primeiro.odd_fech_mandante == 1.66  # média de mercado / Pinnacle fechamento
    sem_pinnacle = df.iloc[2]
    assert sem_pinnacle.odd_fech_mandante == 2.45  # cai para a média de fechamento
    assert df.iloc[0].data == pd.Timestamp("2024-08-16")


def test_fdcouk_formato_extra():
    df = fdcouk.parse((FIXTURES / "fdcouk_BRA.csv").read_bytes(), BRA)
    assert set(df.temporada) == {"2023", "2024"}
    assert set(df.mandante_id) == {"internacional", "flamengo", "botafogo", "palmeiras"}
    assert df.loc[df.mandante_id == "flamengo", "visitante_id"].item() == "atletico-go"
    assert df.odd_fech_visitante.notna().all()


def test_fdorg_converte_utc_e_rodada():
    dados = json.loads((FIXTURES / "fdorg_BSA_2024.json").read_text(encoding="utf-8"))
    df = fdorg._de_partidas(dados["matches"], BRA, "2024")
    jogo = df[df.mandante_id == "flamengo"].iloc[0]
    assert jogo.data == pd.Timestamp("2024-04-14") and jogo.hora == "00:30"  # UTC: virou o dia
    assert jogo.rodada == 1 and df.iloc[0].arbitro == "Fulano"


# ---------------------------------------------------------------- consolidação
def _partidas_duas_fontes():
    a = fdcouk.parse((FIXTURES / "fdcouk_BRA.csv").read_bytes(), BRA)
    b = fdorg._de_partidas(json.loads((FIXTURES / "fdorg_BSA_2024.json").read_text(encoding="utf-8"))["matches"], BRA, "2024")
    return pd.concat([a, b], ignore_index=True)


def test_consolidacao_casa_fontes_mesmo_com_data_utc_diferente():
    cons = consolidar_partidas(_partidas_duas_fontes())
    assert len(cons) == 4  # 3 jogos de 2024 casados + 1 de 2023 só na fdcouk
    fla = cons[cons.mandante_id == "flamengo"].iloc[0]
    assert fla.fontes == "fdcouk,fdorg"
    assert fla.data == pd.Timestamp("2024-04-13")    # data local (fdcouk), não a UTC
    assert fla.rodada == 1                            # campo que só a fdorg tem
    assert fla.odd_fech_mandante == 1.29              # campo que só a fdcouk tem


def test_jogos_distintos_do_mesmo_confronto_nao_se_fundem():
    df = fdcouk.parse((FIXTURES / "fdcouk_BRA.csv").read_bytes(), BRA)
    volta = df.iloc[[0]].copy()
    volta["data"] = pd.Timestamp("2024-09-01")
    cons = consolidar_partidas(pd.concat([df, volta], ignore_index=True))
    assert len(cons) == len(df) + 1


# ---------------------------------------------------------------- gold
def test_construcao_gold_ponta_a_ponta(base_isolada):
    from futstats.build import construir
    gravar_bronze(_partidas_duas_fontes(), "partidas", ["fonte", "competicao_id", "temporada"])
    contagem = construir()
    assert contagem["fato_partida"] == 4 and contagem["fato_time_partida"] == 8

    con = duckdb.connect(str(base_isolada / "teste.duckdb"), read_only=True)
    lider = con.sql("""SELECT time_id, pontos, jogos FROM gold.classificacao
                       WHERE competicao_id = 'BRA1' AND temporada = '2024' AND posicao = 1 ORDER BY time_id""").fetchall()
    assert all(p == 3 and j == 1 for _, p, j in lider)
    soma = con.sql("""SELECT prob_fech_mandante + prob_fech_empate + prob_fech_visitante FROM gold.fato_partida
                      WHERE odd_fech_mandante IS NOT NULL""").fetchall()
    assert all(abs(s - 1) < 0.001 for (s,) in soma)  # margem da casa removida
    tipos = dict(con.sql("SELECT column_name, column_type FROM (DESCRIBE gold.classificacao)").fetchall())
    assert "HUGEINT" not in tipos.values()
    assert (base_isolada / "gold" / "fato_partida.parquet").exists()
