import streamlit as st
import pandas as pd
import backtest
import yfinance as yf
import numpy as np

# Configuração da Página
st.set_page_config(page_title="Dashboard Quantitativo (Legacy)", layout="wide", page_icon="📈")

# Estilo Customizado (Tenta replicar o look antigo)
st.markdown("""
<style>
    .metric-card {
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #333;
        text-align: center;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #00e676;
    }
    .metric-label {
        font-size: 14px;
        color: #b0bec5;
    }
</style>
""", unsafe_allow_html=True)

st.title("📈 Dashboard de Backtesting (Versão Streamlit)")
st.caption("Esta versão foi recriada para fins de comparação com a versão Web/Flask.")

# --- Sidebar ---
st.sidebar.header("Parâmetros")

ticker = st.sidebar.text_input("Ticker (Yahoo Finance)", value="PETR4.SA")
start_date = st.sidebar.date_input("Início", value=pd.to_datetime("2020-01-01"))
end_date = st.sidebar.date_input("Fim", value=pd.to_datetime("2024-01-01"))

strategy_type = st.sidebar.selectbox("Estratégia", ["Média Móvel (SMA)", "RSI Semanal"])

if strategy_type == "Média Móvel (SMA)":
    sma_short = st.sidebar.number_input("Média Curta", min_value=1, value=20)
    sma_long = st.sidebar.number_input("Média Longa", min_value=1, value=50)
elif strategy_type == "RSI Semanal":
    rsi_lower = st.sidebar.number_input("RSI Inferior (Compra)", value=35)
    rsi_upper = st.sidebar.number_input("RSI Superior (Venda)", value=70)

btn_run = st.sidebar.button("Executar Backtest")

if btn_run:
    with st.spinner("Baixando dados e calculando..."):
        try:
            # 1. Baixar Dados
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            
            if df.empty:
                st.error("Nenhum dado encontrado!")
                st.stop()
            
            # Ajuste para MultiIndex se necessário
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # 2. Executar Estratégia
            if strategy_type == "Média Móvel (SMA)":
                res = backtest.strategy_sma_crossover(df, short_window=int(sma_short), long_window=int(sma_long))
                st.subheader(f"Estratégia: SMA {int(sma_short)}/{int(sma_long)}")
            else:
                res = backtest.strategy_rsi_weekly(df, lower=rsi_lower, upper=rsi_upper)
                st.subheader(f"Estratégia: RSI Semanal ({rsi_lower}/{rsi_upper})")

            # 3. Divisão In-Sample / Out-of-Sample
            limit = int(len(res) * 0.7)
            res_is = res.iloc[:limit]
            res_oos = res.iloc[limit:]

            split_date = res.index[limit].strftime('%Y-%m-%d')
            st.info(f"Divisão Treino/Teste: {split_date}")

            # 4. Calcular Métricas
            metrics_is = backtest.calculate_metrics(res_is['Strategy_Returns'])
            metrics_oos = backtest.calculate_metrics(res_oos['Strategy_Returns'])
            
            # Buy & Hold no período OOS para comparação
            bh_return = (res_oos['Close'].iloc[-1] / res_oos['Close'].iloc[0]) - 1
            metrics_oos['Buy & Hold'] = bh_return

            # --- Exibição ---

            # Métricas
            c1, c2 = st.columns(2)
            
            with c1:
                st.markdown("### Treino (In-Sample)")
                col_a, col_b = st.columns(2)
                col_a.metric("Retorno Total", f"{metrics_is.get('Total Return', 0):.2%}")
                col_b.metric("Sharpe", f"{metrics_is.get('Sharpe Ratio', 0):.2f}")
                
            with c2:
                st.markdown("### Teste (Out-of-Sample)")
                col_c, col_d, col_e = st.columns(3)
                col_c.metric("Retorno Total", f"{metrics_oos.get('Total Return', 0):.2%}")
                col_d.metric("Buy & Hold", f"{metrics_oos.get('Buy & Hold', 0):.2%}")
                col_e.metric("Sharpe", f"{metrics_oos.get('Sharpe Ratio', 0):.2f}")

            # Gráficos
            st.markdown("---")
            st.subheader("Curva de Patrimônio (Teste)")
            
            # Preparar dados para o gráfico
            res_oos = res_oos.copy()
            res_oos['Estratégia'] = (1 + res_oos['Strategy_Returns']).cumprod()
            res_oos['Buy & Hold'] = (1 + res_oos['Close'].pct_change()).cumprod()
            
            st.line_chart(res_oos[['Estratégia', 'Buy & Hold']])

            # Tabela de Dados (Opcional)
            with st.expander("Ver Dados Detalhados"):
                st.dataframe(res_oos.tail(100))

        except Exception as e:
            st.error(f"Erro ao executar: {e}")
            # Em caso de erro, mostramos o traceback para debug
            import traceback
            st.code(traceback.format_exc())
