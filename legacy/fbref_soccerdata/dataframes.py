from soccerdata import FBref
import pandas as pd

liga = "Big 5 European Leagues Combined"
temporada = "2022-2023"

fbref = FBref(leagues=[liga], seasons=[temporada])

# Pegar dados de jogadores por partida 
df_players = fbref.read_player_match_stats()

print(df_players.columns)
print(df_players.head())


