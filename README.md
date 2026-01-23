# Algorithmic Trading Ecosystem

Bem-vindo ao ecossistema de trading quantitativo. Este repositório centraliza o fluxo completo de desenvolvimento de estratégias, desde a pesquisa inicial até a execução em tempo real.

## Configuração Rápida

1.  **Instale as dependências:**

    ```bash
    pip install -r requirements.txt
    ```

2.  **MetaTrader 5 (Essencial para o LiveBot):**
    - Certifique-se de ter o **MetaTrader 5** instalado e aberto.
    - **IMPORTANTE:** Você deve estar logado na **sua conta da corretora** (Demo ou Real) no terminal MT5. O robô utiliza a conta ativa no terminal para puxar dados e executar ordens. Sem isso, ele não funcionará.
    - Habilite o "Algo Trading" no terminal.

O projeto é dividido em dois módulos principais, cada um com um propósito específico no ciclo de vida do trading algorítmico:

---

## Diferenças Principais (Resumo)

| Característica     | **Backtest_Project** (O Laboratório)                | **Live_Bot_MT5** (O Executor)                        |
| :----------------- | :-------------------------------------------------- | :--------------------------------------------------- |
| **Objetivo**       | Pesquisa, Validação e "Stress Test" de estratégias. | Monitoramento em Tempo Real e Execução de Ordens.    |
| **Fonte de Dados** | **Yahoo Finance** (Foco em dados Diários/Semanais). | **MetaTrader 5** (Dados Intraday, M1, M5, Tick).     |
| **Ambiente**       | Offline / Estático (Analisa o passado).             | Online / Dinâmico (Reage ao mercado agora).          |
| **Foco Visual**    | Gráficos estatísticos, Curvas de Equity, Heatmaps.  | Dashboard Operacional, Glassmorphism, Latência Zero. |
| **Uso Principal**  | _"Essa ideia funciona nos últimos 10 anos?"_        | _"O mercado está dando sinal agora? Executar!"_      |

---

## 1. Backtest_Project (Research)

Esta é a área de **Pesquisa e Desenvolvimento (R&D)**. Aqui focamos na robustez matemática das estratégias.

### Funcionalidades

- **Dados Históricos Longos**: Análise de décadas de dados via `yfinance`.
- **Métricas Avançadas**: Cálculo automático de Sharpe Ratio, Sortino, Max Drawdown, CAGR.
- **Comparação de Benchmark**: Estratégia vs Buy & Hold.
- **Portfólio**: Otimização e correlação de múltiplos ativos.
- **Standalone Notebooks**: Notebooks Jupyter isolados para testes rápidos e prototipagem.

### Como Usar

Focado em **python puro** e bibliotecas de data science (`pandas`, `numpy`, `scipy`).

```powershell
cd Backtest_Project/backend
# Certifique-se de estar com o venv ativo
python api.py
# Acesse http://localhost:5000
```

---

## 2. Live_Bot_MT5 (Production)

Esta é a área de **Produção**. Uma aplicação moderna conectada diretamente ao terminal MetaTrader 5 para operar no mercado brasileiro (B3) e Forex.

### Funcionalidades

- **Conexão Nativa MT5**: Baixa latência usando a biblioteca `MetaTrader5` oficial.
- **Design Premium**: Interface **Glassmorphism** moderna (Dark Mode) para facilitar a leitura visual durante o pregão.
- **Backtest Intraday**: Motor de backtest adaptado para dados de alta frequência (M1/M5) para validar a micro-estrutura do mercado.
- **Scanner de Mercado**: Monitoramento de múltiplos ativos simultaneamente.
- **Controle Total**: Painel visual para iniciar/pausar robôs e ajustar parâmetros em tempo real.

### Requisitos Críticos

- O terminal **MetaTrader 5** deve estar aberto e logado na máquina Windows.
- A configuração **"Algo Trading"** deve estar habilitada no terminal.

### Como Usar

```powershell
cd Live_Bot_MT5
# O MT5 deve estar rodando!
python app.py
# Acesse http://localhost:5002
```

---

## Configuração do Ambiente

Para garantir que ambos os projetos funcionem, utilizamos um ambiente virtual compartilhado ou dedicado.

1. **Criar Ambiente Virtual**:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

2. **Instalar Dependências**:
   ```powershell
   # Instala pacotes para ambos os projetos (Pandas, Flask, MetaTrader5, Yfinance)
   pip install -r requirements.txt
   ```

---

### Desenvolvedor

Desenvolvido por **Eurico Júnior**.
_Focado na convergência entre Data Science e Trading Executivo._
