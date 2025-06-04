import os
from soccerdata import FBref

ligas = ["Big 5 European Leagues Combined"]
temporadas = [
    "2016-2017", "2017-2018", "2018-2019",
    "2019-2020", "2020-2021", "2021-2022",
    "2022-2023", "2023-2024"
]
stat_types = [
    "keeper", "keeper_adv", "shooting", "passing",
    "passing_types", "goal_shot_creation", "defense",
    "possession", "playing_time", "misc"
]

fbref = FBref(leagues=ligas, seasons=temporadas)

base_path = "dados_jogadores"

for liga in ligas:
    for temporada in temporadas:
        for stat_type in stat_types:
            try:
                print(f"Coletando {stat_type} - {liga} {temporada} ...")
                df = fbref.read_player_season_stats(stat_type=stat_type)
                # Filtra por liga e temporada, se as colunas existirem
                if "league" in df.columns and "season" in df.columns:
                    df = df[(df["league"] == liga) & (df["season"] == temporada)]
                else:
                    print(f"Aviso: colunas 'league' ou 'season' não encontradas para {stat_type} {temporada}")
                
                # Salva os dados
                pasta = os.path.join(base_path, liga, temporada)
                os.makedirs(pasta, exist_ok=True)
                arquivo = os.path.join(pasta, f"{stat_type}.csv")
                df.to_csv(arquivo, index=False)
                print(f"Salvo em {arquivo}")

            except Exception as e:
                print(f"Erro ao coletar {stat_type} - {liga} {temporada}: {e}")
