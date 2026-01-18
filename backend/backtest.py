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

def calculate_trade_stats(df_result):
    """
    Calcula estatísticas de trades baseados na coluna 'Signal'.
    """
    trades = []
    
    # Identificar mudanças de sinal
    # 1 -> Compra (Entrada Long ou Saída Short)
    # 0 -> Venda (Saída Long ou Entrada Short) - Simplificação: Long Only
    # Vamos assumir Long Only: 1 = Comprado, 0 = Vendido (Neutro)
    
    in_trade = False
    entry_price = 0
    entry_date = None
    
    # Iterar sobre o DF (pode ser lento se muito grande, mas para daily data ok)
    # O 'Signal' indica o estado para o DIA SEGUINTE.
    # Se Signal[i] == 1, estaremos comprados em i+1.
    
    # Melhor abordagem: Detectar diff do sinal
    # Se diff == 1 (0 -> 1): Compra no Close do dia (ou Open do proximo)
    # Vamos assumir simplificado: Compra no Close do dia que deu sinal
    
    df = df_result.copy()
    # Garantir datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
         # Tentar converter ou assumir numérico
         pass

    # Lógica Simplificada Long-Only
    # Compra quando Signal passa de 0 para 1
    # Venda quando Signal passa de 1 para 0
    
    # Shift para alinhar: Se Signal[t] = 1, então em t+1 estamos expostos.
    # Mas o backtest já calcula Strategy_Returns baseado nisso.
    # Vamos olhar os trades "teóricos".
    
    # Pegar apenas as transições
    df['trade_signal'] = df['Signal'].diff().fillna(0)
    
    entries = df[df['trade_signal'] == 1]
    exits = df[df['trade_signal'] == -1]
    
    # Alinhamento simples (FIFO)
    # Se o primeiro for exit, ignorar
    if not entries.empty and not exits.empty:
        if exits.index[0] < entries.index[0]:
            exits = exits.iloc[1:]
            
    # Parear
    n_trades = min(len(entries), len(exits))
    
    stats_trades = []
    
    for i in range(n_trades):
        en_date = entries.index[i]
        ex_date = exits.index[i]
        
        en_price = entries.loc[en_date, 'Close']
        ex_price = exits.loc[ex_date, 'Close']
        
        ret = (ex_price / en_price) - 1
        duration = (ex_date - en_date).days
        
        stats_trades.append({
            "entry_date": en_date,
            "exit_date": ex_date,
            "return": ret,
            "duration": duration
        })
        
    # Calcular Métricas Agregadas
    if not stats_trades:
        return {
            "total_trades": 0,
            "win_rate": 0.0,
            "avg_return": 0.0,
            "avg_duration": 0.0,
            "profit_factor": 0.0
        }
        
    df_trades = pd.DataFrame(stats_trades)
    
    wins = df_trades[df_trades['return'] > 0]
    losses = df_trades[df_trades['return'] <= 0]
    
    win_rate = len(wins) / len(df_trades)
    avg_return = df_trades['return'].mean()
    avg_duration = df_trades['duration'].mean()
    
    gross_profit = wins['return'].sum()
    gross_loss = abs(losses['return'].sum())
    profit_factor = gross_profit / gross_loss if gross_loss != 0 else 999.0
    
    return {
        "total_trades": len(df_trades),
        "win_rate": win_rate,
        "avg_return": avg_return,
        "avg_duration": avg_duration,
        "profit_factor": profit_factor
    }

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
    print(f"[DEBUG] Weekly RSI Count (Not NaN): {df_weekly['RSI'].count()}")
    print(f"[DEBUG] Weekly RSI Head: {df_weekly['RSI'].head(20).tolist()}")
    
    # Passo C: Sinais Semanais
    # 1 = Compra, 0 = Venda, NaN = Manter
    df_weekly['Signal_Weekly'] = np.nan
    df_weekly.loc[df_weekly['RSI'] < lower, 'Signal_Weekly'] = 1
    df_weekly.loc[df_weekly['RSI'] > upper, 'Signal_Weekly'] = 0
    
    print(f"[DEBUG] Signals before ffill: {df_weekly['Signal_Weekly'].value_counts(dropna=False)}")

    # --- CORREÇÃO IMPORTANTE ---
    # Propagar o último sinal válido para as semanas seguintes (State Machine)
    # Se não fizer isso, quando o RSI ficar "neutro" (entre 35 e 70), a posição zera (NaN virava 0)
    df_weekly['Signal_Weekly'] = df_weekly['Signal_Weekly'].ffill()
    
    print(f"[DEBUG] Signals after ffill: {df_weekly['Signal_Weekly'].value_counts(dropna=False)}")

    # Passo D: Merge (Joga sinais semanais volta para diário)
    # Reindex com method='ffill' para buscar o valor da semana anterior (Sunday -> Monday/etc)
    daily_signals = df_weekly['Signal_Weekly'].reindex(df.index, method='ffill')
    daily_rsi = df_weekly['RSI'].reindex(df.index, method='ffill')
    
    print(f"[DEBUG] Daily Signals Count: {daily_signals.count()}")
    
    # Prepara DataFrame de saída
    data = df.copy()
    data['Signal'] = daily_signals
    data['RSI'] = daily_rsi
    
    # Preenche NaNs iniciais com 0 ou mantém (se ffill não cobrir o início) -> assumimos flat (0)
    data['Signal'] = data['Signal'].fillna(0)
    
    data['Asset_Returns'] = data['Close'].pct_change()
    
    # Passo E: Viés (Trade no dia seguinte ao sinal)
    data['Strategy_Returns'] = data['Signal'].shift(1) * data['Asset_Returns']
    
    return data[['Close', 'Signal', 'Strategy_Returns', 'RSI']]

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
        
        # 2. Divisão In-Sample (50%) e Out-of-Sample (50%)
        split_idx = int(len(df_full) * 0.5)
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
