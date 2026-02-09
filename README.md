# FinSense: Plataforma de Análise Financeira com Python e MetaTrader5

Bem-vindo ao **FinSense**, um ecossistema completo de trading quantitativo que centraliza o fluxo de desenvolvimento de estratégias de investimento, desde a pesquisa e backtesting até a execução automatizada em tempo real no MetaTrader 5.

Este projeto integra análise técnica avançada, cálculo de métricas de risco e sistemas de automação para operar no mercado brasileiro (B3) e Forex.

---

## Configuração do Ambiente

Esta seção detalha o passo a passo para configurar o ambiente de desenvolvimento e preparar seu sistema para executar ambos os módulos da plataforma.

### Pré-requisitos

- **Python 3.8+** instalado em seu sistema
- **Windows** (recomendado para compatibilidade com MetaTrader 5)
- Acesso a um terminal/prompt de comando

### Criando o Ambiente Virtual

Um ambiente virtual isola as dependências do projeto do seu sistema operacional:

```powershell
python -m venv venv
```

### Ativando o Ambiente Virtual

Após criar o ambiente, você precisa ativá-lo antes de instalar as dependências.

**No Windows (PowerShell):**

```powershell
.\venv\Scripts\activate
```

**No Windows (Command Prompt):**

```cmd
venv\Scripts\activate.bat
```

**No macOS/Linux:**

```bash
source venv/bin/activate
```

### Instalando as Dependências

Com o ambiente virtual ativado, instale todos os pacotes necessários:

```powershell
pip install -r requirements.txt
```

Este comando instala as seguintes bibliotecas principais:

- **pandas** e **numpy**: Manipulação e análise de dados
- **MetaTrader5**: Integração com o terminal MT5
- **yfinance**: Download de dados históricos do Yahoo Finance
- **Flask**: Framework web para os dashboards
- **scipy**: Cálculos estatísticos avançados

---

## Guia de Conexão com MetaTrader 5

O **MetaTrader 5** é a plataforma de execução central para trading automatizado. Este guia ensina como obter acesso ao MT5 através do **Banco BTG Pactual** (ou sua corretora de preferência) e configurá-lo para funcionar com a plataforma FinSense.

### Passo 1: Abertura de Conta

1. Acesse o site do **BTG Pactual** ou sua corretora de preferência
2. Clique em "Abrir Conta" ou "Começar Agora"
3. Preencha as informações pessoais solicitadas (CPF, dados bancários, etc.)
4. Complete o processo de validação (geralmente envolve verificação de identidade)
5. Aguarde a aprovação (pode levar de 1 a 3 dias úteis)

### Passo 2: Contratação da Plataforma MetaTrader 5

1. Após a aprovação, faça login na **área logada do portal** da sua corretora
2. Navegue até a seção **"Plataformas"** ou **"Produtos"**
3. Localize a opção **"MetaTrader 5"** na lista de plataformas disponíveis
4. Clique em **"Contratar"** ou **"Ativar"**
   - O MetaTrader 5 é geralmente **gratuito** quando você tem uma conta ativa com RLP (Representante de Pessoa Física)
5. Confirme a contratação

### Passo 3: Obtenção de Credenciais

1. Após a contratação, verifique seu **e-mail cadastrado** no banco
2. Você receberá um e-mail com as seguintes informações:
   - **Login**: Número de conta de negociação (ex: 12345678)
   - **Senha**: Senha específica do MetaTrader 5
   - **Servidor**: Servidor de negociação da corretora (ex: BTGPactual-Demo ou BTGPactual-Real)

⚠️ **IMPORTANTE:** A senha do MetaTrader 5 é **diferente** da senha de acesso ao portal do banco. Guarde essas credenciais com segurança.

### Passo 4: Instalação do Software MetaTrader 5

1. Acesse o portal da sua corretora ou visite [www.metatrader5.com](https://www.metatrader5.com)
2. Clique em **"Download"** ou **"Baixar MetaTrader 5"**
3. Escolha a versão **"Para Windows"** ou **"Executável"**
4. Abra o arquivo `.exe` baixado
5. Siga o assistente de instalação (aceite os termos e escolha o diretório de instalação)
6. Aguarde a conclusão da instalação

### Passo 5: Configuração no MetaTrader 5

Agora você vai conectar o MT5 à sua conta de negociação.

#### 5.1. Abrindo o MetaTrader 5

1. Clique no ícone do MetaTrader 5 na sua área de trabalho (ou inicie via iniciar do Windows)
2. O software abrirá em poucos segundos

#### 5.2. Fazendo Login na Conta

1. No menu superior, clique em **"Arquivo"**
2. Selecione **"Login na Conta de Negociação"** (ou **"Open an Account"**)
3. Uma janela de login aparecerá
4. Preencha os campos:
   - **Login**: Insira o número de conta recebido por e-mail
   - **Senha**: Insira a senha do MetaTrader 5 recebida por e-mail
   - **Servidor**: Selecione o servidor correto da sua corretora (ex: **BTGPactual-Real** ou **BTGPactual-Demo**)
5. Clique em **"Login"**

Se os dados estiverem corretos, você verá sua conta conectada no canto inferior direito do terminal MT5.

#### 5.3. Ativando o "Algo Trading" (Negociação Automatizada)

⚠️ **CRÍTICO:** Esta etapa é essencial para permitir que o Python envie ordens automaticamente para o MetaTrader 5.

1. No menu superior do MetaTrader 5, localize a opção **"Ferramentas"** ou **"Tools"**
2. Procure por **"Opções"** ou **"Settings"**
3. Na janela de opções, vá para a aba **"Negociação"** ou **"Trading"**
4. Ative a opção **"Permitir Negociação Automatizada"** ou **"Allow Automated Trading"**
5. Certifique-se de que o checkbox está **marcado** (✓)
6. Aplique as mudanças e feche a janela

**Verificação:** Você saberá que o Algo Trading está ativado quando aparecer um ícone de robô (🤖) na barra de ferramentas do MT5 ou quando o status indicar "Automated Trading: Enabled".

---

## Arquitetura do Projeto

O projeto é dividido em dois módulos principais, cada um com um propósito específico no ciclo de vida do trading algorítmico:

## Diferenças Principais (Resumo)

| Característica     | **Backtest_Project** (O Laboratório)                | **Live_Bot_MT5** (O Executor)                        |
| :----------------- | :-------------------------------------------------- | :--------------------------------------------------- |
| **Objetivo**       | Pesquisa, Validação e "Stress Test" de estratégias. | Monitoramento em Tempo Real e Execução de Ordens.    |
| **Fonte de Dados** | **Yahoo Finance** (Foco em dados Diários/Semanais). | **MetaTrader 5** (Dados Intraday, M1, M5, Tick).     |
| **Ambiente**       | Offline / Estático (Analisa o passado).             | Online / Dinâmico (Reage ao mercado agora).          |
| **Foco Visual**    | Gráficos estatísticos, Curvas de Equity, Heatmaps.  | Dashboard Operacional, Glassmorphism, Latência Zero. |
| **Uso Principal**  | _"Essa ideia funciona nos últimos 10 anos?"_        | _"O mercado está dando sinal agora? Executar!"_      |

---

---

## Executando o Projeto

O FinSense é dividido em dois aplicativos que você pode executar conforme suas necessidades.

### Executando o Backtest_Project (Análise e Pesquisa)

O módulo de backtest é ideal para validar estratégias com dados históricos antes de colocá-las em operação real.

```powershell
cd Backtest_Project/backend
python api.py
```

Após executar o comando:

1. O servidor iniciará em `http://localhost:5000`
2. Abra seu navegador e acesse `http://localhost:5000`
3. Você terá acesso aos gráficos de backtest, métricas de desempenho e análises técnicas

**Funcionalidades Disponíveis:**

- **Dashboard Interativo:** Interface moderna com efeitos Glassmorphism, hover 3D e animações.
- **Análise Fundamentalista:** Cards detalhados de Valuation, Endividamento e Eficiência com explicações didáticas (Modais).
- **Notícias Recentes:** Seção automática de notícias relacionadas ao ativo pesquisado.
- **Backtesting Visual:** Gráficos interativos (Candlestick + Indicadores) e curvas de equity.
- **Métricas de Risco:** Sharpe Ratio, Sortino, Drawdown e Volatilidade calculados automaticamente.

### Executando o Live_Bot_MT5 (Execução em Tempo Real)

O módulo Live Bot conecta-se diretamente ao MetaTrader 5 para executar operações automaticamente.

⚠️ **Pré-requisito:** O MetaTrader 5 deve estar **aberto e logado** na sua conta antes de executar este módulo.

```powershell
cd Live_Bot_MT5
python app.py
```

Após executar o comando:

1. O servidor iniciará em `http://localhost:5002`
2. Abra seu navegador e acesse `http://localhost:5002`
3. Você terá acesso ao dashboard de operações em tempo real

**Funcionalidades Disponíveis:**

- Monitoramento em tempo real do mercado
- Execução automática de ordens
- Scanner de múltiplos ativos
- Dashboard com interface moderna (Glassmorphism)
- Controle visual para iniciar/pausar robôs
- Ajuste de parâmetros em tempo real

---

## Diferenças entre os Módulos

| Característica     | **Backtest_Project** (Pesquisa)     | **Live_Bot_MT5** (Produção)         |
| :----------------- | :---------------------------------- | :---------------------------------- |
| **Objetivo**       | Validação de estratégias no passado | Execução em tempo real no mercado   |
| **Fonte de Dados** | Yahoo Finance (dados históricos)    | MetaTrader 5 (dados intraday)       |
| **Ambiente**       | Offline / Estático                  | Online / Dinâmico                   |
| **Latência**       | N/A                                 | Ultra-baixa                         |
| **Pergunta-Chave** | "Isso funcionou antes?"             | "O mercado está dando sinal agora?" |

---

## Estrutura do Projeto

```
Strategy/
├── Backtest_Project/          # Módulo de pesquisa e análise
│   ├── backend/
│   │   ├── api.py             # API Flask para backtest
│   │   ├── backtest.py        # Motor de backtesting
│   │   └── fundamentalista.py # Análise fundamentalista
│   └── frontend/              # Interface web
│
├── Live_Bot_MT5/              # Módulo de produção
│   ├── app.py                 # Aplicação principal
│   ├── backtester.py          # Backtest para dados M1/M5
│   ├── templates/             # HTML dos dashboards
│   ├── utils/                 # Funções auxiliares
│   └── data/                  # Arquivos de dados
│
├── requirements.txt           # Dependências Python
└── README.md                  # Este arquivo
```

---

## Solução de Problemas

### MetaTrader 5 não conecta

- Verifique se o MT5 está aberto e logado
- Confirme que você inseriu as credenciais corretas (Login, Senha, Servidor)
- Verifique se o "Algo Trading" está ativado

### Erro "MetaTrader5 não foi iniciado"

- Abra manualmente o MetaTrader 5
- Certifique-se de estar conectado à sua conta
- Aguarde alguns segundos para que o MT5 sincronize completamente

### Porta já em uso (Address already in use)

Se receber um erro indicando que a porta está em uso:

```powershell
# Para Backtest_Project (porta 5000):
netstat -ano | findstr :5000
# Depois, finalize o processo:
taskkill /PID <PID> /F

# Para Live_Bot_MT5 (porta 5002):
netstat -ano | findstr :5002
taskkill /PID <PID> /F
```

---

## Desenvolvedor

Desenvolvido por **Eurico Júnior**.

_Plataforma focada na convergência entre Data Science, Análise Técnica e Execução Automatizada de Estratégias de Trading._

**Versão:** 1.0  
**Última atualização:** Fevereiro 2026
