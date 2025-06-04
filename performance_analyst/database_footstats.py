import os
import pandas as pd
import json
from dotenv import load_dotenv

#carrega variaveis de autenticaçao
load_dotenv()

#configuraçao da api FOOTBALL-DATA(FD)
BASE_URL_FD = "https://api.football-data.org/v4"
FD_AUTH_TOKEN = os.getenv("FOOTBALL_DATA_TOKEN")

if not FD_AUTH_TOKEN:
    print("Erro critico, Token não encontrado")
    print("Por favor configure o token")
    exit()

HEADERS_FD_BASE = {
    "X-Auth-Token": FD_AUTH_TOKEN
}

#funçao para extrair colunas do JSON
