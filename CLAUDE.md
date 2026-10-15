# CLAUDE.md: Performance Analyst

Base de dados de futebol (pacote `futstats`) para dashboards de desempenho no Power BI, predição de jogos e modelos estatísticos. Visão geral no `README.md`, fontes em `docs/FONTES.md`, próximos passos em `docs/ROADMAP.md`.

## Comandos

Sempre com o ambiente do projeto ativo (`.venv\Scripts\activate`, prompt com `(.venv)`):

- Testes: `python -m pytest -q` (precisam passar antes de todo commit)
- Catálogo: `python -m futstats competicoes`
- Coleta: `python -m futstats coletar fdcouk|fdorg|statsbomb --comp <IDs> --desde <ano>`
- Legado: `python -m futstats importar-legado`
- Times sem alias: `python -m futstats times`
- Montar a base: `python -m futstats construir` → `data/futstats.duckdb` e `data/gold/*.parquet`

## Regras

- **Fontes de dados:** só as permitidas em `docs/FONTES.md`. Nada de coletar Opta/optaplayerstats, Sofascore, FotMob ou WhoScored, porque os termos proíbem. Fonte nova entra primeiro em `docs/FONTES.md`, com licença e limites.
- **Nunca versionar:** `.env` (tem o `FOOTBALL_DATA_TOKEN`), `.venv/`, `data/`. Confira `git status` antes de commitar; centenas de arquivos novos quase sempre são o `.venv`.
- **`legacy/`** é histórico: só leitura. Não apagar nem reescrever.
- **Times:** casamento entre fontes só por `futstats/seeds/team_aliases.csv`, sem fuzzy matching. Alias novo → rodar os testes (há um teste contra alias ambíguo).
- **Camadas:** coletores em `futstats/sources/` devolvem o esquema de `futstats/schema.py`; regras de negócio de BI ficam em `futstats/sql/gold.sql`. Toda tabela gold nova entra em `TABELAS_GOLD` (`build.py`) e em `docs/POWERBI.md`.
- **Mudança em parser ou SQL** vem com teste em `tests/` usando amostra no formato real da fonte (`tests/fixtures/`).
- **Atribuição:** dados StatsBomb exigem "Data provided by StatsBomb" em qualquer visual publicado.

## Fluxo de trabalho

- Branch por mudança (`feat/...`, `fix/...`, `docs/...`) e PR para `main`; não fazer push direto na `main`.
- Commits e documentação em português.
- O Bruno é analista de dados (Power BI, SQL/Databricks, Python); pode usar termos técnicos de dados sem explicar o básico.
