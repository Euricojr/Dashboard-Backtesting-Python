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
def load_data(ticker, start, end):
    """
    Baixa e limpa dados do Yahoo Finance, eliminando qualquer MultiIndex.
    """
    try:
        data = yf.download(ticker, start=start, end=end, progress=False)
        if data.empty:
            return None
        
        # 1. Tratar MultiIndex (yfinance novo)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
            
        # 2. Puxar apenas as colunas necessárias e garantir que são Series 1D
        df = pd.DataFrame(index=data.index)
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col in data.columns:
                # Se houver duplicatas por algum erro, pega a primeira
                val = data[col]
                if isinstance(val, pd.DataFrame):
                    df[col] = val.iloc[:, 0].astype(float)
                else:
                    df[col] = val.astype(float)
        
        return df.dropna()
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

def compute_metrics(returns):
    """
    Calcula métricas financeiras.
    """
    returns = returns.dropna()
    if returns.empty:
        return {"Total": 0, "CAGR": 0, "Vol": 0, "Sharpe": 0, "MaxDD": 0}

    cum_rets = (1 + returns).cumprod()
    total_ret = cum_rets.iloc[-1] - 1
    
    n_years = len(returns) / 252
    cagr = (1 + total_ret)**(1/n_years) - 1 if n_years > 0 else 0
    
    vol = returns.std() * np.sqrt(252)
    sharpe = cagr / vol if vol > 0 else 0
    
    peak = cum_rets.cummax()
    drawdown = (cum_rets - peak) / peak
    max_dd = drawdown.min()
    
    return {
        "Total": total_ret,
        "CAGR": cagr,
        "Vol": vol,
        "Sharpe": sharpe,
        "MaxDD": max_dd
    }

# --- BARRA LATERAL ---
st.sidebar.header("⚙️ Configurações")

# Estado do Ticker
if 'tk' not in st.session_state:
    st.session_state.tk = "PETR4.SA"

# Busca Universal
search_q = st.sidebar.text_input("🔍 Pesquisar Ativo", placeholder="Digite nome ou ticker...")
if search_q:
    try:
        s = yf.Search(search_q, max_results=5).quotes
        if s:
            opts = [f"{q['symbol']} | {q.get('longname', 'Ativo')}" for q in s]
            sel = st.sidebar.selectbox("Resultados:", opts)
            st.session_state.tk = sel.split(" | ")[0]
    except:
        pass

ticker = st.sidebar.text_input("Ticker para Backtest", value=st.session_state.tk)

c1, c2 = st.sidebar.columns(2)
d_ini = c1.date_input("Início", datetime.now() - timedelta(days=365*5))
d_fim = c2.date_input("Fim", datetime.now())

st.sidebar.divider()
st.sidebar.subheader("Estratégia SMA")
win_s = st.sidebar.number_input("Média Curta", value=9, min_value=1)
win_l = st.sidebar.number_input("Média Longa", value=21, min_value=1)

run = st.sidebar.button("🚀 Executar Backtest", use_container_width=True)

# --- APP PRINCIPAL ---
st.title("� Dashboard de Backtesting Quantitativo")

if run:
    with st.spinner("Processando..."):
        df = load_data(ticker, d_ini, d_fim)
        
        if df is not None and not df.empty:
            # Lógica
            df['SMA_S'] = df['Close'].rolling(win_s).mean()
            df['SMA_L'] = df['Close'].rolling(win_l).mean()
            df['Signal'] = np.where(df['SMA_S'] > df['SMA_L'], 1, 0)
            
            # Retornos (Shift 1 para evitar Look-ahead)
            df['Asset_Ret'] = df['Close'].pct_change()
            df['Strat_Ret'] = df['Signal'].shift(1) * df['Asset_Ret']
            
            # Divisão 70/30
            split = int(len(df) * 0.7)
            df_is = df.iloc[:split]
            df_oos = df.iloc[split:]
            
            m_is = compute_metrics(df_is['Strat_Ret'])
            m_oos = compute_metrics(df_oos['Strat_Ret'])
            
            # --- VISUAL ---
            st.subheader(f"Resultado: {ticker}")
            
            # Gráfico 1: Preços
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(x=df.index, y=df['Close'], name="Preço", line=dict(color='gray', width=1)))
            fig1.add_trace(go.Scatter(x=df.index, y=df['SMA_S'], name=f"SMA {win_s}", line=dict(color='cyan')))
            fig1.add_trace(go.Scatter(x=df.index, y=df['SMA_L'], name=f"SMA {win_l}", line=dict(color='orange')))
            
            # Sinais
            sigs = df['Signal'].diff()
            buys = df[sigs == 1]
            sells = df[sigs == -1]
            
            if not buys.empty:
                fig1.add_trace(go.Scatter(x=buys.index, y=buys['Close'], mode='markers', name="Compra", 
                                          marker=dict(symbol='triangle-up', size=12, color='lime')))
            if not sells.empty:
                fig1.add_trace(go.Scatter(x=sells.index, y=sells['Close'], mode='markers', name="Venda", 
                                          marker=dict(symbol='triangle-down', size=12, color='red')))
                                          
            fig1.update_layout(template="plotly_dark", height=450, margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig1, use_container_width=True)
            
            # Gráfico 2: Equity
            st.subheader("Patrimônio Acumulado (Estratégia vs B&H)")
            eq_strat = (1 + df['Strat_Ret'].fillna(0)).cumprod()
            eq_bh = (1 + df['Asset_Ret'].fillna(0)).cumprod()
            
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=df.index, y=eq_strat, name="Estratégia", line=dict(color='cyan', width=2)))
            fig2.add_trace(go.Scatter(x=df.index, y=eq_bh, name="Buy & Hold", line=dict(color='white', dash='dot')))
            
            # Linha IS/OOS (add_shape para evitar erro de média interna do Plotly)
            split_date = df_is.index[-1]
            fig2.add_shape(type="line", x0=split_date, x1=split_date, y0=0, y1=1.1, xref="x", yref="paper",
                          line=dict(color="yellow", dash="dash", width=2))
            
            # Anotação manual para evitar o bug do add_vline
            fig2.add_annotation(x=split_date, y=1.1, yref="paper", text="Fim In-Sample", showarrow=False, font=dict(color="yellow"))
            
            fig2.update_layout(template="plotly_dark", height=400, margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig2, use_container_width=True)
            
            # Tabela
            st.subheader("Performance Geral")
            res_df = pd.DataFrame({
                "Métrica": ["Retorno Total", "CAGR", "Volatilidade", "Sharpe", "Max Drawdown"],
                "In-Sample (70%)": [f"{m_is['Total']:.2%}", f"{m_is['CAGR']:.2%}", f"{m_is['Vol']:.2%}", f"{m_is['Sharpe']:.2f}", f"{m_is['MaxDD']:.2%}"],
                "Out-of-Sample (30%)": [f"{m_oos['Total']:.2%}", f"{m_oos['CAGR']:.2%}", f"{m_oos['Vol']:.2%}", f"{m_oos['Sharpe']:.2f}", f"{m_oos['MaxDD']:.2%}"]
            })
            st.table(res_df)
            
        else:
            st.error("Nenhum dado encontrado para este ticker ou período.")
else:
    st.info("Ajuste os parâmetros na barra lateral e clique em Executar.")
