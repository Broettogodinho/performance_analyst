import os
import requests
import pandas as pd
import json
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env para o ambiente
load_dotenv()

# --- Configurações da API football-data.org ---
BASE_URL_FD = "https://api.football-data.org/v4"
FD_AUTH_TOKEN = os.getenv("FOOTBALL_DATA_TOKEN")

if not FD_AUTH_TOKEN:
    print("ERRO CRÍTICO: Token FD_AUTH_TOKEN não encontrado no .env ou nas variáveis de ambiente.")
    print("Por favor, configure o token para continuar.")
    exit()

HEADERS_FD_BASE = {
    "X-Auth-Token": FD_AUTH_TOKEN
}

# --- Função para Extrair Colunas do JSON (adaptada para football-data.org) ---
def extrair_colunas_fd_json(json_data, endpoint_path_hint=""):
    """
    Extrai colunas de uma resposta JSON da football-data.org.
    Tenta identificar a lista principal de dados ou usa o objeto diretamente.
    """
    if not json_data:
        return "Resposta JSON vazia ou nula."

    data_para_normalizar = None
    # Chaves comuns que contêm listas de itens na API football-data.org
    list_keys = ['competitions', 'matches', 'standings', 'scorers', 'squad', 'referees', 'bookings', 'goals', 'substitutions', 'seasons', 'teams', 'persons'] # Adicione outras conforme identificar

    # Se a resposta for um dicionário, procuramos por uma chave que contenha uma lista
    if isinstance(json_data, dict):
        found_list = False
        for key in list_keys:
            if key in json_data and isinstance(json_data[key], list) and len(json_data[key]) > 0:
                data_para_normalizar = json_data[key][0] # Pega o primeiro item da lista como amostra
                print(f"  (Analisando o primeiro item da lista encontrada em '{key}')")
                found_list = True
                break
        if not found_list:
            # Se não encontrou uma lista conhecida, ou a lista está vazia, ou é um objeto único
            data_para_normalizar = json_data # Trata o JSON inteiro como um único objeto/amostra
            if any(key in json_data for key in list_keys if isinstance(json_data.get(key), list) and not json_data[key]):
                 print("  (Uma chave de lista conhecida foi encontrada, mas estava vazia. Analisando o objeto principal.)")
            else:
                 print("  (Analisando o objeto JSON principal diretamente - esperado para endpoints de item único)")
                
    # Se a resposta já for uma lista (menos comum como resposta raiz nesta API, mas possível)
    elif isinstance(json_data, list):
        if len(json_data) > 0:
            data_para_normalizar = json_data[0]
            print("  (Analisando o primeiro item da lista JSON principal)")
        else:
            return "Resposta é uma lista JSON vazia."
    else:
        return f"Formato de JSON não esperado: {type(json_data)}"

    if data_para_normalizar is not None:
        try:
            df_normalizado = pd.json_normalize(data_para_normalizar, sep='.') # Usando '.' como separador
            return sorted(df_normalizado.columns.tolist())
        except Exception as e:
            # Fallback para chaves do primeiro nível se a normalização profunda falhar
            if isinstance(data_para_normalizar, dict):
                return f"Erro ao normalizar com Pandas: {e}. Chaves do primeiro nível: {sorted(list(data_para_normalizar.keys()))}"
            return f"Erro ao normalizar com Pandas: {e}, e o dado não é um dicionário para fallback."
    
    return "Não foi possível extrair colunas (amostra de dados estava vazia, nula ou em formato não processável)."

# --- Função para Chamar Endpoint e Mapear ---
def mapear_endpoint_fd(nome_descritivo, path_template, path_params=None, query_params=None, extra_headers=None):
    """
    Chama um endpoint da API football-data.org e imprime as colunas mapeadas.
    """
    print(f"\n--- Mapeando Endpoint: {nome_descritivo} ---")
    
    endpoint_path = path_template
    if path_params:
        try:
            endpoint_path = path_template.format(**path_params)
        except KeyError as e:
            print(f"Erro: Parâmetro de path ausente '{e}' para o template '{path_template}'. Verifique 'path_params'.")
            return {"endpoint": path_template, "nome_descritivo": nome_descritivo, "status": "ERRO_PARAM_PATH", "colunas": []}

    print(f"Path Formatado: {endpoint_path}")
    url_completa = f"{BASE_URL_FD}{endpoint_path}"
    
    current_headers = HEADERS_FD_BASE.copy()
    if extra_headers:
        current_headers.update(extra_headers)

    try:
        response = requests.get(url_completa, headers=current_headers, params=query_params, timeout=20)
        response.raise_for_status()
        
        json_response = response.json()
        colunas = extrair_colunas_fd_json(json_response, endpoint_path_hint=endpoint_path)
        
        print("Colunas encontradas:")
        if isinstance(colunas, list) and colunas:
            for coluna in colunas:
                print(f"  - {coluna}")
        else:
            print(f"  {colunas}") # Mensagem de erro/aviso ou lista vazia
        
        return {"endpoint": endpoint_path, "nome_descritivo": nome_descritivo, "status": "SUCESSO", "colunas": colunas if isinstance(colunas, list) else [colunas]}

    except requests.exceptions.Timeout:
        print(f"Erro: Timeout ao tentar acessar {url_completa}")
        return {"endpoint": endpoint_path, "nome_descritivo": nome_descritivo, "status": "TIMEOUT", "colunas": []}
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        error_text = e.response.text[:200] # Limita o tamanho da mensagem de erro
        print(f"Erro HTTP {status_code} para {url_completa}: {error_text}...")
        return {"endpoint": endpoint_path, "nome_descritivo": nome_descritivo, "status": f"HTTP_ERRO_{status_code}", "colunas": []}
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição para {url_completa}: {e}")
        return {"endpoint": endpoint_path, "nome_descritivo": nome_descritivo, "status": "ERRO_REQUISICAO", "colunas": []}
    except ValueError as e: # Erro ao decodificar JSON
        print(f"Erro ao decodificar JSON da resposta de {url_completa}: {e}")
        if 'response' in locals():
             print(f"Resposta recebida (texto): {response.text[:200]}...")
        return {"endpoint": endpoint_path, "nome_descritivo": nome_descritivo, "status": "ERRO_JSON", "colunas": []}
    except Exception as e:
        print(f"Um erro inesperado ocorreu durante o mapeamento de {url_completa}: {e}")
        return {"endpoint": endpoint_path, "nome_descritivo": nome_descritivo, "status": "ERRO_INESPERADO", "colunas": []}

# --- Lista de Endpoints para Mapear (football-data.org) ---
# BRUNO: Preencha esta lista com os endpoints que você quer mapear.
# Para endpoints que exigem IDs no path (ex: /competitions/{code_or_id}),
# você precisará de um ID de exemplo VÁLIDO em 'path_params'.
# Pode ser necessário fazer uma chamada ao "/competitions" primeiro para obter alguns códigos/IDs.

# IDs de exemplo (substitua por IDs/códigos reais obtidos de chamadas anteriores ou da documentação)
# Códigos de ligas das Américas: BSA (Brasil Série A), MLS (EUA), ASL (Argentina), LMX (México), CLI (Libertadores)
COMPETITION_CODE_EXEMPLO = "BSA"  # Ex: Brasileirão Série A
TEAM_ID_EXEMPLO = 64 # Ex: Liverpool (ID da documentação, pode precisar de um time de liga americana)
PERSON_ID_EXEMPLO = 44 # Ex: Cristiano Ronaldo (ID da documentação, pode precisar de um jogador de liga americana)
MATCH_ID_EXEMPLO = 419384 # ID de uma partida (você precisará obter um ID válido)

ENDPOINTS_PARA_MAPEAR_FD = [
    {
        "nome_descritivo": "Listar Todas Competições", 
        "path_template": "/competitions"
    },
    {
        "nome_descritivo": "Detalhes de uma Competição (ex: Brasileirão)", 
        "path_template": "/competitions/{competition_code_or_id}",
        "path_params": {"competition_code_or_id": COMPETITION_CODE_EXEMPLO}
    },
    {
        "nome_descritivo": "Classificação de uma Competição", 
        "path_template": "/competitions/{competition_code_or_id}/standings",
        "path_params": {"competition_code_or_id": COMPETITION_CODE_EXEMPLO},
        "query_params": {"season": "2023"} # Exemplo, verifique temporadas disponíveis
    },
    {
        "nome_descritivo": "Artilheiros de uma Competição", 
        "path_template": "/competitions/{competition_code_or_id}/scorers",
        "path_params": {"competition_code_or_id": COMPETITION_CODE_EXEMPLO},
        "query_params": {"limit": 3}
    },
    {
        "nome_descritivo": "Partidas de uma Competição (sem detalhes profundos)", 
        "path_template": "/competitions/{competition_code_or_id}/matches",
        "path_params": {"competition_code_or_id": COMPETITION_CODE_EXEMPLO},
        "query_params": {"status": "FINISHED", "limit": 1} # Pega 1 partida finalizada como amostra
    },
    {
        "nome_descritivo": "Partidas de uma Competição (COM detalhes - X-Unfold)", 
        "path_template": "/competitions/{competition_code_or_id}/matches",
        "path_params": {"competition_code_or_id": COMPETITION_CODE_EXEMPLO},
        "query_params": {"status": "FINISHED", "limit": 1},
        "extra_headers": { # Cabeçalhos para "desdobrar" detalhes
            "X-Unfold-Lineups": "true",
            "X-Unfold-Bookings": "true",
            "X-Unfold-Subs": "true",
            "X-Unfold-Goals": "true"
        }
    },
    {
        "nome_descritivo": "Detalhes de uma Partida Específica (COM detalhes - X-Unfold)",
        "path_template": "/matches/{match_id}",
        "path_params": {"match_id": MATCH_ID_EXEMPLO}, # **OBTENHA UM ID DE PARTIDA VÁLIDO**
        "extra_headers": {
            "X-Unfold-Lineups": "true", "X-Unfold-Bookings": "true",
            "X-Unfold-Subs": "true", "X-Unfold-Goals": "true"
        }
    },
    {
        "nome_descritivo": "Detalhes de um Time", 
        "path_template": "/teams/{team_id}",
        "path_params": {"team_id": TEAM_ID_EXEMPLO} # **OBTENHA UM ID DE TIME VÁLIDO**
    },
    {
        "nome_descritivo": "Partidas de uma Pessoa (Jogador) com Agregações Estatísticas", 
        "path_template": "/persons/{person_id}/matches",
        "path_params": {"person_id": PERSON_ID_EXEMPLO}, # **OBTENHA UM ID DE PESSOA VÁLIDO**
        "query_params": {"limit": 5} # Pega 5 partidas como amostra para as agregações
    },
    # Adicione mais endpoints que você quer mapear da documentação
]

# --- Execução Principal ---
if __name__ == "__main__":
    mapeamentos_completos_fd = []
    print("MAPEAMENTO DE COLUNAS DA API football-data.org\n")

    # Mapeia os endpoints configurados
    for ep_config in ENDPOINTS_PARA_MAPEAR_FD:
        resultado = mapear_endpoint_fd(
            nome_descritivo=ep_config["nome_descritivo"],
            path_template=ep_config["path_template"],
            path_params=ep_config.get("path_params"),
            query_params=ep_config.get("query_params"),
            extra_headers=ep_config.get("extra_headers")
        )
        if resultado:
            mapeamentos_completos_fd.append(resultado)
    
    # Opcional: Salvar os resultados em um arquivo JSON
    arquivo_saida_fd = "mapeamento_colunas_football_data_org.json"
    try:
        with open(arquivo_saida_fd, 'w', encoding='utf-8') as f:
            json.dump(mapeamentos_completos_fd, f, indent=2, ensure_ascii=False)
        print(f"\n\nResultados do mapeamento salvos em: {arquivo_saida_fd}")
    except Exception as e:
        print(f"\nErro ao salvar resultados do mapeamento em arquivo: {e}")

    print("\n--- FIM DO MAPEAMENTO (football-data.org) ---")