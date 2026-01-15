# Dashboard Quantitativo

Uma plataforma web profissional para backtesting de estratégias de investimento quantitativo. Desenvolvida com **Python (Flask)** no backend e **Tabler UI** no frontend, oferecendo uma interface premium e responsiva.

## Funcionalidades

- **Backtesting de Estratégias**:
  - **Médias Móveis (SMA)**: Estratégia clássica de cruzamento de médias (curta vs longa).
  - **RSI Semanal (IFR)**: Estratégia de reversão à média utilizando o Índice de Força Relativa em timeframe semanal (Compra < 35, Venda > 70).
- **Dashboard Premium**: Interface moderna e escura (Dark Mode) construída com o framework Tabler.
- **Gráficos Interativos**: Visualização avançada de preços e performance usando _Lightweight Charts_ (TradingView).
  - Candles, Linhas de SMA/RSI, Marcadores de Compra/Venda.
  - Curva de Patrimônio vs Buy & Hold.
- **Métricas Financeiras**: Cálculo automático de Retorno Total, CAGR, Sharpe Ratio e Drawdown.
- **Análise com IA**: Geração de insights simulados sobre a performance da estratégia e alertas de risco (Overfitting).
- **Command Palette**: Busca rápida de ativos via teclado (`Ctrl+K`).
- **Multimercado**: Suporte a Ações BR, Stocks EUA, Criptomoedas e Índices Globais.

## Tecnologias

- **Backend**: Python 3, Flask, Pandas, NumPy, YFinance.
- **Frontend**: HTML5, JavaScript (ES6+), Tabler (CSS Framework), Lightweight Charts.
- **Dados**: Yahoo Finance (via biblioteca `yfinance`).

## Instalação e Execução

### Pré-requisitos

- Python 3.8 ou superior instalado.

### Passo a Passo

1.  **Clone o repositório** (ou baixe os arquivos):

    ```bash
    git clone https://github.com/Euricojr/Dashboard-Backtesting-Python.git
    cd Dashboard-Backtesting-Python
    ```

2.  **Crie e ative um ambiente virtual (Recomendado)**:

    ```bash
    # Windows
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1

    # Linux/Mac
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Instale as dependências**:

    ```bash
    pip install -r requirements.txt
    ```

4.  **Execute o Servidor Backend**:

    ```bash
    python backend/api.py
    ```

    _O servidor iniciará em `http://localhost:5000`._

5.  **Acesse o Dashboard**:
    - Abra o arquivo `frontend/index.html` diretamente no seu navegador.
    - **OU** use uma extensão como "Live Server" no VS Code para servir a pasta `frontend`.

## Estrutura do Projeto

```
/
├── backend/
│   └── api.py          # API Flask (Servidor)
├── frontend/
│   ├── index.html      # Interface do Usuário (Tabler UI)
│   └── script.js       # Lógica do Frontend (Gráficos, Fetch)
├── backtest.py         # Lógica Core do Backtest e Indicadores
├── requirements.txt    # Dependências do Python
└── README.md           # Documentação
```

## Como Usar

1.  Abra o Dashboard no navegador.
2.  Use a barra lateral (ou `Ctrl+K`) para selecionar um ativo (ex: PETR4.SA, AAPL, BTC-USD).
3.  Defina o período de **Início** e **Fim**.
4.  Selecione a **Estratégia**:
    - **SMA**: Configure as médias Curta e Longa.
    - **RSI**: Utiliza parâmetros fixos (Semanal, Sobrevenda 35, Sobrecompra 70).
5.  Clique em **"Executar Backtest"**.
6.  Analise os resultados nos gráficos e cards de métricas.

---

Desenvolvido por **Eurico Júnior**.
