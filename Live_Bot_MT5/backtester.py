import pandas as pd
import numpy as np

def calculate_metrics_advanced(returns, periods_per_year=252*24):
    """
    Calcula métricas avançadas para preencher a tabela:
    Retorno Total, CAGR, Sharpe, Volatilidade, Max Drawdown
    periods_per_year é uma estimativa para anualização (ex: M60=252*8, D1=252)
    Para simplicidade em candles variados, vamos tentar inferir ou usar um padrão.
    """
    returns = returns.dropna()
    if returns.empty:
        return {
            "total_return": 0, "cagr": 0, "sharpe": 0, "volatility": 0, "max_drawdown": 0
        }

    # 1. Retorno Total
    cumulative = (1 + returns).cumprod()
    total_return = cumulative.iloc[-1] - 1
    
    # 2. Volatilidade (Anualizada aprox)
    # Assumindo que o backtest enviará dados 'diarizados' ou nós apenas multiplicamos
    # por raiz de 252 (se D1) ou outro fator. Aqui vamos retornar a volatilidade "do período" 
    # e o front que lide com labels ou fixar um fator arbitrario para "Sharpe Anualizado"
    # Vamos usar sqrt(252) como padrão de mercado se não soubermos a freq.
    volatility = returns.std() * np.sqrt(periods_per_year) 
    
    # CAGR Logic Removed as requested
    
    # 4. Sharpe
    mean_ret = returns.mean() * periods_per_year
    sharpe = mean_ret / volatility if volatility != 0 else 0
    
    # 5. Max Drawdown
    peak = cumulative.cummax()
    dd = (cumulative - peak) / peak
    max_dd = dd.min()
    
    return {
        "total_return": total_return,
        "sharpe": sharpe,
        "volatility": volatility,
        "max_drawdown": max_dd
    }

def calculate_trade_stats(df):
    df = df.copy()
    df['trade_signal'] = df['Signal'].diff().fillna(0)
    
    entries = df[df['trade_signal'] == 1]
    exits = df[df['trade_signal'] == -1]
    
    if not entries.empty and not exits.empty:
        if exits.index[0] < entries.index[0]:
            exits = exits.iloc[1:]
    
    n_trades = min(len(entries), len(exits))
    trades = []
    
    for i in range(n_trades):
        en_row = entries.iloc[i]
        ex_row = exits.iloc[i]
        
        en_price = en_row['close']
        ex_price = ex_row['close']
        ret = (ex_price / en_price) - 1
        
        # Duração em Horas (aproximado se Timedelta)
        duration_val = 0
        try:
             diff = ex_row['time'] - en_row['time']
             duration_val = diff.total_seconds() / 3600 # horas
        except:
             pass
             
        trades.append({
            "return": ret,
            "duration": duration_val
        })
        
    if not trades:
        return {
            "total_trades": 0, "win_rate": 0, "avg_return": 0, 
            "avg_duration": 0, "profit_factor": 0
        }
        
    df_trades = pd.DataFrame(trades)
    wins = df_trades[df_trades['return'] > 0]
    losses = df_trades[df_trades['return'] <= 0]
    
    win_rate = len(wins) / len(df_trades)
    avg_return = df_trades['return'].mean()
    avg_duration = df_trades['duration'].mean()/24 # Dias
    
    gross_profit = wins['return'].sum()
    gross_loss = abs(losses['return'].sum())
    profit_factor = gross_profit / gross_loss if gross_loss != 0 else 999.0
    
    return {
        "total_trades": len(df_trades),
        "win_rate": win_rate,
        "avg_return": avg_return,
        "avg_duration": avg_duration, # em dias
        "profit_factor": profit_factor
    }

def strategy_sma_crossover(df, short_window=20, long_window=50):
    """
    Estratégia SMA Crossover adaptada para DataFrame MT5 (lowercase columns).
    """
    data = df.copy()
    
    # Garantir que temos close
    if 'close' not in data.columns:
        raise ValueError("DataFrame deve conter coluna 'close'")
        
    data['SMA_Short'] = data['close'].rolling(window=short_window).mean()
    data['SMA_Long'] = data['close'].rolling(window=long_window).mean()
    
    # 1 = Comprado, 0 = Neutro
    data['Signal'] = np.where(data['SMA_Short'] > data['SMA_Long'], 1, 0)
    
    data['Returns'] = data['close'].pct_change()
    
    # Shift no sinal para evitar look-ahead bias
    # Se sinal deu 1 no fechamento de T, entramos na abertura de T+1 e pegamos o retorno de T+1
    # Ou, simplificando: retorno do dia T+1 é Returns[T+1] * Signal[T]
    data['Strategy_Returns'] = data['Signal'].shift(1) * data['Returns']
    
    return data
