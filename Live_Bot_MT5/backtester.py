import pandas as pd
import numpy as np

def calculate_metrics(returns):
    """
    Calcula métricas de performance para uma série de retornos.
    Adaptação para intraday. Assume-se que 'returns' é percentual p/ período.
    Para anualizar (CAGR/Vol), precisamos saber a frequência.
    Para simplificar, vamos retornar métricas absolutas e Sharpe "simples" ou anualizado aproximado.
    """
    returns = returns.dropna()
    if returns.empty:
        return {
            "Total Return": 0, "Sharpe Ratio": 0, "Max Drawdown": 0, "Win Rate": 0
        }

    # 1. Retorno Total
    cumulative_series = (1 + returns).cumprod()
    total_return = cumulative_series.iloc[-1] - 1
    
    # 2. Sharpe Ratio (Simplificado, considerando risk-free=0)
    # Para anualizar intraday é complexo sem saber datas exatas, 
    # então usamos Sharpe por barra multiplicado por raiz de (barras/ano) ou apenas mean/std
    # Vamos retornar média/std por enquanto (Sharpe por Trade/Barra)
    mean_ret = returns.mean()
    std_ret = returns.std()
    sharpe = mean_ret / std_ret if std_ret != 0 else 0
    
    # 3. Max Drawdown
    peak = cumulative_series.cummax()
    drawdown = (cumulative_series - peak) / peak
    max_drawdown = drawdown.min()
    
    return {
        "Total Return": total_return,
        "Sharpe Ratio (per bar)": sharpe,
        "Max Drawdown": max_drawdown
    }

def calculate_trade_stats(df):
    """
    Gera lista de trades e estatísticas baseadas na coluna 'Signal'.
    Assume que df tem coluna 'time' (datetime) e 'close'.
    """
    df = df.copy()
    
    # Detectar transições de sinal
    # Signal: 1 (Comprado), 0 (Neutro)
    # Mudança 0->1: Compra
    # Mudança 1->0: Venda
    df['trade_signal'] = df['Signal'].diff().fillna(0)
    
    entries = df[df['trade_signal'] == 1]
    exits = df[df['trade_signal'] == -1]
    
    # Alinhamento FIFO
    if not entries.empty and not exits.empty:
        if exits.index[0] < entries.index[0]:
            exits = exits.iloc[1:]
    
    n_trades = min(len(entries), len(exits))
    trades = []
    
    for i in range(n_trades):
        # Usando .iloc[i] para acessar pela posição
        en_row = entries.iloc[i]
        ex_row = exits.iloc[i]
        
        en_price = en_row['close']
        ex_price = ex_row['close']
        
        # Retorno do trade
        ret = (ex_price / en_price) - 1
        
        # Duração
        try:
            duration = ex_row['time'] - en_row['time']
        except:
             duration = 0
             
        trades.append({
            "entry_time": en_row['time'], # Pode ser timestamp ou datetime
            "exit_time": ex_row['time'],
            "entry_price": en_price,
            "exit_price": ex_price,
            "return": ret,
            "type": "Long" # Assumindo Long-Only
        })
        
    if not trades:
        return {"total_trades": 0, "win_rate": 0, "profit_factor": 0, "trades_list": []}
        
    df_trades = pd.DataFrame(trades)
    wins = df_trades[df_trades['return'] > 0]
    losses = df_trades[df_trades['return'] <= 0]
    
    win_rate = len(wins) / len(df_trades)
    
    gross_profit = wins['return'].sum()
    gross_loss = abs(losses['return'].sum())
    profit_factor = gross_profit / gross_loss if gross_loss != 0 else 999.0
    
    return {
        "total_trades": len(df_trades),
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "trades_list": trades
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
