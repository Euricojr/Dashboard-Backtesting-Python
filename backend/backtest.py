import pandas as pd
import numpy as np
import yfinance as yf

def get_data(ticker, period="5y"):
    """
    Coleta dados diários (OHLCV) de um ticker usando yfinance.
    """
    print(f"Baixando dados para {ticker}...")
    df = yf.download(ticker, period=period)
    
    if df.empty:
        raise ValueError(f"Nenhum dado encontrado para o ticker: {ticker}")
        
    return df[['Open', 'High', 'Low', 'Close', 'Volume']]

def calculate_metrics(daily_returns):
    """
    Calcula métricas de performance para uma série de retornos diários.
    Corrigido para evitar FutureWarnings usando .iloc.
    """
    returns = daily_returns.dropna()
    if returns.empty:
        return {
            "Total Return": 0, "CAGR": 0, "Vol Anual": 0, 
            "Sharpe Ratio": 0, "Max Drawdown": 0
        }

    # 1. Retorno Total (Corrigido com .iloc[-1])
    cumulative_series = (1 + returns).cumprod()
    total_return = cumulative_series.iloc[-1] - 1
    
    # 2. CAGR (Retorno Anualizado)
    # Assumindo 252 dias úteis por ano
    n_days = len(returns)
    cagr = (1 + total_return) ** (252 / n_days) - 1
    
    # 3. Volatilidade Anualizada
    vol_anual = returns.std() * np.sqrt(252)
    
    # 4. Sharpe Ratio (Risk-Free = 0)
    sharpe = cagr / vol_anual if vol_anual != 0 else 0
    
    # 5. Max Drawdown
    peak = cumulative_series.cummax()
    drawdown = (cumulative_series - peak) / peak
    max_drawdown = drawdown.min()
    
    return {
        "Total Return": total_return,
        "CAGR": cagr,
        "Vol Anual": vol_anual,
        "Sharpe Ratio": sharpe,
        "Max Drawdown": max_drawdown
    }

def strategy_buy_and_hold(df):
    """
    Estratégia Buy & Hold: Compra no primeiro dia e mantém.
    """
    data = df.copy()
    data['Asset_Returns'] = data['Close'].pct_change()
    data['Signal'] = 1
    data['Strategy_Returns'] = data['Signal'].shift(1) * data['Asset_Returns']
    return data[['Close', 'Signal', 'Strategy_Returns']]

def calculate_rsi(series, period=14):
    """
    Calcula o RSI (Relative Strength Index).
    """
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def strategy_rsi_weekly(df, lower=35, upper=70):
    """
    Estratégia RSI Semanal:
    1. Resample para Semanal.
    2. Calcula RSI(14).
    3. Sinais: RSI < 35 (Compra), RSI > 70 (Venda).
    4. Projeta sinais de volta para Diário.
    """
    # Passo A: Resample para Semanal (usando último valor da semana)
    df_weekly = df.resample('W').last().copy()
    
    # Passo B: Calcula RSI Semanal
    df_weekly['RSI'] = calculate_rsi(df_weekly['Close'], period=14)
    
    # Passo C: Sinais Semanais
    # 1 = Compra, 0 = Venda, NaN = Manter
    df_weekly['Signal_Weekly'] = np.nan
    df_weekly.loc[df_weekly['RSI'] < lower, 'Signal_Weekly'] = 1
    df_weekly.loc[df_weekly['RSI'] > upper, 'Signal_Weekly'] = 0
    
    # Passo D: Merge (Joga sinais semanais volta para diário)
    # Reindex para o índice diário original e preenche para frente (ffill)
    # Isso faz com que o sinal da semana passada persista durante a semana atual
    daily_signals = df_weekly['Signal_Weekly'].reindex(df.index).ffill()
    
    # Prepara DataFrame de saída
    data = df.copy()
    data['Signal'] = daily_signals
    
    # Preenche NaNs iniciais com 0 ou mantém (se ffill não cobrir o início) -> assumimos flat (0)
    data['Signal'] = data['Signal'].fillna(0)
    
    data['Asset_Returns'] = data['Close'].pct_change()
    
    # Passo E: Viés (Trade no dia seguinte ao sinal)
    data['Strategy_Returns'] = data['Signal'].shift(1) * data['Asset_Returns']
    
    return data[['Close', 'Signal', 'Strategy_Returns']]

def strategy_sma_crossover(df, short_window=20, long_window=50):
    """
    Estratégia de Cruzamento de Médias Móveis Simples (SMA).
    """
    data = df.copy()
    data['SMA_Short'] = data['Close'].rolling(window=short_window).mean()
    data['SMA_Long'] = data['Close'].rolling(window=long_window).mean()
    data['Signal'] = np.where(data['SMA_Short'] > data['SMA_Long'], 1, 0)
    data['Asset_Returns'] = data['Close'].pct_change()
    
    # --- CRÍTICO: EVITANDO LOOK-AHEAD BIAS ---
    data['Strategy_Returns'] = data['Signal'].shift(1) * data['Asset_Returns']
    
    return data[['Close', 'Signal', 'Strategy_Returns', 'SMA_Short', 'SMA_Long']]

def print_metrics_report(title, metrics):
    """
    Imprime um relatório formatado das métricas.
    """
    print(f"\n{'='*40}")
    print(f" {title.upper()} ")
    print(f"{'='*40}")
    for key, value in metrics.items():
        if "Ratio" in key:
            print(f"{key:.<25} {value:.2f}")
        else:
            print(f"{key:.<25} {value:.2%}")
    print(f"{'='*40}")

if __name__ == "__main__":
    ticker = "PETR4.SA"
    
    try:
        # 1. Coleta de Dados
        df_full = get_data(ticker)
        
        # 2. Divisão In-Sample (70%) e Out-of-Sample (30%)
        split_idx = int(len(df_full) * 0.7)
        df_in_sample = df_full.iloc[:split_idx].copy()
        df_out_of_sample = df_full.iloc[split_idx:].copy()
        
        print(f"\n--- Divisão de Dados ---")
        print(f"Total: {len(df_full)} dias")
        print(f"In-Sample (Treino): {len(df_in_sample)} dias")
        print(f"Out-of-Sample (Teste): {len(df_out_of_sample)} dias")
        
        # 3. Execução In-Sample
        res_in = strategy_sma_crossover(df_in_sample)
        metrics_in = calculate_metrics(res_in['Strategy_Returns'])
        
        # 4. Execução Out-of-Sample
        res_out = strategy_sma_crossover(df_out_of_sample)
        metrics_out = calculate_metrics(res_out['Strategy_Returns'])
        
        # 5. Relatórios
        print_metrics_report("Métricas SMA: In-Sample", metrics_in)
        print_metrics_report("Métricas SMA: Out-of-Sample", metrics_out)
        
    except Exception as e:
        print(f"\n[ERRO]: {e}")
