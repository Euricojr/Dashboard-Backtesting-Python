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
    Isso corrige o problema de labels estranhos no gráfico.
    """
    try:
        # Download sem progresso para evitar poluição no terminal
        data = yf.download(ticker, start=start, end=end, progress=False)
        
        if data.empty:
            return None
        
        # 1. TRATAMENTO DE MULTIINDEX (yfinance > 0.2.x)
        # Se as colunas forem (Metrica, Ticker), removemos o Ticker para evitar confusão no Plotly
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
            
        # 2. RECONSTRUÇÃO BLINDADA
        # Criamos um novo DataFrame contendo apenas colunas 1D numéricas
        clean_df = pd.DataFrame(index=data.index)
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col in data.columns:
                series = data[col]
                # Se houver múltiplas colunas com o mesmo nome (ex: erro no download), pegamos a primeira
                if isinstance(series, pd.DataFrame):
                    clean_df[col] = series.iloc[:, 0].astype(float)
                else:
                    clean_df[col] = series.astype(float)
        
        return clean_df.dropna()
    except Exception as e:
        st.error(f"Erro técnico ao baixar dados: {e}")
        return None

def compute_metrics(returns):
    """
    Calcula as principais métricas financeiras.
    """
    pts = returns.dropna()
    if pts.empty:
        return {"Total": 0, "CAGR": 0, "Vol": 0, "Sharpe": 0, "MaxDD": 0}

    cum_curve = (1 + pts).cumprod()
    total_ret = cum_curve.iloc[-1] - 1
    
    # Anualização baseada no número de dias de dados
    years = len(pts) / 252
    cagr = (1 + total_ret)**(1/years) - 1 if years > 0 else 0
    vol = pts.std() * np.sqrt(252)
    sharpe = cagr / vol if vol > 0 else 0
    
    peak = cum_curve.cummax()
    dd = (cum_curve - peak) / peak
    max_dd = dd.min()
    
    return {
        "Total": total_ret, "CAGR": cagr, "Vol": vol, "Sharpe": sharpe, "MaxDD": max_dd
    }

# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.title("🎯 Controle")

# Botão para Limpar Cache (Ajuda a resolver erros de memória do Streamlit)
if st.sidebar.button("🧹 Limpar Cache do Sistema"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()

if 'tk_atual' not in st.session_state:
    st.session_state.tk_atual = "PETR4.SA"

# Busca Dinâmica Universal
query = st.sidebar.text_input("🔍 Buscar Ativo (Nome ou Ticker)", placeholder="Ex: Petrobras, ITUB, AAPL...")
if query:
    try:
        search_res = yf.Search(query, max_results=5).quotes
        if search_res:
            opts = [f"{q['symbol']} | {q.get('longname', 'Ativo')}" for q in search_res]
            sel = st.sidebar.selectbox("Resultados Encontrados:", opts)
            st.session_state.tk_atual = sel.split(" | ")[0]
    except:
        pass

ticker_final = st.sidebar.text_input("Ticker Ativo", value=st.session_state.tk_atual)

c_d1, c_d2 = st.sidebar.columns(2)
start_date = c_d1.date_input("Início", datetime.now() - timedelta(days=365*5))
end_date = c_d2.date_input("Fim", datetime.now())

st.sidebar.subheader("Médias Móveis")
s_win = st.sidebar.number_input("Curta", value=9, min_value=1)
l_win = st.sidebar.number_input("Longa", value=21, min_value=1)

run_backtest = st.sidebar.button("🚀 EXECUTAR BACKTEST", use_container_width=True)

# --- ÁREA PRINCIPAL ---
st.title("📈 Dashboard Quantitativo")

if run_backtest:
    with st.spinner("Limpando e processando dados..."):
        df_base = load_data_safe(ticker_final, start_date, end_date)
        
        if df_base is not None and len(df_base) > l_win:
            # 1. LÓGICA DA ESTRATÉGIA
            df = df_base.copy()
            df['SMA_S'] = df['Close'].rolling(s_win).mean()
            df['SMA_L'] = df['Close'].rolling(l_win).mean()
            
            # Gerar Sinais
            df['Signal'] = np.where(df['SMA_S'] > df['SMA_L'], 1, 0)
            
            # Retornos (Shift 1 evita o viés de olhar o futuro)
            df['Asset_Ret'] = df['Close'].pct_change()
            df['Strat_Ret'] = df['Signal'].shift(1) * df['Asset_Ret']
            
            # 2. DIVISÃO IN-SAMPLE/OUT-OF-SAMPLE (70/30)
            limit = int(len(df) * 0.7)
            df_is = df.iloc[:limit]
            df_oos = df.iloc[limit:]
            
            m_is = compute_metrics(df_is['Strat_Ret'])
            m_oos = compute_metrics(df_oos['Strat_Ret'])
            
            # --- INTERFACE VISUAL ---
            
            # Gráfico de Preço (Sem labels MultiIndex)
            st.subheader(f"Análise Gráfica: {ticker_final}")
            fig_p = go.Figure()
            fig_p.add_trace(go.Scatter(x=df.index, y=df['Close'], name="Preço", line=dict(color='#888', width=1)))
            fig_p.add_trace(go.Scatter(x=df.index, y=df['SMA_S'], name=f"SMA {s_win}", line=dict(color='cyan', width=1.5)))
            fig_p.add_trace(go.Scatter(x=df.index, y=df['SMA_L'], name=f"SMA {l_win}", line=dict(color='orange', width=1.5)))
            
            # Marcadores de Trade
            trades = df['Signal'].diff()
            buys = df[trades == 1]
            sells = df[trades == -1]
            
            if not buys.empty:
                fig_p.add_trace(go.Scatter(x=buys.index, y=buys['Close'], mode='markers', name="Compra", marker=dict(symbol='triangle-up', size=12, color='lime')))
            if not sells.empty:
                fig_p.add_trace(go.Scatter(x=sells.index, y=sells['Close'], mode='markers', name="Venda", marker=dict(symbol='triangle-down', size=12, color='red')))
                
            fig_p.update_layout(template="plotly_dark", height=450, margin=dict(l=0,r=0,t=20,b=0), xaxis_title="Data", yaxis_title="Preço (R$)")
            st.plotly_chart(fig_p, use_container_width=True)
            
            # Gráfico de Equity
            st.subheader("Simulação de Capital (Acumulado)")
            equity_strat = (1 + df['Strat_Ret'].fillna(0)).cumprod()
            equity_bh = (1 + df['Asset_Ret'].fillna(0)).cumprod()
            
            fig_e = go.Figure()
            fig_e.add_trace(go.Scatter(x=df.index, y=equity_strat, name="Estratégia", line=dict(color='cyan', width=2)))
            fig_e.add_trace(go.Scatter(x=df.index, y=equity_bh, name="Compra e Segura (B&H)", line=dict(color='white', dash='dot')))
            
            # DIVISÓRIA (Solução definitiva: add_shape manual)
            # Evita o bug interno do Plotly que tenta somar escalas de data
            div_date = df_is.index[-1]
            fig_e.add_shape(type="line", x0=div_date, x1=div_date, y0=0, y1=1, xref="x", yref="paper",
                           line=dict(color="#FFD700", dash="dash", width=2))
            
            fig_e.add_annotation(x=div_date, y=0.95, yref="paper", text="Fim In-Sample  ", showarrow=False, font=dict(color="#FFD700"))
            
            fig_e.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,t=20,b=0), xaxis_title="Data", yaxis_title="Patrimônio (Base 1.0)")
            st.plotly_chart(fig_e, use_container_width=True)
            
            # TABELA DE RESULTADOS
            st.subheader("Relatório de Performance")
            res_table = pd.DataFrame({
                "KPI": ["Retorno Total", "Retorno Anual (CAGR)", "Volatilidade Anual", "Índice Sharpe", "Queda Máxima (Drawdown)"],
                "In-Sample (Treino)": [f"{m_is['Total']:.2%}", f"{m_is['CAGR']:.2%}", f"{m_is['Vol']:.2%}", f"{m_is['Sharpe']:.2f}", f"{m_is['MaxDD']:.2%}"],
                "Out-of-Sample (Validação)": [f"{m_oos['Total']:.2%}", f"{m_oos['CAGR']:.2%}", f"{m_oos['Vol']:.2%}", f"{m_oos['Sharpe']:.2f}", f"{m_oos['MaxDD']:.2%}"]
            })
            st.table(res_table)
            st.info("💡 **Dica:** Um bom modelo deve manter métricas similares tanto no In-Sample quanto no Out-of-Sample.")
            
        else:
            st.error("Dados insuficientes ou Ticker inválido. Tente aumentar o período ou trocar o ativo.")
else:
    st.info("DASHBOARD PRONTO. Configure os ativos na lateral e clique em 'Executar Backtest'.")
