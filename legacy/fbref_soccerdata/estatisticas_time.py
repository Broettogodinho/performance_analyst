import os
import pandas as pd
from soccerdata import FBref

#  Parâmetros
ligas = ["Big 5 European Leagues Combined"]
temporadas = [
    "2016-2017", "2017-2018", "2018-2019", "2019-2020", "2020-2021",
    "2021-2022", "2022-2023", "2023-2024", "2024-2025", "2025-2026"
]
estatisticas = {
    "standard": "estatisticas_padrao",
    "passing": "passes",
    "passing_types": "tipos_de_passes",
    "goal_shot_creation": "criacao_de_gols_chutes",
    "defense": "defesa",
    "possession": "posse_de_bola",
    "playing_time": "tempo_de_jogo",
    "misc": "diversos",
    "shooting": "chutes",
    "keeper": "goleiro",
    "keeper_adv": "goleiro_avancado"
}

#  Pasta de saída
base_path = "dados_times"

#  Loop pelas ligas e temporadas
for liga in ligas:
    for temporada in temporadas:
        print(f"\n Temporada: {temporada}")
        fbref = FBref(leagues=[liga], seasons=[temporada])
        
        for tipo, nome_arquivo in estatisticas.items():
            try:
                print(f" Coletando {tipo}...")
                df = fbref.read_team_season_stats(stat_type=tipo)
                
                #  Cria pasta da temporada
                caminho_pasta = os.path.join(base_path, liga, temporada)
                os.makedirs(caminho_pasta, exist_ok=True)

                #  Salva CSV
                caminho_arquivo = os.path.join(caminho_pasta, f"{nome_arquivo}.csv")
                df.to_csv(caminho_arquivo, index=False)
                print(f" Salvo: {caminho_arquivo}")
            
            except Exception as e:
                print(f" Erro ao coletar {tipo} - {liga} {temporada}: {e}")
