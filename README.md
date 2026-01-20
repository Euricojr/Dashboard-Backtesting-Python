# Portfolio de Estratégias & Trading System

Bem-vindo ao repositório centralizado de estratégias quantitativas e trading bots. Este repositório foi reestruturado para hospedar dois projetos distintos, facilitando a organização entre desenvolvimento de estratégias (Backtest) e execução/monitoramento em tempo real (Live).

## 📂 Estrutura do Repositório

O projeto está dividido em duas pastas principais:

1.  **`Backtest_Project`**: Dashboard de Análise e Backtest de Dados Históricos.
2.  **`Live_Bot_MT5`**: Sistema de Trading em Tempo Real conectado ao MetaTrader 5.

---

## 🚀 1. Backtest Project (Análise Histórica)

Uma plataforma web robusta para testar ideias de trading usando dados históricos do Yahoo Finance.

### Funcionalidades

- **Estratégias**: Cruzamento de Médias (SMA) e RSI Semanal.
- **Visualização**: Gráficos interativos com TradingView Lightweight Charts.
- **Métricas**: Sharpe Ratio, Drawdown, CAGR, Win Rate.
- **IA Analysis**: Insights gerados por IA sobre a qualidade do backtest.
- **Multi-Ativos**: Ações BR, Stocks EUA, Cripto e Índices.

### Como Rodar

```powershell
# 1. Entre na pasta
cd Backtest_Project/backend

# 2. Ative o ambiente virtual (se ainda não estiver ativo)
# ..\..\.venv\Scripts\activate

# 3. Execute o servidor
python api.py
```

> Acesse: `http://localhost:5000`

---

## 📈 2. Live Bot MT5 (Tempo Real)

Uma aplicação conectada diretamente ao terminal MetaTrader 5 (MT5) para monitoramento de mercado e execução de ordens em tempo real.

### Funcionalidades

- **Conexão Direta**: Integração via API Python nativa do MetaTrader5.
- **Gráficos Live**: Plota candles recebidos diretamente do terminal.
- **Seletores Dinâmicos**: Escolha de Timeframe (M1, M5, H1...) e Qtde de Velas.
- **Scanner de Ativos**: Scripts para mapear todos os ativos disponíveis na corretora (Ações e Futuros).
- **Foco**: Otimizado para Mini Índice (WIN) e Mini Dólar (WDO), mas compatível com toda a B3.

### Pré-requisitos

- **MetaTrader 5**: O terminal precisa estar instalado e rodando em sua máquina Windows.
- **Conta**: Logada (Demo ou Real) e com "Algo Trading" habilitado nas configurações.

### Como Rodar

```powershell
# 1. Entre na pasta
cd Live_Bot_MT5

# 2. Execute o app
python app.py
```

> Acesse: `http://localhost:5002`

---

## 🛠️ Ferramentas Úteis

### Listar Ativos do MT5

Dentro de `Live_Bot_MT5/scripts`, existe um utilitário para mapear sua corretora.

```powershell
python Live_Bot_MT5/scripts/listar_ativos.py
```

Isso gera um CSV em `Live_Bot_MT5/data/` com todos os símbolos disponíveis.

---

## 📦 Instalação Geral

Se esta é a primeira vez rodando o projeto:

1. **Crie o ambiente virtual**:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```
2. **Instale as dependências**:
   ```powershell
   pip install -r requirements.txt
   ```
   _(Certifique-se de que o `MetaTrader5` está no requirements.txt)_

---

Desenvolvido por **Eurico Júnior**.
