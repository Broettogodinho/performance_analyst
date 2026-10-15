-- Camada gold: modelo estrela para o Power BI e para os modelos estatísticos.
-- Executado por futstats.build com as views de entrada já criadas:
--   silver_partidas, bronze_chutes (pode estar vazia), bronze_fbref_times (pode estar vazia),
--   dim_competicao, dim_time.

CREATE SCHEMA IF NOT EXISTS gold;

-- ---------------------------------------------------------------------------
-- Partidas: uma linha por jogo
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE gold.fato_partida AS
WITH base AS (
    SELECT *,
           1 / odd_mandante + 1 / odd_empate + 1 / odd_visitante                AS _overround,
           1 / odd_fech_mandante + 1 / odd_fech_empate + 1 / odd_fech_visitante AS _overround_fech
    FROM silver_partidas
)
SELECT
    partida_id, competicao_id, temporada, competicao_id || '|' || temporada AS competicao_temporada,
    CAST(data AS DATE) AS data, hora, rodada, fase,
    mandante_id, visitante_id, mandante_nome, visitante_nome,
    gols_mandante, gols_visitante, gols_mandante_1t, gols_visitante_1t,
    gols_mandante + gols_visitante AS total_gols,
    CASE WHEN gols_mandante > gols_visitante THEN 'M'
         WHEN gols_mandante < gols_visitante THEN 'V'
         WHEN gols_mandante IS NOT NULL THEN 'E' END AS resultado,
    gols_mandante > 0 AND gols_visitante > 0 AS ambos_marcam,
    chutes_mandante, chutes_visitante, chutes_alvo_mandante, chutes_alvo_visitante,
    escanteios_mandante, escanteios_visitante, faltas_mandante, faltas_visitante,
    amarelos_mandante, amarelos_visitante, vermelhos_mandante, vermelhos_visitante,
    xg_mandante, xg_visitante, arbitro,
    odd_mandante, odd_empate, odd_visitante,
    odd_fech_mandante, odd_fech_empate, odd_fech_visitante,
    -- Probabilidades implícitas sem a margem da casa (normalização proporcional).
    ROUND((1 / odd_mandante) / _overround, 4)  AS prob_mercado_mandante,
    ROUND((1 / odd_empate) / _overround, 4)    AS prob_mercado_empate,
    ROUND((1 / odd_visitante) / _overround, 4) AS prob_mercado_visitante,
    ROUND((1 / odd_fech_mandante) / _overround_fech, 4)  AS prob_fech_mandante,
    ROUND((1 / odd_fech_empate) / _overround_fech, 4)    AS prob_fech_empate,
    ROUND((1 / odd_fech_visitante) / _overround_fech, 4) AS prob_fech_visitante,
    ROUND(_overround - 1, 4) AS margem_casa,
    fontes
FROM base;

-- ---------------------------------------------------------------------------
-- Time × partida: duas linhas por jogo (visão de cada time), com acumulados
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE gold.fato_time_partida AS
WITH lados AS (
    SELECT partida_id, competicao_id, temporada, competicao_temporada, data, rodada, fase,
           mandante_id AS time_id, visitante_id AS adversario_id, 'Casa' AS mando,
           gols_mandante AS gols_pro, gols_visitante AS gols_contra,
           xg_mandante AS xg_pro, xg_visitante AS xg_contra,
           chutes_mandante AS chutes_pro, chutes_visitante AS chutes_contra,
           chutes_alvo_mandante AS chutes_alvo_pro, chutes_alvo_visitante AS chutes_alvo_contra,
           escanteios_mandante AS escanteios_pro, escanteios_visitante AS escanteios_contra,
           amarelos_mandante AS amarelos, vermelhos_mandante AS vermelhos,
           prob_fech_mandante AS prob_vitoria_mercado, prob_fech_empate AS prob_empate_mercado
    FROM gold.fato_partida
    UNION ALL
    SELECT partida_id, competicao_id, temporada, competicao_temporada, data, rodada, fase,
           visitante_id, mandante_id, 'Fora',
           gols_visitante, gols_mandante, xg_visitante, xg_mandante,
           chutes_visitante, chutes_mandante, chutes_alvo_visitante, chutes_alvo_mandante,
           escanteios_visitante, escanteios_mandante, amarelos_visitante, vermelhos_visitante,
           prob_fech_visitante, prob_fech_empate
    FROM gold.fato_partida
),
com_resultado AS (
    SELECT *,
           CASE WHEN gols_pro > gols_contra THEN 'V' WHEN gols_pro < gols_contra THEN 'D'
                WHEN gols_pro IS NOT NULL THEN 'E' END AS resultado,
           CASE WHEN gols_pro > gols_contra THEN 3 WHEN gols_pro = gols_contra THEN 1
                WHEN gols_pro IS NOT NULL THEN 0 END AS pontos,
           gols_contra = 0 AS jogo_sem_sofrer,
           ROUND(3 * prob_vitoria_mercado + prob_empate_mercado, 3) AS pontos_esperados_mercado
    FROM lados
)
SELECT *,
       ROW_NUMBER() OVER w_temp                                   AS jogo_n,
       CAST(SUM(pontos) OVER w_temp AS INTEGER)                   AS pontos_acum,
       CAST(SUM(gols_pro - gols_contra) OVER w_temp AS INTEGER)    AS saldo_acum,
       CAST(SUM(pontos) OVER (w_temp ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS INTEGER) AS pontos_ult5,
       STRING_AGG(resultado, '') OVER (w_temp ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS forma_ult5,
       AVG(gols_pro) OVER (w_temp ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS media_gols_pro_ult5,
       AVG(gols_contra) OVER (w_temp ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS media_gols_contra_ult5
FROM com_resultado
WINDOW w_temp AS (PARTITION BY competicao_id, temporada, time_id ORDER BY data, partida_id);

-- ---------------------------------------------------------------------------
-- Classificação por competição e temporada (critérios: pontos, vitórias, saldo, gols pró)
-- Em copas, soma todas as fases; use a coluna `fase` em fato_time_partida para recortes.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE gold.classificacao AS
WITH agg AS (
    SELECT competicao_id, temporada, competicao_temporada, time_id,
           COUNT(*) FILTER (WHERE pontos IS NOT NULL)     AS jogos,
           COUNT(*) FILTER (WHERE resultado = 'V')       AS vitorias,
           COUNT(*) FILTER (WHERE resultado = 'E')       AS empates,
           COUNT(*) FILTER (WHERE resultado = 'D')       AS derrotas,
           CAST(SUM(gols_pro) AS INTEGER)                AS gols_pro,
           CAST(SUM(gols_contra) AS INTEGER)             AS gols_contra,
           CAST(SUM(gols_pro) - SUM(gols_contra) AS INTEGER) AS saldo,
           CAST(SUM(pontos) AS INTEGER)                  AS pontos,
           CAST(SUM(pontos) FILTER (WHERE mando = 'Casa') AS INTEGER) AS pontos_casa,
           CAST(SUM(pontos) FILTER (WHERE mando = 'Fora') AS INTEGER) AS pontos_fora,
           COUNT(*) FILTER (WHERE jogo_sem_sofrer)       AS jogos_sem_sofrer,
           SUM(xg_pro)                                   AS xg_pro,
           SUM(xg_contra)                                AS xg_contra,
           COUNT(xg_pro)                                 AS jogos_com_xg,
           ROUND(SUM(pontos_esperados_mercado), 1)       AS pontos_esperados_mercado,
           COUNT(pontos_esperados_mercado)               AS jogos_com_odds
    FROM gold.fato_time_partida
    GROUP BY ALL
)
SELECT RANK() OVER (PARTITION BY competicao_id, temporada
                    ORDER BY pontos DESC, vitorias DESC, saldo DESC, gols_pro DESC) AS posicao,
       *,
       ROUND(100.0 * pontos / NULLIF(3 * jogos, 0), 1) AS aproveitamento_pct,
       ROUND(gols_pro / NULLIF(jogos, 0), 2)            AS gols_pro_por_jogo,
       ROUND(gols_contra / NULLIF(jogos, 0), 2)         AS gols_contra_por_jogo
FROM agg;

-- ---------------------------------------------------------------------------
-- Chutes (StatsBomb): base para mapas de chute e modelo de xG próprio
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE gold.fato_chute AS
SELECT * FROM bronze_chutes;

-- ---------------------------------------------------------------------------
-- FBref (legado, Big 5 2016-17 a 2024-25): formato longo + resumo largo com as métricas-chave
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE gold.fbref_time_temporada AS
SELECT * FROM bronze_fbref_times;

CREATE OR REPLACE TABLE gold.fbref_resumo AS
SELECT competicao_id, temporada, competicao_id || '|' || temporada AS competicao_temporada,
       time_id, any_value(time_nome) AS time_nome,
       MAX(valor) FILTER (WHERE tabela = 'estatisticas_padrao' AND metrica = 'Poss')                    AS posse_pct,
       MAX(valor) FILTER (WHERE tabela = 'estatisticas_padrao' AND metrica = 'Playing Time | MP')       AS jogos,
       MAX(valor) FILTER (WHERE tabela = 'estatisticas_padrao' AND metrica = 'Performance | Gls')       AS gols,
       MAX(valor) FILTER (WHERE tabela = 'estatisticas_padrao' AND metrica = 'Performance | Ast')       AS assistencias,
       MAX(valor) FILTER (WHERE tabela = 'estatisticas_padrao' AND metrica = 'Expected | xG')           AS xg,
       MAX(valor) FILTER (WHERE tabela = 'estatisticas_padrao' AND metrica = 'Expected | npxG')         AS npxg,
       MAX(valor) FILTER (WHERE tabela = 'estatisticas_padrao' AND metrica = 'Expected | xAG')          AS xag,
       MAX(valor) FILTER (WHERE tabela = 'estatisticas_padrao' AND metrica = 'Progression | PrgC')      AS conducoes_progressivas,
       MAX(valor) FILTER (WHERE tabela = 'estatisticas_padrao' AND metrica = 'Progression | PrgP')      AS passes_progressivos,
       MAX(valor) FILTER (WHERE tabela = 'chutes' AND metrica = 'Standard | Sh')                        AS chutes,
       MAX(valor) FILTER (WHERE tabela = 'chutes' AND metrica = 'Standard | SoT')                       AS chutes_no_alvo,
       MAX(valor) FILTER (WHERE tabela = 'chutes' AND metrica = 'Standard | Dist')                      AS distancia_media_chute,
       MAX(valor) FILTER (WHERE tabela = 'passes' AND metrica = 'Total | Cmp%')                         AS passes_certos_pct,
       MAX(valor) FILTER (WHERE tabela = 'defesa' AND metrica = 'Tackles | Tkl')                        AS desarmes,
       MAX(valor) FILTER (WHERE tabela = 'defesa' AND metrica = 'Int')                                  AS interceptacoes,
       MAX(valor) FILTER (WHERE tabela = 'goleiro' AND metrica = 'Performance | GA')                    AS gols_sofridos,
       MAX(valor) FILTER (WHERE tabela = 'goleiro' AND metrica = 'Performance | Save%')                 AS defesas_goleiro_pct,
       MAX(valor) FILTER (WHERE tabela = 'goleiro' AND metrica = 'Performance | CS')                    AS jogos_sem_sofrer,
       MAX(valor) FILTER (WHERE tabela = 'goleiro_avancado' AND metrica = 'Expected | PSxG')            AS psxg_contra
FROM gold.fbref_time_temporada
GROUP BY competicao_id, temporada, time_id;

-- ---------------------------------------------------------------------------
-- Dimensões
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE gold.dim_competicao AS SELECT * FROM dim_competicao;
CREATE OR REPLACE TABLE gold.dim_time AS SELECT * FROM dim_time;

CREATE OR REPLACE TABLE gold.dim_temporada AS
SELECT DISTINCT competicao_id, temporada,
       CAST(LEFT(temporada, 4) AS INTEGER) AS ano_inicio,
       competicao_id || '|' || temporada  AS competicao_temporada
FROM gold.fato_partida;

CREATE OR REPLACE TABLE gold.dim_data AS
SELECT CAST(d AS DATE) AS data, YEAR(d) AS ano, MONTH(d) AS mes, strftime(d, '%Y-%m') AS ano_mes,
       ISODOW(d) AS dia_semana_n,
       ['Seg','Ter','Qua','Qui','Sex','Sáb','Dom'][ISODOW(d)] AS dia_semana
FROM range((SELECT MIN(data) FROM gold.fato_partida), (SELECT MAX(data) FROM gold.fato_partida) + INTERVAL 1 DAY, INTERVAL 1 DAY) t(d);
