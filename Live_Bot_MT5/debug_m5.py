import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import json

def ensure_mt5_connected():
    if mt5.initialize():
        return True, ""
    return False, mt5.last_error()

connected, err = ensure_mt5_connected()
if not connected:
    print(f"Error: {err}")
    exit()

symbol = 'WINJ26'
mt5.symbol_select(symbol, True)

tf_str = 'M5'
timeframe = mt5.TIMEFRAME_M5

rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 5000)
df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s')

print(f"Total candles fetched: {len(df)}")

df['EMA9'] = df['close'].ewm(span=9, adjust=False).mean()
df['EMA21'] = df['close'].ewm(span=21, adjust=False).mean()

df['date'] = df['time'].dt.date
df['Typical_Price'] = (df['high'] + df['low'] + df['close']) / 3
df['Vol_x_TP'] = df['tick_volume'] * df['Typical_Price']

df['Cum_Vol_x_TP'] = df.groupby('date')['Vol_x_TP'].cumsum()
df['Cum_Vol'] = df.groupby('date')['tick_volume'].cumsum()
df['VWAP'] = df['Cum_Vol_x_TP'] / df['Cum_Vol']

in_position = False
trade_type = None 
entry_price = 0.0

total_trades = 0

from datetime import time as dt_time
hora_inicio = dt_time(9, 15)
hora_fim = dt_time(12, 30)

for i in range(2, len(df)):
    row = df.iloc[i]
    if in_position:
        high = row['high']
        low = row['low']
        closed_trade = False
        
        if trade_type == 'BUY':
            if low <= entry_price - 100.0:
                closed_trade = True
            elif high >= entry_price + 200.0:
                closed_trade = True
                
        elif trade_type == 'SELL':
            if high >= entry_price + 100.0:
                closed_trade = True
            elif low <= entry_price - 200.0:
                closed_trade = True
                
        if closed_trade:
            in_position = False
            total_trades += 1
        continue 
        
    hora_atual = row['time'].time()
    
    if hora_inicio <= hora_atual <= hora_fim:
        current_closed = df.iloc[i-1]
        prev_closed = df.iloc[i-2]
        
        c_ema9 = current_closed['EMA9']
        c_ema21 = current_closed['EMA21']
        p_ema9 = prev_closed['EMA9']
        p_ema21 = prev_closed['EMA21']
        
        c_close = current_closed['close']
        c_vwap = current_closed['VWAP']
        
        cross_up = (p_ema9 <= p_ema21) and (c_ema9 > c_ema21)
        cross_down = (p_ema9 >= p_ema21) and (c_ema9 < c_ema21)
        
        if cross_up and c_close > c_vwap:
            in_position = True
            trade_type = 'BUY'
            entry_price = row['open']
        elif cross_down and c_close < c_vwap:
            in_position = True
            trade_type = 'SELL'
            entry_price = row['open']

print(f"Total trades for {tf_str}: {total_trades}")
