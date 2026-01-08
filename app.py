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

# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.title("🎯 Configurações")

# 1. Seleção de Ativo Simplificada
st.sidebar.subheader("Escolha o Ativo")
busca = st.sidebar.text_input("Digite o nome ou ticker (Ex: Vale, AAPL)", placeholder="Pesquisar...")

# Tickers padrão caso não haja busca
opcoes_finais = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "AAPL", "BTC-USD"]

if busca:
    try:
        res = yf.Search(busca, max_results=5).quotes
        if res:
            opcoes_finais = [q['symbol'] for q in res]
            # Adiciona a busca manual no topo se não estiver na lista
            if busca.upper() not in opcoes_finais:
                opcoes_finais.insert(0, busca.upper())
    except:
        opcoes_finais = [busca.upper()]

ticker_final = st.sidebar.selectbox("Confirme o Ticker:", options=opcoes_finais)

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
            
            # --- GRÁFICOS ---
            st.subheader(f"Análise Gráfica: {ticker_final}")
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
        else:
            st.error(f"❌ Não foi possível realizar o backtest para {ticker_final}. Tente um período maior ou verifique o ticker.")
else:
    st.info("📊 Configure as opções acima e execute o backtest.")
