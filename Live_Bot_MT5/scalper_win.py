import time
import json
import os
import MetaTrader5 as mt5
import pandas as pd
import csv
from datetime import datetime, timedelta, time as dt_time
from dotenv import load_dotenv

# Importa o notificador do Telegram do seu utils
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.telegram_notifier import TelegramNotifier

# Força o terminal Windows a usar UTF-8 para evitar crash nos prints com Emojis
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

# Instância do Telegram global para o Scalper
telegram_bot = TelegramNotifier()

CONTROLE_FILE = "controle_scalper.json"
SYMBOL = "WINJ26" # Ajuste para o contrato vigente do momento
DEFAULT_TIMEFRAME = mt5.TIMEFRAME_M5
VOLUME = 1.0
SL_POINTS = 100.0
TP_POINTS = 200.0  
MAGIC_NUMBER = 777777 # Magic exclusivo para isolar as negociações do Scalper
MAX_TRADES_DIA = 3
COOLDOWN_MINUTES = 5 # Tempo de espera entre trades para evitar overtrading

# Filtro de Horário (Golden Zone)
HORA_INICIO = dt_time(9, 15)
HORA_FIM = dt_time(17, 0)

def load_controle():
    if not os.path.exists(CONTROLE_FILE):
        return {"status": "OFF", "trades_hoje": 0, "lucro_hoje": 0.0, "data": datetime.now().strftime('%Y-%m-%d')}
    
    try:
        with open(CONTROLE_FILE, "r") as f:
            data = json.load(f)
            hoje_str = datetime.now().strftime('%Y-%m-%d')
            
            # Garante que SL, TP e Timeframe existam no dicionário
            if "sl_points" not in data: data["sl_points"] = SL_POINTS
            if "tp_points" not in data: data["tp_points"] = TP_POINTS
            if "timeframe" not in data: data["timeframe"] = "M5"
            if "ultima_saida" not in data: data["ultima_saida"] = None
            
            # Reset diário dos lucros e trades se virou o dia
            if data.get("data") != hoje_str:
                data["trades_hoje"] = 0
                data["lucro_hoje"] = 0.0
                data["data"] = hoje_str
                save_controle(data)
            return data
    except Exception:
        return {
            "status": "OFF", 
            "trades_hoje": 0, 
            "lucro_hoje": 0.0, 
            "data": datetime.now().strftime('%Y-%m-%d'),
            "sl_points": SL_POINTS,
            "tp_points": TP_POINTS,
            "timeframe": "M5",
            "ultima_saida": None
        }

def save_controle(data):
    with open(CONTROLE_FILE, "w") as f:
        json.dump(data, f, indent=4)

def ensure_mt5_connection():
    if not mt5.terminal_info():
        mt5.initialize(login=int(os.getenv("XP_DEMO_LOGIN", 0)), 
                       password=os.getenv("XP_DEMO_PASSWORD", ""), 
                       server="XPMT5-DEMO")
        
def wait_position_close(ticket, entrada_info):
    """Fica em loop até o SL ou TP bater na corretora ou forçar fechamento via software"""
    print(f"⏳ Aguardando fechamento da posição (Ticket: {ticket})...")
    
    hora_entrada = entrada_info['hora_entrada']
    preco_entrada = entrada_info['preco']
    direcao = entrada_info['direcao']
    
    # Carrega limites para fallback de segurança
    controle_atual = load_controle()
    sl_points_ativos = float(controle_atual.get("sl_points", SL_POINTS))
    tp_points_ativos = float(controle_atual.get("tp_points", TP_POINTS))
    
    trace_pontos = []
    
    while True:
        pos = mt5.positions_get(ticket=ticket)
        if pos is None or len(pos) == 0:
            break
            
        preco_atual = pos[0].price_current
        if direcao == mt5.ORDER_TYPE_BUY:
            pontos = preco_atual - preco_entrada
        else:
            pontos = preco_entrada - preco_atual
            
        trace_pontos.append(int(pontos))
        
        # Fallback de Software (Soft-Stop e Soft-TakeProfit)
        # Se a corretora ignorou os limites da boleta OCO original, fecha a mercado!
        if pontos <= -sl_points_ativos or pontos >= tp_points_ativos:
            print(f"⚠️ Alerta: SL/TP atingido. Forçando fechamento via Software (Proteção contra Falha de OCO B3)...")
            close_action = mt5.ORDER_TYPE_SELL if direcao == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
            
            req_close = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": SYMBOL,
                "volume": pos[0].volume,
                "type": close_action,
                "position": ticket,
                "magic": MAGIC_NUMBER,
                "comment": "Fechamento Emergencial B3",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_RETURN,
            }
            mt5.order_send(req_close)
            # Aguarda pra confirmar que fechou (se fechar, próxima volta do while sairá no break do len(pos) == 0)
            time.sleep(1.5)
            continue
            
        # O sono dura apenas 1 segundo pra ter precisao na trajetoria
        time.sleep(1)
        
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
                
    # Atualiza JSON com o lucro e salva a hora de saída
    data = load_controle()
    data["trades_hoje"] += 1
    data["lucro_hoje"] += lucro
    data["ultima_saida"] = datetime.now().isoformat()
    save_controle(data)
    
    resultado_str = "🟢 GAIN" if lucro > 0 else "🔴 LOSS"
    direcao_str = "COMPRA" if entrada_info['direcao'] == mt5.ORDER_TYPE_BUY else "VENDA"
    pontos_estimados = abs(lucro) / 0.20 # 1 contrato WIN = R$ 0,20 por ponto
    
    max_positivo = max(trace_pontos) if trace_pontos else 0
    max_negativo = min(trace_pontos) if trace_pontos else 0
    
    # Adiciona relatorio final para atualizar o CSV se necessario
    entrada_info['trace_pontos'] = trace_pontos
    registrar_log_auditoria(entrada_info) # Chama denovo pro arquivo consolidar com a trajetoria no final
    
    msg_telegram = (
        f" *RAIO-X DA OPERAÇÃO | {SYMBOL}*\n"
        f" Direção: *{direcao_str}*\n"
        f" Duração: {int(minutos)}m e {int(segundos)}s\n\n"
        f" *VOLATILIDADE (Em Pontos):*\n"
        f"- Bateu Máximo: +{int(max_positivo)} pts\n"
        f"- Bateu Mínimo: {int(max_negativo)} pts\n\n"
        f" *MOTIVO DA ENTRADA:*\n"
        f"- Gatilho: {entrada_info['preco']}\n"
        f"- EMA 9: {entrada_info['ema9']:.2f} | EMA 21: {entrada_info['ema21']:.2f}\n"
        f"- VWAP: {entrada_info['vwap']:.2f}\n\n"
        f" *RESULTADO FINAL:*\n"
        f"{resultado_str} de R$ {lucro:.2f} ({int(pontos_estimados)} pts)\n"
        f" Status Dia: {data['trades_hoje']} trades (R$ {data['lucro_hoje']:.2f})"
    )
    
    print(f" Trade fechado. Lucro/Prejuízo: R$ {lucro:.2f}")
    telegram_bot.enviar_mensagem(msg_telegram)

def registrar_log_auditoria(entrada_info):
    hoje_str = datetime.now().strftime('%Y-%m-%d')
    nome_arquivo = f"scalper_auditoria_{hoje_str}.csv"
    
    cabecalho_existe = os.path.exists(nome_arquivo)
    
    try:
        with open(nome_arquivo, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not cabecalho_existe:
                writer.writerow(['Hora_Ocorrencia_Exata', 'Direcao_Executada', 'Preco_Entrada', 'Gatilho_EMA9', 'Gatilho_SMA21', 'Filtro_VWAP', 'Trajetoria_Pontos'])
                
            direcao_str = "COMPRA" if entrada_info['direcao'] == mt5.ORDER_TYPE_BUY else "VENDA"
            hora_str = entrada_info['hora_entrada'].strftime('%Y-%m-%d %H:%M:%S')
            
            writer.writerow([
                hora_str, 
                direcao_str, 
                round(entrada_info['preco'], 2), 
                round(entrada_info['ema9'], 2), 
                round(entrada_info['sma21'], 2), 
                round(entrada_info['vwap'], 2),
                str(entrada_info.get('trace_pontos', []))
            ])
    except Exception as e:
        print(f"Erro ao salvar log de auditoria: {e}")

def iniciar_robo():
    ensure_mt5_connection()
    print("🤖 Robô Scalper WIN Inicializado. Lendo Regra de Ouro...")
    
    ultima_vela_operada = None
    ultima_vela_vista = None
    
    while True:
        # 1. Regra de Ouro: Ler status antes de tudo
        controle = load_controle()
        
        # if controle["trades_hoje"] >= MAX_TRADES_DIA:
        #     time.sleep(60)
        #     continue
            
        # Sistema de Cooldown removido a pedido do usuario

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
        
        # Mapeia timeframe do JSON para constante MT5
        tf_str = controle.get("timeframe", "M5")
        mt5_tf = mt5.TIMEFRAME_M1 if tf_str == "M1" else mt5.TIMEFRAME_M5
        
        # Reduzindo de 1000 para 200 velas pois o mercado B3 tem 108 velas de M5, isso garante 100% da VWAP Diária
        rates = mt5.copy_rates_from_pos(SYMBOL, mt5_tf, 0, 200)
        if rates is None or len(rates) < 50:
            err_code = mt5.last_error()
            print(f"⚠️ [Scalper] ERRO/AVISO: Falha ao obter dados suficientes para {SYMBOL}. Código MT5: {err_code}")
            time.sleep(5)
            continue
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        vela_atual_time = df.iloc[-1]['time']
        
        # O GATILHO (NEW BAR DETECTION)
        if ultima_vela_vista is None or vela_atual_time != ultima_vela_vista:
            ultima_vela_vista = vela_atual_time
            
            # --- HEARTBEAT LOG ---
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🫀 [Scalper] Nova Vela Detectada ({vela_atual_time}). Processando análises para {SYMBOL} no TF {tf_str}...")
            
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
            
            # --- EXECUTION LOG ---
            print(f"   ↳ [Scalper] {SYMBOL} Valores Atuais - EMA9: {current['EMA9']:.2f}, SMA21: {current['SMA21']:.2f}, VWAP: {current['VWAP']:.2f}")
            
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
                        sl = price - float(controle.get("sl_points", SL_POINTS))
                        tp = price + float(controle.get("tp_points", TP_POINTS))
                        msg_label = "COMPRA"
                    else: # SELL
                        price = mt5.symbol_info_tick(SYMBOL).bid
                        sl = price + float(controle.get("sl_points", SL_POINTS))
                        tp = price - float(controle.get("tp_points", TP_POINTS))
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
                    
                    print(f"📩 [Scalper] Enviando Ordem OCO: {msg_label} | Price: {price} | SL: {sl} | TP: {tp}")
                    res = mt5.order_send(request)
                    if res.retcode == mt5.TRADE_RETCODE_DONE:
                        msg_telegram_entrada = (
                            f"🟢 *ORDEM EXECUTADA!* 🟢\n"
                            f"Ativo: {SYMBOL}\n"
                            f"Direção: {msg_label}\n"
                            f"Preço de Entrada: {price}\n"
                            f"Aguardando fechamento..."
                        )
                        telegram_bot.enviar_mensagem(msg_telegram_entrada)
                        
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
                        print(f"❌ [Scalper] Erro na Ordem: {res.comment} / MT5 Error: {mt5.last_error()} / Retcode: {res.retcode}")
        
        # Ciclo Ultra-Rápido (0.1s para reação quase imediata no mt5)
        time.sleep(0.1)

if __name__ == "__main__":
    iniciar_robo()
