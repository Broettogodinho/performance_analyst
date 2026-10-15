# Fontes de dados

Levantamento feito em outubro/2026. O critério é usar só fontes que permitem uso pessoal e de pesquisa, sem violar termos de uso.

## Em uso

| Fonte | Conteúdo | Cobertura | Acesso | Condições |
|---|---|---|---|---|
| **football-data.co.uk** | Resultados, chutes, escanteios, faltas, cartões, árbitro e odds (abertura e fechamento) | Big 5, Championship, Portugal, Holanda (desde os anos 1990); Brasil, Argentina e MLS no formato "extra" (desde ~2012) | CSV gratuito, sem cadastro | Citar a fonte |
| **football-data.org** | Partidas com id, rodada, fase e árbitro; artilharia | Plano grátis: Brasileirão, Champions, Big 5, Eredivisie, Primeira Liga, Championship, Copa, Euro | API com token gratuito (10 req/min) | Libertadores exige plano pago |
| **StatsBomb Open Data** | Eventos lance a lance com xG, posição de cada chute, jogada, pressão | Temporadas selecionadas: Copas do Mundo, Euros, La Liga (era Messi), Bundesliga 2023-24 (jogos do Leverkusen), Champions (finais), MLS 2023 e outras | GitHub, gratuito | Atribuição obrigatória: "Data provided by StatsBomb" + logo |
| **Legado FBref** (`legacy/`) | ~210 métricas avançadas por time, incluindo xG, PSxG e progressão | Big 5, 2016-17 a 2024-25 | Já coletado | Não é mais atualizável (ver abaixo) |

## Avaliadas e não usadas

**Opta (optaplayerstats.statsperform.com)**
- Não há API nem exportação. A página é uma vitrine de placares e estatísticas carregadas por JavaScript.
- Os termos da Stats Perform limitam o conteúdo a uso pessoal e não comercial. Reprodução, republicação ou uso em outros ambientes exigem consentimento por escrito, e o rodapé proíbe uso comercial ou distribuição.
- A Opta está fiscalizando ativamente: em **20/01/2026** encerrou o feed avançado do FBref e exigiu a exclusão dos dados.
- **Conclusão:** dados da Opta só com licença comercial direta da Stats Perform.

**FBref (estatísticas avançadas)**
- Desde jan/2026 o FBref só publica estatísticas básicas.
- A biblioteca `soccerdata`, usada na versão anterior deste projeto, segue útil para dados básicos, mas não traz mais xG nem métricas avançadas do FBref.

**Sofascore, FotMob, WhoScored**
- Têm xG e muitas estatísticas, mas não oferecem API pública e os termos proíbem coleta automatizada. Ficam fora.

## Pagas, para considerar no futuro

- **API-Football**: grátis com 100 requisições/dia e temporadas limitadas; Pro a US$ 19/mês com 7.500/dia e todas as ligas. Traz escalações, eventos, estatísticas por jogador e lesões. É o caminho natural para dados de **jogadores** do Brasileirão e da Libertadores.
- **Sportmonks** e **Stats Perform/Opta**: comerciais, para quando o projeto virar produto.
