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

HEADERS_FD_BASE = {
    "X-Auth-Token": FD_AUTH_TOKEN
}

# Constantes e Configurações do Script 
ANO_INICIAL_COLETA = 2022
PASTA_RAIZ_DADOS = "dados_coletados_football_data_org"
NOME_ENDPOINT_FOLDER = "partidas_competicao"

# Funções Auxiliares (mesma do script anterior) 
def fazer_requisicao_fd_com_retry(endpoint_path, params=None, extra_headers=None, max_retries=3, base_delay_seconds=6.5):
    url_completa = f"{BASE_URL_FD}{endpoint_path}"
    current_headers = HEADERS_FD_BASE.copy()
    if extra_headers:
        current_headers.update(extra_headers)

    print(f"Requisitando: {url_completa} com params: {params}")
    # print(f"Cabeçalhos: {current_headers}") # Para depuração dos X-Unfold

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
                time.sleep(base_delay_seconds)
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

# Função Principal para Coleta de Partidas de Competição 
def coletar_partidas_por_competicao(competition_code, ano_inicio=ANO_INICIAL_COLETA):
    print(f"\n--- Iniciando coleta de PARTIDAS para a competição: {competition_code} ---")
    
    pasta_base_competicao = os.path.join(PASTA_RAIZ_DADOS, NOME_ENDPOINT_FOLDER, competition_code)
    os.makedirs(pasta_base_competicao, exist_ok=True)

    ano_fim = obter_ano_atual()

    # Cabeçalhos para solicitar todos os detalhes "desdobrados" (unfolded)
    headers_com_unfold = {
        "X-Unfold-Lineups": "true",
        "X-Unfold-Bookings": "true",
        "X-Unfold-Subs": "true",
        "X-Unfold-Goals": "true"
    }

    for ano_temporada in range(ano_inicio, ano_fim + 1):
        print(f"\n  Buscando dados de partidas para a temporada (ano de início): {ano_temporada}...")
        
        pasta_ano = os.path.join(pasta_base_competicao, str(ano_temporada))
       

        endpoint_path = f"/competitions/{competition_code}/matches"
        params = {
            "season": str(ano_temporada),
            "status": "FINISHED" 
            # "limit": 50 # A API pode ter um limite padrão baixo por página, verifique a necessidade de paginação ou um limite maior
        }

        time.sleep(6.5) # Pausa proativa
        dados_api = fazer_requisicao_fd_com_retry(endpoint_path, params=params, extra_headers=headers_com_unfold)

        if dados_api and "matches" in dados_api and dados_api["matches"]:
            try:
                
                
                lista_partidas_para_df = []
                for partida_json in dados_api["matches"]:
                    
                    partida_normalizada = pd.json_normalize(partida_json, sep='_')
                    
                    # Remove colunas que são listas de objetos para evitar problemas na linha principal do CSV
                   
                    colunas_de_lista = ['goals', 'bookings', 'substitutions', 
                                        'homeTeam_lineup', 'homeTeam_bench', 
                                        'awayTeam_lineup', 'awayTeam_bench', 'referees']
                    for col_lista in colunas_de_lista:
                        if col_lista in partida_normalizada.columns:
                            partida_normalizada = partida_normalizada.drop(columns=[col_lista])
                    
                    if not partida_normalizada.empty:
                        lista_partidas_para_df.append(partida_normalizada.iloc[0]) #

                if lista_partidas_para_df:
                    df_partidas = pd.DataFrame(lista_partidas_para_df)
                    
                    
                    df_partidas['competition_id_api'] = dados_api.get('competition', {}).get('id')
                    df_partidas['competition_code_api'] = dados_api.get('competition', {}).get('code')
                    df_partidas['competition_name_api'] = dados_api.get('competition', {}).get('name')
                   
                    df_partidas['season_filter_year'] = ano_temporada 
                    
                    os.makedirs(pasta_ano, exist_ok=True) 
                    nome_arquivo = f"partidas_{competition_code}_{ano_temporada}.csv"
                    caminho_arquivo = os.path.join(pasta_ano, nome_arquivo)
                    
                    df_partidas.to_csv(caminho_arquivo, index=False, encoding='utf-8-sig')
                    print(f"    Dados de {len(df_partidas)} partidas salvos em: {caminho_arquivo}")
                else:
                    print(f"    Nenhuma partida processada para {competition_code} na temporada {ano_temporada} após normalização.")

            except Exception as e:
                print(f"    Erro ao processar ou salvar dados de partidas para {ano_temporada}: {e}")
                print(f"    Dados recebidos (matches): {json.dumps(dados_api.get('matches'), indent=2, ensure_ascii=False)[:500]}...")

        elif dados_api is None:
            print(f"    Falha ao obter dados de partidas para {competition_code} na temporada {ano_temporada}.")
        else:
            print(f"    Nenhuma partida encontrada ou formato de dados inesperado para {competition_code} na temporada {ano_temporada}.")
            if 'message' in dados_api: print(f"    Mensagem da API: {dados_api['message']}")
            
    print(f"\n--- Coleta de partidas para {competition_code} finalizada ---")

# Execução Principal
if __name__ == "__main__":
    
    COMPETICOES_ALVO_PARTIDAS = ["BSA", "PPL", "BL1", "DED", "ELC"] 

    print(f"Iniciando script para coletar PARTIDAS DE COMPETIÇÃO da API football-data.org.")
    diretorio_base_script = os.path.join(os.getcwd(), PASTA_RAIZ_DADOS, NOME_ENDPOINT_FOLDER)
    print(f"Dados serão salvos em subpastas dentro de: {diretorio_base_script}")

    for codigo_comp in COMPETICOES_ALVO_PARTIDAS:
        coletar_partidas_por_competicao(codigo_comp, ano_inicio=ANO_INICIAL_COLETA)
        if len(COMPETICOES_ALVO_PARTIDAS) > 1 and codigo_comp != COMPETICOES_ALVO_PARTIDAS[-1]:
             print(f"Pausa de 10 segundos entre competições...")
             time.sleep(10)

    print("\n--- Processo de coleta de PARTIDAS DE COMPETIÇÃO finalizado ---")