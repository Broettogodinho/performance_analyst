# Análise de Dados de Desempenho de Futebol com `soccerdata` e Power BI

## Descrição
Este projeto tem como objetivo geral coletar, organizar e analisar dados completos de desempenho de times e jogadores das principais ligas de futebol (principalmente europeias) dos últimos anos, utilizando a biblioteca `soccerdata`. Os dados são preparados para análises e visualizações aprofundadas no Power BI, incluindo dados históricos, estatísticas por partidas e temporadas, para dar suporte a análises avançadas e geração de insights.

## Funcionalidades Principais
* **Coleta Abrangente de Dados:** Utiliza a biblioteca `soccerdata` para extrair informações de fontes como FBRef e SoFIFA.
* **Dados Históricos e Atuais:** Coleta de estatísticas de times e jogadores desde a temporada 2010-2011 até as mais recentes (2025-2026, conforme o plano).
* **Granularidade dos Dados:** Aquisição de dados em nível de temporada e por partida, tanto para times quanto para jogadores.
* **Armazenamento Organizado:** Os dados coletados são salvos localmente em formato CSV, estruturados por ano, liga e time para fácil acesso.
* **Preparação para BI:** Os dados são processados e padronizados para importação e modelagem no Power BI.
* **Visualização Interativa:** Desenvolvimento de relatórios e dashboards no Power BI para análise de desempenho, com filtros por temporada, liga e diversas métricas.
* **Automação (Planejado):** Implementação de scripts para coleta e atualização periódica e automatizada dos dados.

## Fontes de Dados
A principal fonte de dados para este projeto é a biblioteca Python **`soccerdata`**, que facilita o acesso a dados de futebol de sites populares:
* **FBRef:** Fornece estatísticas detalhadas de partidas, temporadas, times e jogadores.
* **SoFIFA:** Oferece dados sobre atributos de jogadores, classificações de times e informações de versões do jogo FIFA.

O foco da coleta são as principais ligas europeias, incluindo a "Big 5 European Leagues Combined".

## Tecnologias Utilizadas
* **Python 3.x**
* **`soccerdata`**: Biblioteca central para coleta de dados.
* **Pandas**: Para manipulação e análise dos DataFrames retornados pela `soccerdata`.
* **CSV**: Formato de arquivo para armazenamento local dos dados coletados.
* **Power BI**: Para modelagem de dados, criação de relatórios e dashboards interativos.
* (Opcional, adicione outras bibliotecas que você usa, ex: `requests`, `json`, etc.)

## Como Usar / Executar

### Pré-requisitos
* Python 3.8+
* pip (gerenciador de pacotes Python)
* Git (para clonar o repositório)
* Power BI Desktop (para visualizar e editar os relatórios)

### Instalação
1.  Clone o repositório:
    ```bash
    git clone [https://github.com/Broettogodinho/performance_analyst.git](https://github.com/Broettogodinho/performance_analyst.git)
    cd PROJETO-ANALISE-DE-DADOS-DE-DESEMPENHO # Ou o nome da pasta raiz do seu projeto
    ```
2.  Crie e ative um ambiente virtual (recomendado):
    ```bash
    python -m venv .venv
    ```
    * No Windows:
        ```bash
        .venv\Scripts\activate
        ```
    * No Linux/macOS:
        ```bash
        source .venv/bin/activate
        ```
3.  Instale as dependências:
    *(Bruno, é altamente recomendável criar um arquivo `requirements.txt` com as bibliotecas Python que você usa, como `soccerdata`, `pandas`, etc. Você pode gerá-lo com `pip freeze > requirements.txt` após instalar tudo no seu ambiente virtual).*
    ```bash
    pip install -r requirements.txt
    ```
    Se você ainda não tem um `requirements.txt`, no mínimo instale a `soccerdata`:
    ```bash
    pip install soccerdata pandas
    ```

### Executando as Coletas e Análises
1.  **Scripts de Coleta:**
    * Execute os scripts localizados na pasta `performance_analyst/scripts_coleta/` (ou onde você os colocou) para popular a pasta `performance_analyst/dados_coletados/`.
    * Exemplo (adapte aos nomes dos seus scripts):
        ```bash
        python performance_analyst/scripts_coleta/coletar_dados_times.py
        python performance_analyst/scripts_coleta/coletar_dados_jogadores.py
        ```
2.  **Power BI:**
    * Abra o Power BI Desktop.
    * Importe os dados dos arquivos CSV gerados.
    * Desenvolva ou abra os relatórios e dashboards para análise. (Consulte o "Guia rápido para atualização dos dados e relatórios" mencionado nos seus entregáveis da Sprint 4).

## Plano de Sprints (Resumo)

* **Sprint 1: Preparação do ambiente e levantamento dos dados disponíveis**
    * Configurar Python e `soccerdata`, explorar métodos da biblioteca, testar coletas básicas.
* **Sprint 2: Coleta e armazenamento dos dados históricos por temporada**
    * Coletar dados por temporada (2010-2026) das principais ligas, salvar em CSVs organizados.
* **Sprint 3: Ampliação da coleta para estatísticas individuais e análises avançadas**
    * Coletar dados detalhados de jogadores, integrar diferentes fontes, padronizar dados.
* **Sprint 4: Preparação e integração dos dados no Power BI**
    * Criar ETLs para Power BI, construir modelos de dados, desenvolver relatórios e dashboards.
* **Sprint 5: Sazonalidade, automatização e monitoramento**
    * Desenvolver catálogo sazonal, automatizar coleta e atualização, monitorar qualidade dos dados.

## Contribuindo
Contribuições são bem-vindas! Sinta-se à vontade para abrir *Issues* para reportar bugs, sugerir melhorias ou discutir novas funcionalidades. Pull Requests também são apreciados.

## Autor
* **Bruno Broetto Godinho**
* GitHub: [@Broettogodinho](https://github.com/Broettogodinho)
* https://www.linkedin.com/in/bruno-broetto-godinho/

## Licença
Este projeto está licenciado sob os termos da **Apache License, Version 2.0**.

Para ver o texto completo da licença, consulte o arquivo [LICENSE] neste repositório.