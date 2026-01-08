import pandas as pd
import numpy as np
import yfinance as yf

def get_data(ticker, period="5y"):
    """
    Coleta dados diários (OHLCV) de um ticker usando yfinance.
    """
    print(f"Baixando dados para {ticker}...")
    df = yf.download(ticker, period=period)
    
    # Garantir que temos dados
    if df.empty:
        raise ValueError(f"Nenhum dado encontrado para o ticker: {ticker}")
        
    # Manter apenas as colunas necessárias para o backtest
    return df[['Open', 'High', 'Low', 'Close', 'Volume']]

def strategy_buy_and_hold(df):
    """
    Estratégia Buy & Hold: Compra no primeiro dia e mantém.
    """
    data = df.copy()
    
    # Cálculo do retorno simples do ativo (diário)
    data['Asset_Returns'] = data['Close'].pct_change()
    
    # Sinal: 1 para todos os dias (sempre comprado)
    data['Signal'] = 1
    
    # --- EVITANDO LOOK-AHEAD BIAS ---
    # No Buy & Hold, o sinal é constante, mas para consistência métrica:
    # O retorno da estratégia no dia (t) é o sinal do dia (t-1) * retorno do ativo no dia (t).
    data['Strategy_Returns'] = data['Signal'].shift(1) * data['Asset_Returns']
    
    return data[['Close', 'Signal', 'Strategy_Returns']]

def strategy_sma_crossover(df, short_window=20, long_window=50):
    """
    Estratégia de Cruzamento de Médias Móveis Simples (SMA).
    """
    data = df.copy()
    
    # 1. Cálculo das Médias Móveis
    data['SMA_Short'] = data['Close'].rolling(window=short_window).mean()
    data['SMA_Long'] = data['Close'].rolling(window=long_window).mean()
    
    # 2. Geração de Sinais (Baseado no fechamento do dia t)
    # 1 = Comprado (SMA Curta > SMA Longa)
    # 0 = Neutro/Venda (SMA Curta <= SMA Longa)
    data['Signal'] = np.where(data['SMA_Short'] > data['SMA_Long'], 1, 0)
    
    # 3. Cálculo dos Retornos do Ativo
    data['Asset_Returns'] = data['Close'].pct_change()
    
    # --- CRÍTICO: EVITANDO LOOK-AHEAD BIAS ---
    # O sinal gerado no FECHAMENTO do dia 't' só pode ser executado no dia 't+1'.
    # Portanto, o retorno da estratégia no dia 't' é o sinal do dia 't-1' multiplicado pelo retorno do dia 't'.
    # Usamos .shift(1) para garantir que não estamos usando informações do futuro.
    data['Strategy_Returns'] = data['Signal'].shift(1) * data['Asset_Returns']
    
    return data[['Close', 'Signal', 'Strategy_Returns']]

if __name__ == "__main__":
    # Exemplo de uso
    ticker = "PETR4.SA"
    
    try:
        # 1. Coleta
        df_base = get_data(ticker)
        
        # 2. Backtest SMA Crossover
        print("\nExecutando Backtest: SMA Crossover (20/50)...")
        results_sma = strategy_sma_crossover(df_base, short_window=20, long_window=50)
        
        # 3. Backtest Buy & Hold
        print("Executando Backtest: Buy & Hold...")
        results_bh = strategy_buy_and_hold(df_base)
        
        # 4. Demonstração dos Resultados
        print("\n--- Resultados SMA Crossover (Últimos 10 dias) ---")
        print(results_sma.tail(10))
        
        # Verificação de Retorno Acumulado Simples (Apenas para conferência rápida)
        cum_ret_sma = (1 + results_sma['Strategy_Returns'].fillna(0)).cumprod()[-1] - 1
        cum_ret_bh = (1 + results_bh['Strategy_Returns'].fillna(0)).cumprod()[-1] - 1
        
        print(f"\nRetorno Acumulado SMA: {cum_ret_sma:.2%}")
        print(f"Retorno Acumulado Buy & Hold: {cum_ret_bh:.2%}")
        
    except Exception as e:
        print(f"Erro durante a execução: {e}")
