import time
import json
import os
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta, time as dt_time
from dotenv import load_dotenv

# Importa o notificador do Telegram do seu utils
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.telegram_notifier import TelegramNotifier

load_dotenv()

# Instância do Telegram global para o Scalper
telegram_bot = TelegramNotifier()

CONTROLE_FILE = "controle_scalper.json"
SYMBOL = "WINJ26" # Ajuste para o contrato vigente do momento
TIMEFRAME = mt5.TIMEFRAME_M5
VOLUME = 1.0
SL_POINTS = 100.0
TP_POINTS = 200.0  
MAGIC_NUMBER = 777777 # Magic exclusivo para isolar as negociações do Scalper
MAX_TRADES_DIA = 3

# Filtro de Horário (Golden Zone)
HORA_INICIO = dt_time(9, 15)
HORA_FIM = dt_time(12, 30)

def load_controle():
    if not os.path.exists(CONTROLE_FILE):
        return {"status": "OFF", "trades_hoje": 0, "lucro_hoje": 0.0, "data": datetime.now().strftime('%Y-%m-%d')}
    
    try:
        with open(CONTROLE_FILE, "r") as f:
            data = json.load(f)
            hoje_str = datetime.now().strftime('%Y-%m-%d')
            # Reset diário dos lucros e trades se virou o dia
            if data.get("data") != hoje_str:
                data["trades_hoje"] = 0
                data["lucro_hoje"] = 0.0
                data["data"] = hoje_str
                save_controle(data)
            return data
    except Exception:
        return {"status": "OFF", "trades_hoje": 0, "lucro_hoje": 0.0, "data": datetime.now().strftime('%Y-%m-%d')}

def save_controle(data):
    with open(CONTROLE_FILE, "w") as f:
        json.dump(data, f, indent=4)

def ensure_mt5_connection():
    if not mt5.terminal_info():
        mt5.initialize(login=int(os.getenv("XP_DEMO_LOGIN", 0)), 
                       password=os.getenv("XP_DEMO_PASSWORD", ""), 
                       server="XPMT5-DEMO")
        
def wait_position_close(ticket, entrada_info):
    """Fica em loop até o SL ou TP bater na corretora e fechar a posição"""
    print(f"⏳ Aguardando fechamento da posição (Ticket: {ticket})...")
    
    hora_entrada = entrada_info['hora_entrada']
    
    while True:
        pos = mt5.positions_get(ticket=ticket)
        if pos is None or len(pos) == 0:
            break
        time.sleep(2)
        
    hora_saida = datetime.now()
    duracao = hora_saida - hora_entrada
    minutos, segundos = divmod(duracao.total_seconds(), 60)
        
    print("🏁 Posição Encerrada! Compilando resultado...")
    time.sleep(2) # Buffer para o MT5 atualizar o History
    
    hoje = datetime.now().replace(hour=0, minute=0, second=0)
    deals = mt5.history_deals_get(hoje, datetime.now() + timedelta(days=1))
    lucro = 0.0
    
    if deals:
        for deal in deals:
            # deal.entry == 1 (DEAL_ENTRY_OUT) significa que foi negócio de saída (fechamento)
            if deal.position_id == ticket and getattr(deal, 'entry', 0) == 1:
                lucro += deal.profit
                
    # Atualiza JSON
    data = load_controle()
    data["trades_hoje"] += 1
    data["lucro_hoje"] += lucro
    save_controle(data)
    
    resultado_str = "🟢 GAIN" if lucro > 0 else "🔴 LOSS"
    direcao_str = "COMPRA" if entrada_info['direcao'] == mt5.ORDER_TYPE_BUY else "VENDA"
    pontos_estimados = abs(lucro) / 0.20 # 1 contrato WIN = R$ 0,20 por ponto
    
    msg_telegram = (
        f"🧾 *RAIO-X DA OPERAÇÃO | {SYMBOL}*\n"
        f"🧭 Direção: *{direcao_str}*\n"
        f"⏰ Duração: {int(minutos)}m e {int(segundos)}s\n\n"
        f"� *MOTIVO DA ENTRADA:*\n"
        f"• Gatilho: {entrada_info['preco']}\n"
        f"• EMA 9: {entrada_info['ema9']:.2f} | EMA 21: {entrada_info['ema21']:.2f}\n"
        f"• VWAP: {entrada_info['vwap']:.2f}\n\n"
        f"�💰 *RESULTADO FINAL:*\n"
        f"{resultado_str} de R$ {lucro:.2f} ({int(pontos_estimados)} pts)\n"
        f"📉 Status Dia: {data['trades_hoje']} trades (R$ {data['lucro_hoje']:.2f})"
    )
    
    print(f"💰 Trade fechado. Lucro/Prejuízo: R$ {lucro:.2f}")
    telegram_bot.enviar_mensagem(msg_telegram)

def iniciar_robo():
    ensure_mt5_connection()
    print("🤖 Robô Scalper WIN Inicializado. Lendo Regra de Ouro...")
    
    ultima_vela_operada = None
    
    while True:
        # 1. Regra de Ouro: Ler status antes de tudo
        controle = load_controle()
        
        if controle["trades_hoje"] >= MAX_TRADES_DIA:
            time.sleep(60)
            continue

        if controle["status"] == "OFF":
            # Sleep longo e PULA para reavaliar no proximo tick
            time.sleep(5)
            continue
            
        hora_atual = datetime.now().time()
        if hora_atual < HORA_INICIO or hora_atual > HORA_FIM:
            print(f"⏳ Fora da janela operacional ({HORA_INICIO.strftime('%H:%M')} - {HORA_FIM.strftime('%H:%M')}). A aguardar...")
            time.sleep(60)
            continue

        # 2. Status é ON. Seguir com análise
        ensure_mt5_connection()
        rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 300)
        if rates is None or len(rates) < 50:
            time.sleep(5)
            continue
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        # Filtro de VWAP (só pega volume do dia de hoje para ser fidedigno)
        start_hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        df_hoje = df[df['time'] >= start_hoje].copy()
        if not df_hoje.empty:
            df_hoje['Typical_Price'] = (df_hoje['high'] + df_hoje['low'] + df_hoje['close']) / 3
            df_hoje['Vol_x_TP'] = df_hoje['tick_volume'] * df_hoje['Typical_Price']
            df_hoje['Cum_Vol_x_TP'] = df_hoje['Vol_x_TP'].cumsum()
            df_hoje['Cum_Vol'] = df_hoje['tick_volume'].cumsum()
            df_hoje['VWAP'] = df_hoje['Cum_Vol_x_TP'] / df_hoje['Cum_Vol']
            df['VWAP'] = df_hoje['VWAP']
        else:
            df['VWAP'] = df['close']

        # Calculo das Médias (EMA 9 e SMA 21 para consistência)
        df['EMA9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['SMA21'] = df['close'].rolling(window=21).mean()
        
        # Analisa a última vela fechada para evitar a "Síndrome da Vela Aberta"
        current = df.iloc[-2]
        prev = df.iloc[-3]
        
        vela_time = current['time']
        
        # Lógicas de Cruzamento (Compra e Venda)
        cross_up = prev['EMA9'] <= prev['SMA21'] and current['EMA9'] > current['SMA21']
        cross_down = prev['EMA9'] >= prev['SMA21'] and current['EMA9'] < current['SMA21']
        
        # Só opera essa vela 1 vez
        if vela_time != ultima_vela_operada:
            action = None
            
            # Sinal de COMPRA: EMA9 passa pra cima E o preço atual está acima do VWAP
            if cross_up and current['close'] > current['VWAP']:
                action = mt5.ORDER_TYPE_BUY
            # Sinal de VENDA: EMA9 passa pra baixo E o preço atual está abaixo do VWAP
            elif cross_down and current['close'] < current['VWAP']:
                action = mt5.ORDER_TYPE_SELL
                
            if action is not None:
                ultima_vela_operada = vela_time
                if action == mt5.ORDER_TYPE_BUY:
                    price = mt5.symbol_info_tick(SYMBOL).ask
                    sl = price - SL_POINTS
                    tp = price + TP_POINTS
                    msg_label = "COMPRA"
                else: # SELL
                    price = mt5.symbol_info_tick(SYMBOL).bid
                    sl = price + SL_POINTS
                    tp = price - TP_POINTS
                    msg_label = "VENDA"
                
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": SYMBOL,
                    "volume": float(VOLUME),
                    "type": action,
                    "price": price,
                    "sl": float(sl),
                    "tp": float(tp),
                    "deviation": 20,
                    "magic": MAGIC_NUMBER,
                    "comment": "ScalperWIN_Auto",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_RETURN, # Comum B3
                }
                
                print(f"📩 Enviando Ordem OCO: {msg_label} | Price: {price} | SL: {sl} | TP: {tp}")
                res = mt5.order_send(request)
                if res.retcode == mt5.TRADE_RETCODE_DONE:
                    # Montando pacote de dados pro Raio-X
                    entrada_info = {
                        "hora_entrada": datetime.now(),
                        "direcao": action,
                        "preco": price,
                        "ema9": current['EMA9'],
                        "sma21": current['SMA21'],
                        "vwap": current['VWAP']
                    }
                    wait_position_close(res.order, entrada_info)
                else:
                    print(f"❌ Erro na Ordem: {res.comment}")
        
        time.sleep(3) # Pausa pequena no meio da vela atual para não causar CPU estresse (~Tick loop)

if __name__ == "__main__":
    iniciar_robo()
