# Legado

Código e dados da primeira versão do projeto, mantidos para histórico e importados pela nova base com `python -m futstats importar-legado`.

| Pasta | Situação |
|---|---|
| `dados_football_data_org/partidas_competicao` | ✅ Importado: partidas 2023-2025 de BSA, BL1, DED, PPL e ELC |
| `dados_football_data_org/artilheiros` | Mantido; ainda não usado |
| `fbref_soccerdata/dados_times` | ✅ Importado: ~210 métricas avançadas por time, Big 5, 2016-17 a 2024-25 |
| `fbref_soccerdata/raw_data` | Usado para identificar a liga de cada time (cache HTML do FBref) |
| `fbref_soccerdata/Big 5 European Leagues Combined` | ⚠️ Não importável: os CSVs de jogadores foram salvos sem as colunas de jogador, time e temporada (eram o índice do DataFrame e se perderam no `to_csv(index=False)`) |
| `fbref_soccerdata/dados_ligas` | Mantido; coberto por `dados_times` |
| `*.py`, `requirements_soccerdata.txt` | Scripts antigos (soccerdata/FBref e football-data.org); substituídos pelo pacote `futstats` |

Desde 20/01/2026 o FBref não publica mais as estatísticas avançadas da Opta, por isso esses dados não podem ser recoletados. Veja `docs/FONTES.md`.
