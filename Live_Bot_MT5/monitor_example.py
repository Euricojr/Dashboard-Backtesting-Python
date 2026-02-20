import time
import pandas as pd
import MetaTrader5 as mt5
from datetime import datetime
from utils.telegram_notifier import TelegramNotifier

import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env (se existir)
load_dotenv()

# --- CONFIGURAÇÃO ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SYMBOL = "WINJ26"
TIMEFRAME = mt5.TIMEFRAME_M5
SHORT_WINDOW = 20
LONG_WINDOW = 50

# Estado para evitar repetição de mensagens no mesmo cruzamento
# 0 = Neutro, 1 = Comprado (Golden Cross emitido), -1 = Vendido (Death Cross emitido)
LAST_SIGNAL_STATE = 0 

def ensure_mt5_connected():
    if not mt5.initialize():
        print("Erro ao inicializar MT5:", mt5.last_error())
        return False
    return True

def get_data(symbol, timeframe, count=200):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None or len(rates) == 0:
        return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def calculate_sma(df, short_window, long_window):
    df['SMA_Short'] = df['close'].rolling(window=short_window).mean()
    df['SMA_Long'] = df['close'].rolling(window=long_window).mean()
    return df

def check_crossover(df):
    global LAST_SIGNAL_STATE
    
    # Precisamos de pelo menos 2 linhas com médias calculadas
    if len(df) < 2:
        return None

    # Pegamos os dois ultimos registros COMPLETOS (excluindo a vela em formação se quisermos ser conservadores)
    # Mas o requisito diz "em tempo real" ou "fechamento". 
    # Para tempo real, pegamos last e penultima.
    
    current = df.iloc[-1]
    prev = df.iloc[-2]
    
    c_short = current['SMA_Short']
    c_long = current['SMA_Long']
    p_short = prev['SMA_Short']
    p_long = prev['SMA_Long']
    
    if pd.isna(c_short) or pd.isna(c_long) or pd.isna(p_short) or pd.isna(p_long):
        return None

    signal_text = None
    new_state = LAST_SIGNAL_STATE
    
    # Golden Cross: Curta cruza Longa para CIMA
    if p_short <= p_long and c_short > c_long:
        if LAST_SIGNAL_STATE != 1: # Só avisa se não estava "Comprado"
            signal_text = "COMPRA (Golden Cross)"
            new_state = 1
            
    # Death Cross: Curta cruza Longa para BAIXO
    elif p_short >= p_long and c_short < c_long:
        if LAST_SIGNAL_STATE != -1: # Só avisa se não estava "Vendido"
            signal_text = "VENDA (Death Cross)"
            new_state = -1

    if signal_text:
        LAST_SIGNAL_STATE = new_state
        return {
            "sinal": signal_text,
            "preco": current['close'],
            "time": current['time']
        }
    
    return None

def main():
    notifier = TelegramNotifier(token=TELEGRAM_TOKEN, chat_id=TELEGRAM_CHAT_ID)
    
    if not ensure_mt5_connected():
        return

    print(f"🚀 Iniciando Monitoramento de {SYMBOL}...")
    print("Pressione Ctrl+C para parar.")

    try:
        while True:
            df = get_data(SYMBOL, TIMEFRAME)
            
            if df is not None:
                df = calculate_sma(df, SHORT_WINDOW, LONG_WINDOW)
                alert = check_crossover(df)
                
                if alert:
                    msg = (
                        f"🚀 **ALERTA FINSENSE** 🚀\n"
                        f"Ativo: {SYMBOL}\n"
                        f"Sinal: {alert['sinal']}\n"
                        f"Preço: {alert['preco']:.3f}\n"
                        f"Horário: {alert['time'].strftime('%H:%M')}"
                    )
                    print(f"\n⚡ ALERTA DETECTADO: {msg}")
                    notifier.enviar_mensagem(msg)
                
                # Feedback visual simples no console
                latest = df.iloc[-1]
                print(f"\r[{datetime.now().strftime('%H:%M:%S')}] {SYMBOL} Close: {latest['close']:.2f} | S:{latest['SMA_Short']:.2f} | L:{latest['SMA_Long']:.2f}", end="")
            
            time.sleep(5) # Aguarda 5 segundos antes da proxima verificação

    except KeyboardInterrupt:
        print("\n🛑 Monitoramento encerrado pelo usuário.")
        mt5.shutdown()

if __name__ == "__main__":
    main()
