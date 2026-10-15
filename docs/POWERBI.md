# Power BI: conexão, modelo e dashboard de desempenho

## 1. Conectar

Depois de `python -m futstats construir`, os arquivos ficam em `data/gold/*.parquet`.

1. **Obter dados → Parquet**, um arquivo por tabela. Para várias de uma vez, use **Obter dados → Pasta**, aponte para `data/gold` e filtre por `.parquet`.
2. Para atualizar, rode `construir` de novo e clique em **Atualizar** no Power BI. O caminho não muda.

> Dica: crie um parâmetro `PastaGold` com o caminho da pasta e use-o nas consultas. Assim o `.pbix` funciona em outra máquina trocando só o parâmetro.

## 2. Tabelas

| Tabela | Grão | Uso |
|---|---|---|
| `dim_competicao` | competição | nome, país, tipo (liga/copa) |
| `dim_time` | time | nome de exibição, país |
| `dim_temporada` | competição × temporada | chave `competicao_temporada` |
| `dim_data` | dia | ano, mês, dia da semana |
| `fato_partida` | jogo | placar, estatísticas, odds e probabilidades do mercado |
| `fato_time_partida` | time × jogo (2 linhas por jogo) | **base do dashboard**: pontos, gols, xG, forma, acumulados |
| `classificacao` | time × temporada | tabela pronta com posição e aproveitamento |
| `fbref_resumo` | time × temporada (Big 5, 2016-25) | métricas avançadas: xG, posse, passes progressivos, PSxG |
| `fbref_time_temporada` | time × temporada × métrica | as ~210 métricas do FBref em formato longo |
| `fato_chute` | chute (StatsBomb) | mapas de chute e xG por jogador |

## 3. Relacionamentos (todos 1:N, filtro em direção única)

```
dim_time[time_id]                    → fato_time_partida[time_id]
dim_time[time_id]                    → classificacao[time_id]
dim_time[time_id]                    → fbref_resumo[time_id]
dim_competicao[competicao_id]        → dim_temporada[competicao_id]
dim_temporada[competicao_temporada]  → fato_time_partida[competicao_temporada]
dim_temporada[competicao_temporada]  → classificacao[competicao_temporada]
dim_temporada[competicao_temporada]  → fato_partida[competicao_temporada]
dim_temporada[competicao_temporada]  → fbref_resumo[competicao_temporada]
dim_data[data]                       → fato_time_partida[data]
dim_data[data]                       → fato_partida[data]
```

Use `fato_time_partida` para tudo que é "do ponto de vista do time". `fato_partida` serve para visões do jogo, como mandante × visitante, total de gols e odds.

Os slicers de **Competição** e **Temporada** devem vir de `dim_competicao[nome]` e `dim_temporada[temporada]`.

## 4. Medidas DAX

Crie uma tabela vazia `_Medidas` e cole:

```dax
Jogos = COUNTROWS ( fato_time_partida )
Pontos = SUM ( fato_time_partida[pontos] )
Aproveitamento % = DIVIDE ( [Pontos], 3 * [Jogos] )
Vitórias = CALCULATE ( [Jogos], fato_time_partida[resultado] = "V" )
Empates = CALCULATE ( [Jogos], fato_time_partida[resultado] = "E" )
Derrotas = CALCULATE ( [Jogos], fato_time_partida[resultado] = "D" )

Gols Pró = SUM ( fato_time_partida[gols_pro] )
Gols Contra = SUM ( fato_time_partida[gols_contra] )
Saldo = [Gols Pró] - [Gols Contra]
Gols Pró por Jogo = DIVIDE ( [Gols Pró], [Jogos] )
Gols Contra por Jogo = DIVIDE ( [Gols Contra], [Jogos] )
Jogos sem Sofrer % = DIVIDE ( CALCULATE ( [Jogos], fato_time_partida[jogo_sem_sofrer] = TRUE () ), [Jogos] )

Aproveitamento Casa % = CALCULATE ( [Aproveitamento %], fato_time_partida[mando] = "Casa" )
Aproveitamento Fora % = CALCULATE ( [Aproveitamento %], fato_time_partida[mando] = "Fora" )

-- Finalização (onde a fonte traz chutes)
Chutes por Jogo = DIVIDE ( SUM ( fato_time_partida[chutes_pro] ), [Jogos] )
Precisão de Chute % = DIVIDE ( SUM ( fato_time_partida[chutes_alvo_pro] ), SUM ( fato_time_partida[chutes_pro] ) )
Conversão (Gols / Chute no Alvo) = DIVIDE ( [Gols Pró], SUM ( fato_time_partida[chutes_alvo_pro] ) )

-- xG (StatsBomb / FBref)
xG Pró = SUM ( fato_time_partida[xg_pro] )
xG Contra = SUM ( fato_time_partida[xg_contra] )
Gols - xG = [Gols Pró] - [xG Pró]

-- Desempenho vs. expectativa do mercado (odds de fechamento sem margem)
Pontos Esperados (Mercado) = SUM ( fato_time_partida[pontos_esperados_mercado] )
Pontos acima do Esperado =
    VAR JogosComOdds = CALCULATE ( [Jogos], NOT ISBLANK ( fato_time_partida[pontos_esperados_mercado] ) )
    VAR PontosComOdds = CALCULATE ( [Pontos], NOT ISBLANK ( fato_time_partida[pontos_esperados_mercado] ) )
    RETURN IF ( JogosComOdds > 0, PontosComOdds - [Pontos Esperados (Mercado)] )

-- Forma
Forma Últimos 5 =
    VAR UltimoJogo = MAX ( fato_time_partida[jogo_n] )
    RETURN CALCULATE ( MAX ( fato_time_partida[forma_ult5] ), fato_time_partida[jogo_n] = UltimoJogo )
Pontos Últimos 5 =
    VAR UltimoJogo = MAX ( fato_time_partida[jogo_n] )
    RETURN CALCULATE ( SUM ( fato_time_partida[pontos] ), fato_time_partida[jogo_n] > UltimoJogo - 5 )
```

> "Pontos acima do Esperado" positivo significa que o time somou mais pontos do que as odds indicavam: superou a expectativa do mercado. É um bom indicador de "sorte × qualidade" e a base para os modelos de predição da Fase 3.

## 5. Layout sugerido do dashboard

**Página 1: Liga**
- Slicers: Competição, Temporada.
- Tabela `classificacao`: posição, time, J, V, E, D, GP, GC, SG, Pts e Aproveitamento %, com formatação condicional nas zonas.
- Cartões: gols por jogo da liga, % vitórias do mandante, % empates, % ambos marcam (de `fato_partida`).
- Gráfico de linhas: `pontos_acum` × `jogo_n` por time (os 4 primeiros ou os times selecionados).

**Página 2: Time**
- Slicer: Time.
- Cartões: Pontos, Aproveitamento %, Gols Pró/Contra por Jogo, Forma Últimos 5, Pontos acima do Esperado.
- Colunas: Aproveitamento Casa × Fora.
- Linha: média móvel de gols pró e contra nos últimos 5 jogos (`media_gols_pro_ult5`, `media_gols_contra_ult5`) por data.
- Tabela de jogos: data, adversário, mando, placar, resultado, probabilidade de vitória pelo mercado.

**Página 3: Big 5 avançado (FBref 2016-25)**
- Dispersão: `xg` × `gols` por time-temporada, com a linha de referência y = x. Acima da linha, o time finalizou acima do esperado.
- Dispersão: `posse_pct` × pontos (join com `classificacao` quando houver as duas fontes).
- Ranking: passes progressivos e conduções progressivas.

**Página 4: Chutes (StatsBomb)**
- Dispersão sobre a imagem de um campo (x de 0 a 120, y de 0 a 80), com tamanho = xG e cor = gol/não gol.
- Inclua "Data provided by StatsBomb" e o logo na página. É exigência da licença.
