# 🚀 FinSense: Plataforma Estratégica de Trading Automatizado

Bem-vindo ao **FinSense**, um ecossistema completo e avançado de trading quantitativo desenvolvido em Python. A plataforma centraliza todo o fluxo de desenvolvimento de estratégias de investimento, desde a pesquisa, backtesting, e escaneamento do mercado (B3 e Forex), até a execução automatizada em tempo real (Algo Trading) no MetaTrader 5, com direito a monitoramento e alertas na palma da mão via Telegram.

---

## 🌟 Funcionalidades Principais

- **📊 Dashboards Interativos (Web):** Interfaces modernas com design _Glassmorphism_, animações _hover 3D_ e atualizações em tempo real (WebSockets / Polling).
- **📈 Análise Técnica em Tempo Real:** Cálculo e plotagem dinâmica de indicadores diretamente no gráfico, como as Médias Móveis Simples (SMAs).
- **🔬 Motor de Backtesting e Análise Fundamentalista:** Ferramentas para validar se uma estratégia funcionou nos últimos anos, checando Métricas de Risco (Profit Factor, Win Rate, Drawdown) e dados de valuation.
- **🤖 Execução Automática no MetaTrader 5:** Envio e gerenciamento de ordens automatizadas no mercado (B3/Forex).
- **⚡ Scanner Elite Integrado:** Um script de inteligência de mercado (`scanner_elite.py`) que varre o histórico de mais de 120 ativos da B3 (via `yfinance` em timeframes como 1h ou Diário) buscando configurações otimizadas de cruzamento de médias, selecionando automaticamente os ativos mais lucrativos.
- **📱 Monitoramento e Controle Avançado via Telegram Bot:** Receba alertas de oportunidades, status consolidado e o novo *Resumo Diário* em JSON diretamente no celular. Interaja de forma bidirecional com o robô via **Botões Inline** (ex: Ligar/Desligar Scalper WIN, visualizar Estatísticas), trabalhando em sincronia perfeita com o painel de controle do Dashboard Web.
- **📱 Responsividade e Mobile-First:** Gráficos de Candlestick inteligentes que calibram a visibilidade de velas estritamente pela dimensão da tela (reduzindo carga visual no celular) de forma dinâmica.
- **✨ Interface e UX Refinados:** Design otimizado no painel de controle do Scalper WIN (espaçamentos, glassmorphism e cores) e nova Landing Page enriquecida com copywriting de conversão e atalho vetorizado direto para o `@AlertaOperacoes_bot`.
- **📈 Estabilidade e Alta Precisão:** Algoritmo revisado de cálculo de *Winrate*, e arquitetura "Thread-Safe" que protege o Core da plataforma contra quedas (`RuntimeError: main thread not in main loop`), garantindo operação ininterrupta, inclusive nos momentos de mercado fechado.

---

## 🏗 Arquitetura do Projeto

O FinSense é dividido em módulos principais, cada um com um propósito específico no ciclo de vida do seu capital algorítmico:

| Módulo / Ferramenta  | Objetivo Principal                                        | Fonte de Dados                            | Ambiente            | Foco Principal                                              |
| :------------------- | :-------------------------------------------------------- | :---------------------------------------- | :------------------ | :---------------------------------------------------------- |
| **Backtest_Project** | Laboratório: Pesquisa, Validação e Avaliação da robustez. | Yahoo Finance (Histórico Diário/Semanal). | Offline / Estático  | _"Esta ideia de trade é lucrativa no longo prazo?"_         |
| **App (Dashboard)**  | Monitoramento visual, histórico, botões Telegram.         | MetaTrader 5 (Tick, H1, etc).             | Web (Localhost 5002)| _"Ligar/Desligar robôs pelo Telegram, ver carteira."_       |
| **Scalper WIN**      | Motor Autônomo (Background) de scalping de Índice/B3.     | MetaTrader 5 (M1, M5) + VWAP + EMAs       | Online / Dinâmico   | _"Executa operações velozes e soft-stops automaticamente."_ |
| **Watchdog**         | Guardião do ecossistema e Menu Inicial no Telegram        | Ações do Usuário via Telegram             | Online / Background | _"Sobe ou desce todos os processos em Python num clique."_  |
| **Scanner Elite**    | Peneira: Busca os melhores ativos em um universo amplo.   | Yahoo Finance (Intraday/Diário).          | Offline (Preparo)   | _"Quais dos 120 ativos da B3 têm o melhor Profit Factor?"_  |

---

## ⚙️ Configuração do Ambiente

Esta seção detalha o passo a passo para configurar e preparar o seu sistema. **Recomendamos o uso de Windows** para compatibilidade com o pacote oficial do `MetaTrader5` via Python.

### 1. Pré-requisitos

- Python 3.8 ou superior instalado.
- Terminal / Prompt de Comando / PowerShell.

### 2. Criando e Ativando o Ambiente Virtual

```powershell
# Criação do ambiente virtual
python -m venv venv

# Ativação no Windows (PowerShell)
.\venv\Scripts\activate

# (Opcional) Ativação no Windows (CMD)
venv\Scripts\activate.bat
```

### 3. Instalando as Dependências

Com o ambiente ativado, instale todos os pacotes:

```powershell
pip install -r requirements.txt
```

> **Principais bibliotecas instaladas:** `pandas`, `numpy`, `MetaTrader5`, `yfinance`, `Flask`, `python-telegram-bot`, `python-dotenv`.

### 4. Configuração das Variáveis de Ambiente (`.env`)

Na raiz do projeto (`Strategy/`), crie um arquivo chamado `.env` (ou edite o existente) e preencha com as suas credenciais:

```properties
GROQ_API_KEY=sua_chave_groq_aqui

TELEGRAM_TOKEN=seu_token_da_api_do_telegram_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui
```

_(Dica: Fale com o `@BotFather` no Telegram para criar um bot e pegar o Token. Fale com o `@userinfobot` para descobrir o seu Chat ID)._

---

## 📉 Guia de Conexão com MetaTrader 5

O **MetaTrader 5** é essencial para o módulo **Live_Bot_MT5**.

1. **Abertura e Contratação:** Abra conta na corretora da sua preferência (Ex: BTG Pactual) e contrate/habilite o MetaTrader 5 com RLP ativado.
2. **Instalação:** Baixe e instale a plataforma no Windows.
3. **Login:** Faça Login no MT5 inserindo o **número da conta de negociação**, sua **senha do MT5** (enviada por e-mail) e escolha o **Servidor** correto (Real ou Demo).
4. **Habilitando o Algorithmic Trading (CRÍTICO):**
   - Vá no Menu Superior ➔ **Ferramentas (Tools)** ➔ **Opções (Options)**.
   - Acesse a aba **Negociação Automatizada (Expert Advisors / Trading)**.
   - Marque a caixa de seleção: **"Permitir Negociação Automatizada" (Allow Automated Trading)**.
   - Clique em Ok. Verifique o ícone indicando que está liberado.

---

## ▶️ Como Executar a Plataforma

Aqui estão os comandos para iniciar cada parte do ecossistema. Certifique-se de estar com o ambiente virtual (venv) **ativado**.

### A. Para Realizar Mapeamento de Mercado (Scanner Elite)

Roda um script de varredura que analisa ~120 ativos da B3, efetuando backtest com Estratégia de Cruzamento de Médias Móveis (SMA 20/50).

```powershell
cd Live_Bot_MT5
python scanner_elite.py
```

**Resultado:** Os ativos aprovados (`Profit Factor > 1.20`) são gravados e geram o arquivo de resultados em `data/backtest_results.csv`, pronto para ser utilizado como filtro pelas fases de execução!

### B. Para Análise e Backtesting Web (Backtest_Project)

Dashboard com métricas focadas em análise fundamentalista, notícias e curvas de equity no passado.

```powershell
cd Backtest_Project/backend
python api.py
```

**Acesso:** Abra no navegador através de `http://localhost:5000`

### C. Para Executar a Orquestra Completa (Watchdog / App / Scalper)

Esta é a espinha dorsal operacional. Para operar em alta velocidade e receber informações e alertas no Telegram sem precisar deixar milhares de terminais manuais expostos, o sistema unificou-se através de um *Guardião (Watchdog)*.

⚠️ **Pré-requisito Crítico:** O MetaTrader 5 deve estar _Aberto_, _Logado na conta XP Demo (ou Real)_, e com o botão _Algo Trading na cor verde (Habilitado)_.

**Passo a passo diário na prática:**
1. Abra o terminal na pasta e inicie o Guardião:
```powershell
cd Live_Bot_MT5
python watchdog.py
```
2. No Bot do Watchdog no Telegram, envie o comando `/start`.
3. Clique no botão de atalho **"🟢 Ligar"**.
4. Apenas pressionando esse botão, o Watchdog engatilhará os dois robôs essenciais (A *"Torre de Controle"* via `app.py`, e o *"Motor Scalper Executivo"* via `scalper_win.py`) que blindam a sua carteira e sobem seus alertas aos segundos corretos de operação.

**Acessando a Interface Visual do Dashboard na Web:**
Embora os alertas de posição e robôs trabalhem via background invisível pelo Telegram, se desejar acompanhar os gráficos *Neo-Tech*, plotagem de histórico ou fazer análises profundas de Candlesticks atualizados no milissegundo:
👉 Abra o seu navegador web favorito e acesse: **`http://localhost:5002`**

---

## 📂 Estrutura de Diretórios Resumida

```
Strategy/
├── .env                       # Chaves e Tokens de API das aplicações.
├── Backtest_Project/          # Módulo de pesquisa longo-prazo
│   ├── backend/
│   │   ├── api.py             # Server Flask (porta 5000)
│   │   ├── backtest.py        # Algoritmos do analisador de histórico
│   │   └── fundamentalista.py
│   └── frontend/              # Interface web exploratória
│
├── Live_Bot_MT5/              # Módulo de produção e ação rápida
│   ├── watchdog.py            # Sistema-Guardião p/ ligar/desligar a orquestra inteira via Telegram
│   ├── app.py                 # (Torre de Controle) Servidor Web Flask (porta 5002) + Menu Padrão Telegram
│   ├── scalper_win.py         # (Motor) Sistema 100% autônomo M5 com VWAP, EMA e Soft-Stops dinâmicos
│   ├── controle_scalper.json  # Arquivo-Ponte. O app.py preenche, os robôs respeitam e leem limites
│   ├── scanner_elite.py       # Peneira algorítmica de ativos em Python
│   ├── templates/, static/    # UI/UX Interface Web (Glassmorphism + Gráficos 3D TradingView)
│   └── data/                  # Base de dados, CSVs de rastreio contínuo e logs de auditoria
│
├── requirements.txt           # Bibliotecas e dependências de todo o projeto
└── README.md                  # Este arquivo central de documentação
```

---

## 🛠 Solução de Problemas Comuns

- **"MetaTrader5 não foi iniciado" ou Erros de Conexão na API no Console:**
  Verifique se o Terminal MT5 está, de fato, rodando no Windows e se o login da corretora está correto. Não se esqueça de ativar o "Algo Trading".

- **Erro de Porta Ocupada (Address already in use):**
  A porta 5000 ou 5002 pode ter ficado presa. Pare o processo usando seu PID:

  ```powershell
  netstat -ano | findstr :5000  # Ou :5002
  taskkill /PID <NUMERO_PID> /F
  ```

- **Telegram Bot não reage ou dá Timeout:**
  Verifique se as variáveis `TELEGRAM_TOKEN` e `TELEGRAM_CHAT_ID` estão corretas no `.env`. Certifique-se também de ligá-lo clicando no botão no Dashboard Web antes de aguardar msgs.

---

## 👨‍💻 Desenvolvedor

Desenvolvido por **Eurico Júnior**.

_Plataforma focada na convergência entre Data Science, Backend Avançado, Concepção Interfaces (UI/UX) e Execução Automatizada de Estratégias Institucionais._

**Versão:** 1.2  
**Última Atualização:** Março 2026
