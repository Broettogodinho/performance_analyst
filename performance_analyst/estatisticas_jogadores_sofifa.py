import os
import pandas as pd
from soccerdata import SoFIFA

# 1. Coletar as últimas 100 versões
print("🔍 Buscando últimas versões do SoFIFA...")
sofifa = SoFIFA(versions="all")
df_versions = sofifa.read_versions().reset_index()
df_versions["update"] = pd.to_datetime(df_versions["update"], errors="coerce")
df_versions = df_versions[df_versions["update"].notna()]
ultimas_100 = df_versions.sort_values("update").tail(100)
lista_versions = ultimas_100["version_id"].tolist()

# 2. Reinstanciar com as 100 últimas versões
print("📥 Coletando dados de jogadores das últimas 100 versões...")
sofifa = SoFIFA(versions=lista_versions)
df_jogadores = sofifa.read_players()

# 3. Criar pasta principal
output_dir = "data_sofifa_jogadores"
os.makedirs(output_dir, exist_ok=True)

# 4. Verificar se coluna de nacionalidade existe
if "nationality_name" not in df_jogadores.columns:
    raise KeyError("A coluna 'nationality_name' não foi encontrada no DataFrame.")

# 5. Separar e salvar por nacionalidade
print("💾 Salvando dados por nacionalidade...")
for nacionalidade, df_nac in df_jogadores.groupby("nationality_name"):
    nome_pasta = os.path.join(output_dir, nacionalidade.replace(" ", "_"))
    os.makedirs(nome_pasta, exist_ok=True)

    caminho_arquivo = os.path.join(nome_pasta, f"jogadores_{nacionalidade.replace(' ', '_')}.csv")
    df_nac.to_csv(caminho_arquivo, index=False)

print("✅ Finalizado! Dados salvos em: data_sofifa_jogadores/")
