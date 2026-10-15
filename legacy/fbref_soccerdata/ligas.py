from soccerdata import FBref
import os
import pandas as pd

#parametros
anos = list(range(2010, 2027))
ligas = [
    "ENG-Premier League",
    "ESP-La Liga",
    "FRA-Ligue 1",
    "GER-Bundesliga",
    "ITA-Serie A"
]

output_dir = "dados_ligas"
os.makedirs(output_dir, exist_ok=True)

for liga_id in ligas:
    for ano in anos:
        temporada = f"{ano}-{str(ano+1)[-2:]}"
        try:
            print(f"Baixando dados gerais da liga{liga_id} - temporada {temporada}")
            fbref = FBref(leagues=[liga_id], seasons=[temporada])

            #lista de infos
            df_leagues = fbref.read_leagues()
            df_seasons = fbref.read_seasons()
            df_team_season = fbref.read_team_season_stats(stat_type="standard")
            df_team_match = fbref.read_team_match_stats(stat_type="schedule")
            df_player_season = fbref.read_player_season_stats(stat_type="standard")
            df_schedule = fbref.read_schedule()

            #salva arquivos csv por df 
            base_name = f"{liga_id.replace(' ','_').replace('-','_')}_{temporada}"

            df_leagues.to_csv(os.path.join(output_dir,f"{base_name}_leagues.csv"), index=False, encoding='utf-8-sig')
            df_seasons.to_csv(os.path.join(output_dir, f"{base_name}_seasons.csv"),index=False, encoding='utf-8-sig')
            df_team_season.to_csv(os.path.join(output_dir, f"{base_name}_team_season.csv"),index=False, encoding='utf-8-sig')
            df_team_match.to_csv(os.path.join(output_dir, f"{base_name}_team_match.csv"),index=False, encoding='utf-8-sig')
            df_player_season.to_csv(os.path.join(output_dir, f"{base_name}_player_season.csv"),index=False, encoding='utf-8-sig')
            df_schedule.to_csv(os.path.join(output_dir, f"{base_name}_schedule.csv"),index=False, encoding='utf-8-sig')

            print(f"Dados salvos para {liga_id} - {temporada}")

        except Exception as e:
            print(f"Erro ao baixar dados da {liga_id} -{temporada}: {e: }")
            