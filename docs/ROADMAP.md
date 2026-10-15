# Roadmap

O projeto avança em fases curtas. Cada fase termina com algo utilizável e testado.

## ✅ Fase 1: Base de dados (este PR)
- Pacote `futstats` com CLI: coleta de football-data.co.uk, football-data.org e StatsBomb.
- Importação do legado (FBref 2016-25 e football-data.org 2023-25).
- Normalização de nomes de times entre fontes (`seeds/team_aliases.csv`) com relatório de nomes não casados.
- Consolidação de partidas entre fontes (mesmo jogo = mesma competição, temporada e confronto, com até 2 dias de diferença).
- DuckDB + Parquet. Modelo estrela gold: classificação, forma, acumulados, odds sem margem, pontos esperados pelo mercado.
- Guia do Power BI com relacionamentos, medidas DAX e layout.

## Fase 1b: Dashboard de desempenho
- Rodar a carga histórica completa na máquina local (seção "Carga inicial" do README).
- Revisar o relatório `futstats times` e completar os aliases.
- Montar o `.pbix` seguindo `docs/POWERBI.md`.

## Fase 2: Qualidade e automação
- Validações automáticas: jogos por rodada, placares nulos, times novos sem alias, temporadas incompletas.
- Atualização agendada com GitHub Actions ou Agendador de Tarefas, coletando só a temporada atual.
- Tabela de classificação **rodada a rodada** (posição em cada data), para o gráfico de "corrida pelo título".

## Fase 3: Predição de jogos
- **Elo** por time, com vantagem de mando calibrada por liga.
- **Poisson / Dixon-Coles**: força de ataque e defesa → probabilidade de cada placar → 1X2, over/under, ambos marcam.
- Backtest temporal (treina até a rodada N, prevê a N+1), avaliado por log-loss e Brier score **contra as odds de fechamento**. O mercado é o benchmark a bater.
- Tabela `gold.predicoes` e página de predições no Power BI.

## Fase 4: Modelos avançados
- Modelo de **xG próprio** treinado nos chutes da StatsBomb (regressão logística ou gradient boosting com distância, ângulo, parte do corpo e tipo de jogada).
- Simulação de Monte Carlo da temporada: probabilidade de título, Libertadores e rebaixamento.
- Dados de **jogadores** (API-Football, se valer o custo) com rating por posição e minutos.

## Fora de escopo
- Coleta de sites cujos termos proíbem (Opta, Sofascore, FotMob, WhoScored). Ver `docs/FONTES.md`.
