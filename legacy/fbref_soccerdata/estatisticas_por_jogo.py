import os
import logging
from pathlib import Path
import pandas as pd
from soccerdata import FBref

# Configuração de logging
logging.basicConfig(
    filename="match_stats.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Tradução das colunas
traducao_colunas = {
    ('players_used', ''): 'Jogadores Utilizados',
    ('Age', ''): 'Idade Média',
    ('Poss', ''): 'Posse (%)',
    ('Playing Time', 'MP'): 'Partidas',
    ('Playing Time', 'Starts'): 'Titularidades',
    ('Playing Time', 'Min'): 'Minutos Jogados',
    ('Playing Time', '90s'): 'Jogos (90min)',
    ('Performance', 'Gls'): 'Gols',
    ('Performance', 'Ast'): 'Assistências',
    ('Performance', 'G+A'): 'Gols+Assistências',
    ('Performance', 'G-PK'): 'Gols sem Pênalti',
    ('Performance', 'PK'): 'Pênaltis Convertidos',
    ('Performance', 'PKatt'): 'Pênaltis Tentados',
    ('Performance', 'CrdY'): 'Cartões Amarelos',
    ('Performance', 'CrdR'): 'Cartões Vermelhos',
    ('Expected', 'xG'): 'xG',
    ('Expected', 'npxG'): 'xG (sem pênalti)',
    ('Expected', 'xAG'): 'xAG',
    ('Expected', 'npxG+xAG'): 'npxG+xAG',
    ('Progression', 'PrgC'): 'Conduções Progressivas',
    ('Progression', 'PrgP'): 'Passes Progressivos',
    ('Per 90 Minutes', 'Gls'): 'Gols/90min',
    ('Per 90 Minutes', 'Ast'): 'Assist/90min',
    ('Per 90 Minutes', 'G+A'): 'G+A/90min',
    ('Per 90 Minutes', 'G-PK'): 'Gols SP/90min',
    ('Per 90 Minutes', 'G+A-PK'): 'G+A SP/90min',
    ('Per 90 Minutes', 'xG'): 'xG/90min',
    ('Per 90 Minutes', 'xAG'): 'xAG/90min',
    ('Per 90 Minutes', 'xG+xAG'): 'xG+xAG/90min',
    ('Per 90 Minutes', 'npxG'): 'npxG/90min',
    ('Per 90 Minutes', 'npxG+xAG'): 'npxG+xAG/90min',
    ('url', ''): 'URL'
}

colunas_desejadas = list(traducao_colunas.keys())

# Ligas e temporadas
ligas = [
    'Big 5 European Leagues Combined'
]

temporadas = [
    '2016-2017', '2017-2018', '2018-2019', '2019-2020',
    '2020-2021', '2021-2022', '2022-2023', '2023-2024',
    '2024-2025', '2025-2026', '2026-2027'
]

# Instanciando FBref
fbref = FBref()


# Pasta base
pasta_base = Path("dados_ligas")
pasta_base.mkdir(exist_ok=True)

# Início da coleta
for liga in ligas:
    print(f"\n Iniciando coleta para a liga: {liga}")
    pasta_liga = pasta_base / liga
    pasta_liga.mkdir(parents=True, exist_ok=True)

    for temporada in temporadas:
        try:
            print(f" Temporada: {temporada}")
            fbref = FBref(leagues=liga, seasons=temporada)
            df = fbref.read_team_season_stats(stat_type='standard')



            # Verificar quais colunas estão disponíveis
            colunas_validas = [col for col in colunas_desejadas if col in df.columns]

            if not colunas_validas:
                raise ValueError("Nenhuma das colunas desejadas está disponível.")

            df_filtrado = df[colunas_validas]
            df_filtrado.columns = [traducao_colunas[col] for col in colunas_validas]

            # Salvar CSV
            caminho_arquivo = pasta_liga / f"{temporada}.csv"
            df_filtrado.to_csv(caminho_arquivo, index=False, encoding="utf-8-sig")
            print(f"  Dados salvos em: {caminho_arquivo}")

        except Exception as e:
            msg = f"Erro ao coletar dados da temporada {temporada} da liga {liga}: {e}"
            print(f"  {msg}")
            logging.error(msg)

print("\n Coleta finalizada para todas as ligas.")
