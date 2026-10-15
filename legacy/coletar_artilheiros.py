import os
import requests
import pandas as pd
import json
import time
from datetime import datetime
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env para o ambiente
load_dotenv()

# Configurações da API football-data.org 
BASE_URL_FD = "https://api.football-data.org/v4"
FD_AUTH_TOKEN = os.getenv("FOOTBALL_DATA_TOKEN")

if not FD_AUTH_TOKEN:
    print("ERRO CRÍTICO: Token FD_AUTH_TOKEN não encontrado no .env ou nas variáveis de ambiente.")
    exit()

HEADERS_FD = {
    "X-Auth-Token": FD_AUTH_TOKEN
}

# Constantes e Configurações do Script 
ANO_INICIAL_COLETA = 2016
PASTA_RAIZ_DADOS = "dados_coletados_football_data_org"
NOME_ENDPOINT_FOLDER = "artilheiros"

# Funções Auxiliares (mesma do script de classificações)
def fazer_requisicao_fd_com_retry(endpoint_path, params=None, extra_headers=None, max_retries=3, base_delay_seconds=6.5):
    url_completa = f"{BASE_URL_FD}{endpoint_path}"
    current_headers = HEADERS_FD.copy()
    if extra_headers:
        current_headers.update(extra_headers)

    print(f"Requisitando: {url_completa} com params: {params}")

    for attempt in range(max_retries):
        try:
            response = requests.get(url_completa, headers=current_headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                delay = base_delay_seconds * (attempt + 2)
                print(f"Erro 429 (Too Many Requests). Aguardando {delay:.1f}s antes de tentar novamente...")
                time.sleep(delay)
            elif e.response.status_code in [403, 404]:
                print(f"Erro HTTP {e.response.status_code} para {url_completa}: {e.response.text[:200]}")
                return None 
            else:
                print(f"Erro HTTP para {url_completa}: {e.response.status_code} - {e.response.text[:200]}")
                if attempt + 1 == max_retries: return None
                time.sleep(base_delay_seconds) # Pausa antes de retentativa para outros erros HTTP
        except requests.exceptions.Timeout:
            print(f"Erro: Timeout. Tentativa {attempt + 1}/{max_retries}")
            if attempt + 1 == max_retries: return None
            time.sleep(base_delay_seconds)
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição para {url_completa}: {e}")
            return None
        except ValueError as e:
            print(f"Erro ao decodificar JSON de {url_completa}: {e}")
            if 'response' in locals(): print(f"Resposta (texto): {response.text[:200]}...")
            return None
    return None

def obter_ano_atual():
    return datetime.now().year

# Função Principal para Coleta de Artilheiros 
def coletar_artilheiros_por_competicao(competition_code, ano_inicio=ANO_INICIAL_COLETA):
    print(f"\n--- Iniciando coleta de ARTILHEIROS para a competição: {competition_code} ---")
    
    pasta_base_competicao = os.path.join(PASTA_RAIZ_DADOS, NOME_ENDPOINT_FOLDER, competition_code)
    os.makedirs(pasta_base_competicao, exist_ok=True)

    ano_fim = obter_ano_atual()

    for ano_temporada in range(ano_inicio, ano_fim + 1):
        print(f"\n  Buscando dados de artilheiros para a temporada (ano de início): {ano_temporada}...")
        
        pasta_ano = os.path.join(pasta_base_competicao, str(ano_temporada))
      

        endpoint_path = f"/competitions/{competition_code}/scorers"
        
        params = {"season": str(ano_temporada), "limit": 200} 

        time.sleep(6.5) 
        dados_api = fazer_requisicao_fd_com_retry(endpoint_path, params=params)

        if dados_api and "scorers" in dados_api and dados_api["scorers"]:
            try:
               
                df_artilheiros = pd.json_normalize(dados_api["scorers"], sep='.')
                
                df_artilheiros['competition_code'] = dados_api.get('competition',{}).get('code', competition_code)
                df_artilheiros['competition_name'] = dados_api.get('competition',{}).get('name')
                df_artilheiros['season_start_year'] = dados_api.get('season',{}).get('startDate')[:4] 
                
                os.makedirs(pasta_ano, exist_ok=True) 
                nome_arquivo = f"artilheiros_{competition_code}_{ano_temporada}.csv"
                caminho_arquivo = os.path.join(pasta_ano, nome_arquivo)
                
                df_artilheiros.to_csv(caminho_arquivo, index=False, encoding='utf-8-sig')
                print(f"    Dados de artilheiros salvos em: {caminho_arquivo}")
            except Exception as e:
                print(f"    Erro ao processar ou salvar dados de artilheiros para {ano_temporada}: {e}")
                print(f"    Dados recebidos (scorers): {json.dumps(dados_api.get('scorers'), indent=2, ensure_ascii=False)[:500]}...")

        elif dados_api is None:
            print(f"    Falha ao obter dados de artilheiros para {competition_code} na temporada {ano_temporada}.")
        else:
            print(f"    Nenhum artilheiro encontrado ou formato de dados inesperado para {competition_code} na temporada {ano_temporada}.")
            if 'message' in dados_api: print(f"    Mensagem da API: {dados_api['message']}")
            
    print(f"\n--- Coleta de artilheiros para {competition_code} finalizada ---")

#Execução Principal
if __name__ == "__main__":
    
    COMPETICOES_ALVO_ARTILHARIA = ["BSA", "MLS", "PPL", "BL1", "DED", "ELC"] 

    print(f"Iniciando script para coletar ARTILHEIROS da API football-data.org.")
    diretorio_base_script = os.path.join(os.getcwd(), PASTA_RAIZ_DADOS, NOME_ENDPOINT_FOLDER)
    print(f"Dados serão salvos em subpastas dentro de: {diretorio_base_script}")

    for codigo_comp in COMPETICOES_ALVO_ARTILHARIA:
        coletar_artilheiros_por_competicao(codigo_comp, ano_inicio=ANO_INICIAL_COLETA)
        if len(COMPETICOES_ALVO_ARTILHARIA) > 1 and codigo_comp != COMPETICOES_ALVO_ARTILHARIA[-1]:
             print(f"Pausa de 10 segundos entre competições...")
             time.sleep(10)

    print("\n--- Processo de coleta de ARTILHEIROS finalizado ---")