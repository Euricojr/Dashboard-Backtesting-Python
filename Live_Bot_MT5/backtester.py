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
    if cumulative.empty:
         total_return = 0
    else:
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
    if 'Signal' not in df.columns:
         return {
            "total_trades": 0, "win_rate": 0, "avg_return": 0, 
            "avg_duration": 0, "profit_factor": 0
        }

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
             
        # Formata as datas para envio fácil no JSON
        try:
            en_time_str = en_row['time'].strftime('%d/%m/%Y %H:%M')
            ex_time_str = ex_row['time'].strftime('%d/%m/%Y %H:%M')
        except:
            en_time_str = str(en_row['time'])
            ex_time_str = str(ex_row['time'])
             
        trades.append({
            "return": ret,
            "duration": duration_val,
            "entry_time": en_time_str,
            "exit_time": ex_time_str,
            "entry_price": en_price,
            "exit_price": ex_price,
            "type": "COMPRA"
        })
        
    if not trades:
        return {
            "total_trades": 0, "win_rate": 0, "avg_return": 0, 
            "avg_duration": 0, "profit_factor": 0, "trades": []
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
        "profit_factor": profit_factor,
        "trades": trades
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

def optimize_sma(df):
    """
    Otimiza os parâmetros de Média Móvel (Curta e Longa) buscando o maior Profit Factor.
    Versão Otimizada (Fast Numpy).
    """
    # Converter para numpy para velocidade extrema
    prices = df['close'].values
    
    # Ranges
    short_range = range(5, 25, 2)
    long_range = range(30, 105, 5)
    
    best_score = -1
    best_params = (20, 50)
    
    # Pre-cálculo de retornos %
    # ret[i] = (price[i] - price[i-1]) / price[i-1]
    # Usamos numpy diff
    returns = np.diff(prices) / prices[:-1]
    returns = np.insert(returns, 0, 0) # align with prices length
    
    for short in short_range:
        # Calcular SMA Curta uma vez para todos os Longs compatíveis? 
        # Não, pois muda a cada iteração. Mas pandas rolling é rápido.
        # Para ultra performance, poderiamos usar convolution, mas rolling do pandas já é C-optimized.
        # Vamos apenas evitar criar DataFrames inteiros.
        
        sma_short = pd.Series(prices).rolling(short).mean().values
        
        for long in long_range:
            if short >= long:
                continue
                
            sma_long = pd.Series(prices).rolling(long).mean().values
            
            # Signal: 1 se Short > Long, 0 caso contrario
            # Usamos np.nan_to_num para lidar com os nans iniciais do rolling
            signals = np.where(np.nan_to_num(sma_short) > np.nan_to_num(sma_long), 1, 0)
            
            # Strategy Returns = Signal[t-1] * Returns[t]
            # Shift signals forward by 1
            shifted_signals = np.roll(signals, 1)
            shifted_signals[0] = 0
            
            # Vectorized Returns
            strat_rets = shifted_signals * returns
            
            # Fast Profit Factor Calculation (Vectorized)
            wins = strat_rets[strat_rets > 0].sum()
            losses = abs(strat_rets[strat_rets < 0].sum())
            
            # Se não operou, PF = 0
            if losses == 0:
                if wins > 0: pf = 100.0 # Infinite profit
                else: pf = 0.0
            else:
                pf = wins / losses
                
            if pf > best_score:
                best_score = pf
                best_params = (short, long)
                
    return best_params

def backtest_scalper_engine(df, sl_manual=150.0, tp_manual=300.0, start_time="09:15", end_time="17:00"):
    """
    Engine de Simulação Iterativa Strict (Non-Vectorized)
    Controla posições abertas, stops diários e filtros de horário dinâmicos.
    Requer que o DataFrame de entrada já contenha: 'EMA9', 'SMA21', 'VWAP', 'date' e 'time_only'.
    """
    from datetime import datetime
    t_start = datetime.strptime(start_time, "%H:%M").time()
    t_end = datetime.strptime(end_time, "%H:%M").time()
    
    # Prepara coluna para sinais no grid se não existir
    if 'trade_signal' not in df.columns:
        df['trade_signal'] = None

    in_position = False
    trade_type = None
    entry_price = 0.0
    cooldown_until = None
    
    total_trades = 0
    win_count = 0
    total_profit_pts = 0.0
    
    peak_rs = 0.0
    max_drawdown_rs = 0.0
    
    current_trade_date = None
    trades_today = 0
    entry_index = 0
    
    for i in range(2, len(df)):
        row = df.iloc[i]
        
        row_date = row['date']
        if current_trade_date != row_date:
            current_trade_date = row_date
            trades_today = 0
        
        if in_position:
            high = row['high']
            low = row['low']
            closed_trade = False
            profit_pts = 0.0
            
            if trade_type == 'BUY':
                if low <= entry_price - sl_manual:
                    profit_pts = -sl_manual
                    closed_trade = True
                    df.at[df.index[i], 'trade_signal'] = 'LOSS_BUY'
                elif high >= entry_price + tp_manual:
                    profit_pts = tp_manual
                    closed_trade = True
                    df.at[df.index[i], 'trade_signal'] = 'WIN_BUY'
            
            elif trade_type == 'SELL':
                if high >= entry_price + sl_manual:
                    profit_pts = -sl_manual
                    closed_trade = True
                    df.at[df.index[i], 'trade_signal'] = 'LOSS_SELL'
                elif low <= entry_price - tp_manual:
                    profit_pts = tp_manual
                    closed_trade = True
                    df.at[df.index[i], 'trade_signal'] = 'WIN_SELL'
                    
            if closed_trade:
                in_position = False
                total_trades += 1
                if profit_pts > 0:
                    win_count += 1
                
                total_profit_pts += profit_pts
                
                # Avalia Drawdown cumulativo (R$ 0.20 por ponto de WIN)
                current_balance_rs = total_profit_pts * 0.20
                if current_balance_rs > peak_rs:
                    peak_rs = current_balance_rs
                
                dd = peak_rs - current_balance_rs
                if dd > max_drawdown_rs:
                    max_drawdown_rs = dd
                    # Cooldown removido a pedido do usuario
            continue 
            
        hora_atual = row['time_only']
        # Filtro de Cooldown removido
        
        # Filtro de Atraso e Janela Otimizada (Condição Principal Refatorada)
        if t_start <= hora_atual <= t_end:
            current_closed = df.iloc[i-1]
            prev_closed = df.iloc[i-2]
            
            c_ema9 = current_closed['EMA9']
            c_sma21 = current_closed['SMA21']
            p_ema9 = prev_closed['EMA9']
            p_sma21 = prev_closed['SMA21']
            
            c_close = current_closed['close']
            c_vwap = current_closed['VWAP']
            
            cross_up = (p_ema9 <= p_sma21) and (c_ema9 > c_sma21)
            cross_down = (p_ema9 >= p_sma21) and (c_ema9 < c_sma21)
            
            if cross_up and c_close > c_vwap:
                in_position = True
                trade_type = 'BUY'
                entry_price = row['open']  # Entrada na abertura atual realista
                entry_index = i
                trades_today += 1
                df.at[df.index[i], 'trade_signal'] = 'BUY'

            elif cross_down and c_close < c_vwap:
                in_position = True
                trade_type = 'SELL'
                entry_price = row['open']
                entry_index = i
                trades_today += 1
                df.at[df.index[i], 'trade_signal'] = 'SELL'

    lucro_total_rs = total_profit_pts * 0.20
    winrate = (win_count / total_trades * 100) if total_trades > 0 else 0.0
    
    return {
        "start_time": start_time,
        "end_time": end_time,
        "total_trades": total_trades,
        "winrate": winrate,
        "lucro_total_rs": lucro_total_rs,
        "max_drawdown_rs": max_drawdown_rs,
    }
