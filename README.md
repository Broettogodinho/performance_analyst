# ⚽ Performance Analyst

[![testes](https://github.com/Broettogodinho/performance_analyst/actions/workflows/tests.yml/badge.svg)](https://github.com/Broettogodinho/performance_analyst/actions/workflows/tests.yml)

Base de dados de futebol para **dashboards de desempenho**, **predição de jogos** e outros **modelos estatísticos**. Cobre Brasileirão, Big 5 europeias, Champions, Libertadores e outras ligas, usando só fontes gratuitas e permitidas.

```
football-data.co.uk ─┐
football-data.org ───┼─► bronze (Parquet) ─► silver (partidas consolidadas) ─► gold (DuckDB + Parquet) ─► Power BI / modelos
StatsBomb Open Data ─┤
legado FBref ────────┘
```

## O que já existe (Fase 1)

- **Coleta** de três fontes gratuitas e importação dos dados antigos do projeto. Detalhes e licenças em [`docs/FONTES.md`](docs/FONTES.md).
- **Times casados entre fontes:** "CA Paranaense", "Athletico-PR" e "Athletico Paranaense" viram o mesmo `athletico-pr`. Isso vale por regras de normalização e por uma tabela de apelidos editável. Não há casamento "aproximado": o que não casar aparece num relatório para revisão.
- **Partidas consolidadas:** cada jogo vira uma linha, combinando o melhor de cada fonte (rodada da football-data.org, odds da football-data.co.uk, xG da StatsBomb).
- **Modelo estrela** pronto para BI:
  - classificação;
  - forma nos últimos 5 jogos;
  - pontos acumulados;
  - aproveitamento em casa e fora;
  - probabilidades do mercado sem a margem da casa;
  - **pontos esperados pelo mercado**, que diz se o time está acima ou abaixo do que as odds previam.
- **Métricas avançadas do FBref** (xG, PSxG, passes progressivos…) da Big 5 de 2016-17 a 2024-25, preservadas do legado.
- **Guia do Power BI**, com relacionamentos, medidas DAX e layout das páginas: [`docs/POWERBI.md`](docs/POWERBI.md).

Próximas fases (predição com Elo e Dixon-Coles, xG próprio, simulação de temporada) em [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Instalação

```bash
git clone https://github.com/Broettogodinho/performance_analyst.git
cd performance_analyst
python -m venv .venv
.venv\Scripts\activate            # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env            # e cole seu token da football-data.org  (Linux/macOS: cp)
```

## Carga inicial

```bash
python -m futstats importar-legado                                         # dados já coletados (legacy/)
python -m futstats coletar fdcouk --desde 2015                             # resultados + odds, todas as ligas do catálogo
python -m futstats coletar fdorg --comp BRA1 UCL ENG1 ESP1 --desde 2023    # rodada/fase (plano grátis: ~3 temporadas)
python -m futstats coletar statsbomb --comp GER1 ESP1 WC EURO              # eventos e xG das temporadas abertas
python -m futstats times                                                   # revisar nomes que não casaram
python -m futstats construir                                               # monta data/futstats.duckdb e data/gold/*.parquet
```

Para atualizar durante a temporada, basta rodar de novo sem `--desde`: coleta só a temporada atual e reconstrói. Recoletar é idempotente, porque substitui a partição em vez de duplicar.

Outros comandos:
- `python -m futstats competicoes` lista o catálogo e as fontes de cada competição.
- `python -m futstats times --todos` mostra todos os nomes e como foram resolvidos.

### Times que não casaram

Se `futstats times` listar um nome, por exemplo "Botafogo-SP" da fonte A que deveria ser o mesmo time de outra fonte, adicione uma linha ou um apelido em [`futstats/seeds/team_aliases.csv`](futstats/seeds/team_aliases.csv):

```csv
time_id,nome_exibicao,pais,aliases
botafogo-sp,Botafogo-SP,Brasil,Botafogo SP|Botafogo FC SP
```

Depois rode `construir` de novo. Há um teste que impede o mesmo apelido de apontar para dois times.

## Consultas rápidas (DuckDB)

```python
import duckdb
con = duckdb.connect("data/futstats.duckdb", read_only=True)
con.sql("""
    SELECT posicao, t.nome_exibicao, jogos, pontos, aproveitamento_pct, pontos_esperados_mercado
    FROM gold.classificacao c JOIN gold.dim_time t USING (time_id)
    WHERE competicao_id = 'BRA1' AND temporada = '2024'
    ORDER BY posicao
""").show()
```

## Estrutura

```
futstats/
├── config.py          # caminhos e catálogo de competições (ids por fonte)
├── teams.py           # normalização de nomes de times
├── schema.py          # esquema padrão de partidas
├── http.py            # downloads com cache, retentativa e pausa
├── storage.py         # bronze (Parquet particionado) e consolidação (silver)
├── build.py           # monta gold no DuckDB e exporta Parquet
├── sources/           # football_data_couk, football_data_org, statsbomb, legacy
├── sql/gold.sql       # modelo estrela
└── seeds/team_aliases.csv
docs/                  # FONTES, POWERBI, ROADMAP
legacy/                # código e dados da versão anterior (ver legacy/README.md)
tests/                 # pytest com amostras de cada fonte
data/                  # gerado localmente (não versionado)
```

## Testes

```bash
pytest -q
```

## Créditos e licenças de dados

- Resultados e odds: [football-data.co.uk](https://www.football-data.co.uk)
- Partidas: [football-data.org](https://www.football-data.org)
- Eventos e xG: **Data provided by [StatsBomb](https://github.com/statsbomb/open-data)**. A atribuição é obrigatória em qualquer publicação.
- Legado: FBref / Sports Reference (dados coletados antes de jan/2026)

## Autor

**Bruno Broetto Godinho** · [GitHub](https://github.com/Broettogodinho) · [LinkedIn](https://www.linkedin.com/in/bruno-broetto-godinho/)

Licença: Apache 2.0 (código). Os dados seguem as condições de cada fonte.
