import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="InvestDashboard PRO", layout="wide")

# --- LÓGICA DE DADOS ---

@st.cache_data
def load_data_safe(ticker, start, end):
    """
    Baixa dados do Yahoo Finance e garante que o DataFrame seja 'chapado' (sem MultiIndex).
    """
    try:
        data = yf.download(ticker, start=start, end=end, progress=False)
        
        if data.empty:
            return None
        
        # 1. TRATAMENTO DE MULTIINDEX
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
            
        # 2. RECONSTRUÇÃO BLINDADA
        clean_df = pd.DataFrame(index=data.index)
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col in data.columns:
                series = data[col]
                if isinstance(series, pd.DataFrame):
                    clean_df[col] = series.iloc[:, 0].astype(float)
                else:
                    clean_df[col] = series.astype(float)
        
        return clean_df.dropna()
    except Exception as e:
        st.error(f"Erro técnico ao baixar dados: {e}")
        return None

def compute_metrics(returns):
    pts = returns.dropna()
    if pts.empty:
        return {"Total": 0, "CAGR": 0, "Vol": 0, "Sharpe": 0, "MaxDD": 0}

    cum_curve = (1 + pts).cumprod()
    total_ret = cum_curve.iloc[-1] - 1
    years = len(pts) / 252
    cagr = (1 + total_ret)**(1/years) - 1 if years > 0 else 0
    vol = pts.std() * np.sqrt(252)
    sharpe = cagr / vol if vol > 0 else 0
    peak = cum_curve.cummax()
    dd = (cum_curve - peak) / peak
    max_dd = dd.min()
    
    return {"Total": total_ret, "CAGR": cagr, "Vol": vol, "Sharpe": sharpe, "MaxDD": max_dd}


def generate_analysis(metrics_in, metrics_out):
    """
    Gera um relatório interpretativo comparando treino e teste.
    """
    analysis = "### 🤖 Análise da IA (Simulada)\n\n"
    
    # 1. Lucratividade e Comparação (Check se existe info de B&H)
    total_oos = metrics_out['Total']
    bh_total = metrics_out.get('BH_Total')
    
    if bh_total is not None:
        if total_oos > bh_total:
            analysis += f"🚀 **Performance Excepcional:** A estratégia superou o Buy & Hold no período de teste ({total_oos:.2%} vs {bh_total:.2%}).\n\n"
        else:
            analysis += f"🐢 **Abaixo do Mercado:** A estratégia não superou o Buy & Hold ({total_oos:.2%} vs {bh_total:.2%}).\n\n"
    elif total_oos > 0:
        analysis += f"✅ **Lucratividade:** A estratégia foi lucrativa no período de teste com retorno de {total_oos:.2%}.\n\n"
    else:
        analysis += f"❌ **Prejuízo:** A estratégia não foi lucrativa no período de teste ({total_oos:.2%}).\n\n"
    
    # 2. Overfitting (Comparação de Sharpe)
    sharpe_is = metrics_in['Sharpe']
    sharpe_oos = metrics_out['Sharpe']
    
    if sharpe_is > 0 and (sharpe_oos < 0 or sharpe_oos < sharpe_is * 0.5):
        analysis += "⚠️ **Alerta de Possível Overfitting:** O Sharpe caiu drasticamente no teste (Out-of-Sample). Isso sugere que os parâmetros podem estar muito 'viciados' no passado.\n\n"
    else:
        analysis += "💎 **Robustez:** O desempenho no teste foi consistente com o treino, indicando uma estratégia mais confiável.\n\n"
        
    # 3. Risco (Drawdown)
    max_dd = abs(metrics_out['MaxDD'])
    if max_dd > 0.30:
        analysis += f"🚩 **Risco Elevado:** O Drawdown Máximo de {max_dd:.2%} ultrapassa o limite prudencial de 30%. Cuidado com a volatilidade!\n\n"
    
    return analysis

# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.title("🎯 Configurações")

# 1. Listas Categorizadas
BR_STOCKS = {
    "PETR4.SA": "Petrobras (PETR4)", "VALE3.SA": "Vale (VALE3)", "ITUB4.SA": "Itaú Unibanco (ITUB4)",
    "BBAS3.SA": "Banco do Brasil (BBAS3)", "BBDC4.SA": "Bradesco (BBDC4)", "ABEV3.SA": "Ambev (ABEV3)",
    "WEGE3.SA": "Weg (WEGE3)", "JBSS3.SA": "JBS (JBSS3)", "ELET3.SA": "Eletrobras (ELET3)",
    "B3SA3.SA": "B3 (B3SA3)", "RENT3.SA": "Localiza (RENT3)", "SUZB3.SA": "Suzano (SUZB3)",
    "GGBR4.SA": "Gerdau (GGBR4)", "RDOR3.SA": "Rede D'Or (RDOR3)", "RADL3.SA": "RaiaDrogasil (RADL3)",
    "HAPV3.SA": "Hapvida (HAPV3)", "CSAN3.SA": "Cosan (CSAN3)", "VIVT3.SA": "Vivo (VIVT3)",
    "CPLE6.SA": "Copel (CPLE6)", "EQTL3.SA": "Equatorial (EQTL3)", "BBSE3.SA": "BB Seguridade (BBSE3)",
    "RAIZ4.SA": "Raízen (RAIZ4)", "UGPA3.SA": "Ultrapar (UGPA3)", "LREN3.SA": "Lojas Renner (LREN3)",
    "PRIO3.SA": "Prio (PRIO3)", "CMIG4.SA": "Cemig (CMIG4)", "ENEV3.SA": "Eneva (ENEV3)",
    "ASAI3.SA": "Assaí (ASAI3)", "TOTS3.SA": "Totvs (TOTS3)", "SBSP3.SA": "Sabesp (SBSP3)",
    "VBBR3.SA": "Vibra (VBBR3)", "CCRO3.SA": "CCR (CCRO3)", "TIMS3.SA": "TIM (TIMS3)",
    "CPFE3.SA": "CPFL Energia (CPFE3)", "STBP3.SA": "Santos Brasil (STBP3)", "EMBR3.SA": "Embraer (EMBR3)",
    "GOAU4.SA": "Gerdau Metalúrgica (GOAU4)", "ALOS3.SA": "Allos (ALOS3)", "CYRE3.SA": "Cyrela (CYRE3)",
    "EGIE3.SA": "Engie (EGIE3)", "CSNA3.SA": "Siderúrgica Nac (CSNA3)", "YDUQ3.SA": "Yduqs (YDUQ3)",
    "MRFG3.SA": "Marfrig (MRFG3)", "COGN3.SA": "Cogna (COGN3)", "MRVE3.SA": "MRV (MRVE3)",
    "BRKM5.SA": "Braskem (BRKM5)", "MULT3.SA": "Multiplan (MULT3)", "CRFB3.SA": "Carrefour BR (CRFB3)",
    "PCAR3.SA": "Pão de Açúcar (PCAR3)", "MGLU3.SA": "Magalu (MGLU3)"
}

US_STOCKS = {
    "AAPL": "Apple (AAPL)", "MSFT": "Microsoft (MSFT)", "NVDA": "NVIDIA (NVDA)", "GOOGL": "Alphabet (GOOGL)",
    "AMZN": "Amazon (AMZN)", "META": "Meta (META)", "TSLA": "Tesla (TSLA)", "BRK-B": "Berkshire (BRK-B)",
    "LLY": "Eli Lilly (LLY)", "AVGO": "Broadcom (AVGO)", "WMT": "Walmart (WMT)", "JPM": "JPMorgan (JPM)",
    "V": "Visa (V)", "ORCL": "Oracle (ORCL)", "XOM": "Exxon Mobil (XOM)", "MA": "Mastercard (MA)",
    "JNJ": "Johnson & Johnson (JNJ)", "NFLX": "Netflix (NFLX)", "BAC": "Bank of America (BAC)",
    "ABBV": "AbbVie (ABBV)", "COST": "Costco (COST)", "PG": "Procter & Gamble (PG)", "HD": "Home Depot (HD)",
    "AMD": "AMD (AMD)", "ADBE": "Adobe (ADBE)", "CRM": "Salesforce (CRM)", "KO": "Coca-Cola (KO)",
    "PEP": "PepsiCo (PEP)", "TMO": "Thermo Fisher (TMO)", "DIS": "Disney (DIS)", "CSCO": "Cisco (CSCO)",
    "INTU": "Intuit (INTU)", "PFE": "Pfizer (PFE)", "LIN": "Linde (LIN)", "AMAT": "Applied Materials (AMAT)",
    "CMCSA": "Comcast (CMCSA)", "TXN": "Texas Instr (TXN)", "QCOM": "Qualcomm (QCOM)", "AMD": "AMD (AMD)",
    "PLTR": "Palantir (PLTR)", "MU": "Micron (MU)", "GE": "General Electric (GE)", "CAT": "Caterpillar (CAT)",
    "IBM": "IBM (IBM)", "UBER": "Uber (UBER)", "BA": "Boeing (BA)", "INTC": "Intel (INTC)",
    "GS": "Goldman Sachs (GS)", "MS": "Morgan Stanley (MS)", "SBUX": "Starbucks (SBUX)"
}

CRYPTO = {
    "BTC-USD": "Bitcoin (BTC)", "ETH-USD": "Ethereum (ETH)", "SOL-USD": "Solana (SOL)", "BNB-USD": "BNB (BNB)",
    "XRP-USD": "XRP (XRP)", "DOGE-USD": "Dogecoin (DOGE)", "ADA-USD": "Cardano (ADA)", "TRX-USD": "TRON (TRX)",
    "AVAX-USD": "Avalanche (AVAX)", "DOT-USD": "Polkadot (DOT)", "LINK-USD": "Chainlink (LINK)",
    "SHIB-USD": "Shiba Inu (SHIB)", "BCH-USD": "Bitcoin Cash (BCH)", "LTC-USD": "Litecoin (LTC)",
    "NEAR-USD": "NEAR Protocol (NEAR)", "UNI-USD": "Uniswap (UNI)", "MATIC-USD": "Polygon (MATIC)",
    "ICP-USD": "Internet Computer (ICP)", "ETC-USD": "Ethereum Classic (ETC)", "FIL-USD": "Filecoin (FIL)",
    "XLM-USD": "Stellar (XLM)", "XMR-USD": "Monero (XMR)", "ATOM-USD": "Cosmos (ATOM)", "APT-USD": "Aptos (APT)",
    "HBAR-USD": "Hedera (HBAR)", "VET-USD": "VeChain (VET)", "OP-USD": "Optimism (OP)", "ARB-USD": "Arbitrum (ARB)",
    "RNDR-USD": "Render (RNDR)", "INJ-USD": "Injective (INJ)", "STX-USD": "Stacks (STX)", "KAS-USD": "Kaspa (KAS)",
    "FTM-USD": "Fantom (FTM)", "AAVE-USD": "Aave (AAVE)", "TIA-USD": "Celestia (TIA)", "THETA-USD": "Theta (THETA)",
    "EGLD-USD": "MultiversX (EGLD)", "SAND-USD": "The Sandbox (SAND)", "MANA-USD": "Decentraland (MANA)",
    "EOS-USD": "EOS (EOS)", "FLOW-USD": "Flow (FLOW)", "QNT-USD": "Quant (QNT)", "AXS-USD": "Axie Infinity (AXS)",
    "MKR-USD": "Maker (MKR)", "GRT-USD": "The Graph (GRT)", "SNX-USD": "Synthetix (SNX)", "GALA-USD": "Gala (GALA)",
    "ALGO-USD": "Algorand (ALGO)", "LDO-USD": "Lido DAO (LDO)", "KAVA-USD": "Kava (KAVA)"
}

INDICES = {
    "^BVSP": "IBOVESPA (BR)", "^GSPC": "S&P 500 (US)", "^DJI": "Dow Jones (US)", "^IXIC": "NASDAQ (US)",
    "^NDX": "NASDAQ 100 (US)", "^FTSE": "FTSE 100 (UK)", "^GDAXI": "DAX (GER)", "^FCHI": "CAC 40 (FR)",
    "^N225": "Nikkei 225 (JP)", "^HSI": "Hang Seng (HK)", "^AXJO": "ASX 200 (AU)", "^NSEI": "NIFTY 50 (IN)",
    "^GSPTSE": "S&P/TSX (CA)", "^STOXX50E": "Euro Stoxx 50 (EU)", "000001.SS": "SSE Comp (CN)",
    "399001.SZ": "SZSE Comp (CN)", "^SSMI": "SMI (CH)", "^KS11": "KOSPI (KR)", "^STI": "Straits Times (SG)",
    "^TWII": "TSEC Weighted (TW)"
}

# Unindo tudo para o seletor
CATEGORIES = {
    "🇧🇷 Ações Brasil": BR_STOCKS,
    "🇺🇸 Ações EUA": US_STOCKS,
    "₿ Criptomoedas": CRYPTO,
    "📊 Índices Globais": INDICES
}

st.sidebar.subheader("Escolha o Ativo")

# Flatten list for selectbox options
all_options = []
for cat, stocks in CATEGORIES.items():
    all_options.append(f"--- {cat} ---")
    all_options.extend(stocks.keys())
all_options.append("🔍 PESQUISAR OUTRO...")

selected_option = st.sidebar.selectbox(
    "Selecione um ativo ou pesquise:",
    options=all_options,
    index=1 # Começa em PETR4
)

# Lógica de seleção
if selected_option == "🔍 PESQUISAR OUTRO...":
    busca = st.sidebar.text_input("Digite o ticker (Ex: WEGE3.SA, GOOG):", placeholder="Ticker...")
    ticker_final = busca.upper() if busca else "PETR4.SA"
elif selected_option.startswith("---"):
    st.sidebar.warning("Selecione um ativo válido (não um cabeçalho)")
    ticker_final = "PETR4.SA"
else:
    ticker_final = selected_option

# Nome amigável para exibição
friendly_name = ticker_final
for cat, stocks in CATEGORIES.items():
    if ticker_final in stocks:
        friendly_name = stocks[ticker_final]
        break

st.sidebar.divider()

# 2. Período e Parâmetros
c_d1, c_d2 = st.sidebar.columns(2)
start_date = c_d1.date_input("Início", datetime.now() - timedelta(days=365*5))
end_date = c_d2.date_input("Fim", datetime.now())

st.sidebar.subheader("Médias Móveis")
s_win = st.sidebar.number_input("Janela Curta", value=9, min_value=1)
l_win = st.sidebar.number_input("Janela Longa", value=21, min_value=1)

run_backtest = st.sidebar.button("🚀 EXECUTAR BACKTEST", use_container_width=True)

# 3. Ferramentas no final
st.sidebar.divider()
if st.sidebar.button("🧹 Limpar Dados (Reset)"):
    st.cache_data.clear()
    st.rerun()

# --- ÁREA PRINCIPAL ---
st.title("📈 Dashboard Quantitativo")

if run_backtest:
    with st.spinner("Processando..."):
        df_base = load_data_safe(ticker_final, start_date, end_date)
        
        if df_base is not None and len(df_base) > l_win:
            df = df_base.copy()
            df['SMA_S'] = df['Close'].rolling(s_win).mean()
            df['SMA_L'] = df['Close'].rolling(l_win).mean()
            df['Signal'] = np.where(df['SMA_S'] > df['SMA_L'], 1, 0)
            df['Asset_Ret'] = df['Close'].pct_change()
            df['Strat_Ret'] = df['Signal'].shift(1) * df['Asset_Ret']
            
            limit = int(len(df) * 0.7)
            df_is = df.iloc[:limit]
            df_oos = df.iloc[limit:]
            m_is = compute_metrics(df_is['Strat_Ret'])
            m_oos = compute_metrics(df_oos['Strat_Ret'])
            
            # Adicionando B&H para comparação na IA
            m_bh_oos = compute_metrics(df_oos['Asset_Ret'])
            m_oos['BH_Total'] = m_bh_oos['Total']
            
            # --- GRÁFICOS ---
            st.subheader(f"Análise Gráfica: {friendly_name}")
            fig_p = go.Figure()
            fig_p.add_trace(go.Scatter(x=df.index, y=df['Close'], name="Preço", line=dict(color='#888', width=1)))
            fig_p.add_trace(go.Scatter(x=df.index, y=df['SMA_S'], name=f"SMA {s_win}", line=dict(color='cyan', width=1.5)))
            fig_p.add_trace(go.Scatter(x=df.index, y=df['SMA_L'], name=f"SMA {l_win}", line=dict(color='orange', width=1.5)))
            
            trades = df['Signal'].diff()
            buys = df[trades == 1]; sells = df[trades == -1]
            if not buys.empty: fig_p.add_trace(go.Scatter(x=buys.index, y=buys['Close'], mode='markers', name="Compra", marker=dict(symbol='triangle-up', size=12, color='lime')))
            if not sells.empty: fig_p.add_trace(go.Scatter(x=sells.index, y=sells['Close'], mode='markers', name="Venda", marker=dict(symbol='triangle-down', size=12, color='red')))
            fig_p.update_layout(template="plotly_dark", height=450, margin=dict(l=0,r=0,t=20,b=0))
            st.plotly_chart(fig_p, use_container_width=True)
            
            st.subheader("Retorno Acumulado")
            eq_strat = (1 + df['Strat_Ret'].fillna(0)).cumprod()
            eq_bh = (1 + df['Asset_Ret'].fillna(0)).cumprod()
            fig_e = go.Figure()
            fig_e.add_trace(go.Scatter(x=df.index, y=eq_strat, name="Estratégia", line=dict(color='cyan', width=2)))
            fig_e.add_trace(go.Scatter(x=df.index, y=eq_bh, name="B&H", line=dict(color='white', dash='dot')))
            
            div_date = df_is.index[-1]
            fig_e.add_shape(type="line", x0=div_date, x1=div_date, y0=0, y1=1, xref="x", yref="paper", line=dict(color="#FFD700", dash="dash", width=2))
            fig_e.add_annotation(x=div_date, y=0.95, yref="paper", text="Fim In-Sample ", showarrow=False, font=dict(color="#FFD700"))
            fig_e.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,t=20,b=0))
            st.plotly_chart(fig_e, use_container_width=True)
            
            # --- PERFORMANCE ---
            st.subheader("Relatório de Performance")
            res_table = pd.DataFrame({
                "Métrica": ["Retorno Total", "CAGR", "Volatilidade", "Sharpe", "MaxDD"],
                "In-Sample": [f"{m_is['Total']:.2%}", f"{m_is['CAGR']:.2%}", f"{m_is['Vol']:.2%}", f"{m_is['Sharpe']:.2f}", f"{m_is['MaxDD']:.2%}"],
                "Out-of-Sample": [f"{m_oos['Total']:.2%}", f"{m_oos['CAGR']:.2%}", f"{m_oos['Vol']:.2%}", f"{m_oos['Sharpe']:.2f}", f"{m_oos['MaxDD']:.2%}"]
            })
            st.table(res_table)

            # --- IA EXPLICATIVA ---
            st.divider()
            analysis_text = generate_analysis(m_is, m_oos)
            
            if "Overfitting" in analysis_text or "Prejuízo" in analysis_text or "não superou" in analysis_text:
                st.warning(analysis_text)
            else:
                st.info(analysis_text)

        else:
            st.error(f"❌ Não foi possível realizar o backtest para {ticker_final}. Tente um período maior ou verifique o ticker.")
else:
    st.info("📊 Configure as opções acima e execute o backtest.")

# --- RODAPÉ ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #888;'>"
    "Projeto de Backtesting Quantitativo | Desenvolvido por <b>Eurico Júnior</b>"
    "</div>", 
    unsafe_allow_html=True
)
