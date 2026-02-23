# 🚀 FinSense: Plataforma Estratégica de Trading Automatizado

Bem-vindo ao **FinSense**, um ecossistema completo e avançado de trading quantitativo desenvolvido em Python. A plataforma centraliza todo o fluxo de desenvolvimento de estratégias de investimento, desde a pesquisa, backtesting, e escaneamento do mercado (B3 e Forex), até a execução automatizada em tempo real (Algo Trading) no MetaTrader 5, com direito a monitoramento e alertas na palma da mão via Telegram.

---

## 🌟 Funcionalidades Principais

- **📊 Dashboards Interativos (Web):** Interfaces modernas com design _Glassmorphism_, animações _hover 3D_ e atualizações em tempo real (WebSockets / Polling).
- **📈 Análise Técnica em Tempo Real:** Cálculo e plotagem dinâmica de indicadores diretamente no gráfico, como as Médias Móveis Simples (SMAs).
- **🔬 Motor de Backtesting e Análise Fundamentalista:** Ferramentas para validar se uma estratégia funcionou nos últimos anos, checando Métricas de Risco (Profit Factor, Win Rate, Drawdown) e dados de valuation.
- **🤖 Execução Automática no MetaTrader 5:** Envio e gerenciamento de ordens automatizadas no mercado (B3/Forex).
- **⚡ Scanner Elite Integrado:** Um script de inteligência de mercado (`scanner_elite.py`) que varre o histórico de mais de 120 ativos da B3 (via `yfinance` em timeframes como 1h ou Diário) buscando configurações otimizadas de cruzamento de médias, selecionando automaticamente os ativos mais lucrativos.
- **📱 Monitoramento via Telegram Bot:** Receba alertas sobre oportunidades de mercado diretamente no seu celular. O status de funcionamento do Bot pode ser ligado e desligado (On/Off) com apenas um clique pelo painel de controle do Dashboard Web.

---

## 🏗 Arquitetura do Projeto

O FinSense é dividido em módulos principais, cada um com um propósito específico no ciclo de vida do seu capital algorítmico:

| Módulo / Ferramenta  | Objetivo Principal                                        | Fonte de Dados                            | Ambiente            | Foco Principal                                              |
| :------------------- | :-------------------------------------------------------- | :---------------------------------------- | :------------------ | :---------------------------------------------------------- |
| **Backtest_Project** | Laboratório: Pesquisa, Validação e Avaliação da robustez. | Yahoo Finance (Histórico Diário/Semanal). | Offline / Estático  | _"Esta ideia de trade é lucrativa no longo prazo?"_         |
| **Live_Bot_MT5**     | Ação: Monitoramento e Execução em Tempo Real das ordens.  | MetaTrader 5 (Tick, M1, M5, H1, etc).     | Online / Dinâmico   | _"O cruzamento das médias aconteceu agora! Executar."_      |
| **Scanner Elite**    | Peneira: Busca os melhores ativos em um universo amplo.   | Yahoo Finance (Intraday/Diário).          | Offline (Preparo)   | _"Quais dos 120 ativos da B3 têm o melhor Profit Factor?"_  |
| **Telegram Monitor** | Alerta: Envia os sinais diretos para o celular.           | Sinais do Live_Bot.                       | Online / Background | _"O que o robô está fazendo enquanto estou longe da tela?"_ |

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

### C. Para Executar as Operações Reais / Monitoramento (Live_Bot_MT5)

Este é o core da plataforma de execução. Ele se acopla ao seu MT5 logado e, opcionalmente, abre uma thread em background para enviar disparos ao seu Telegram através do `bot_viagem.py` encapsulado.
⚠️ **Pré-requisito:** O programa MetaTrader 5 deve estar _Aberto_, _Logado_ e com o _Algo Trading Habilitado_.

```powershell
cd Live_Bot_MT5
python app.py
```

**Acesso:** Abra no navegador através de `http://localhost:5002`

- Você terá o painel operacional para pausar/iniciar os robôs da b3.
- Inclui um botão dinâmico na interface para **Ativar/Desativar o Bot do Telegram**.

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
│   ├── app.py                 # Aplicação Central e Server Flask (porta 5002)
│   ├── scanner_elite.py       # Peneira algorítmica de ativos em Python
│   ├── bot_viagem.py          # Lógica do Telegram Bot de alertas de mercado
│   ├── templates/             # HTML (+ Tailwind/Vanilha CSS) do Dashboard Moderno
│   ├── static/                # ARquivos JS para atualizações em tempo real das SMAs e botões On/Off
│   └── data/                  # Base de dados (e.g., backtest_results.csv)
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

**Versão:** 1.1  
**Última Atualização:** Fevereiro 2026
