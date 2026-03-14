import threading
import time
from flask import Flask, render_template, jsonify, request
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pandas as pd
from utils.telegram_notifier import TelegramNotifier
import os
import logging
import json
import io
import matplotlib
matplotlib.use('Agg')
import mplfinance as mpf
from dotenv import load_dotenv
import numpy as np


###### 9 exponencial



# Carrega variáveis de ambiente (incluindo XP_DEMO_PASSWORD e XP_DEMO_LOGIN)
load_dotenv()

app = Flask(__name__)

# Silencia os logs de requisição HTTP do Flask (Werkzeug) para não poluir o terminal
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# ======================================================================
# CONEXÃO BLINDADA (XP SIMULADOR) - INICIA ANTES DE TUDO
# ======================================================================
def ensure_mt5_connected():
    try:
        XP_LOGIN_STR = os.getenv("XP_DEMO_LOGIN")
        XP_SERVER = "XPMT5-DEMO"
        XP_PASSWORD = os.getenv("XP_DEMO_PASSWORD")
        
        if not XP_PASSWORD:
            err_msg = "A senha da conta XP Demo nao foi encontrada! (Falta XP_DEMO_PASSWORD no .env)"
            print(f"[ERROR] {err_msg}")
            return False, err_msg
            
        if not XP_LOGIN_STR:
            err_msg = "O login da conta XP Demo nao foi encontrado! (Falta XP_DEMO_LOGIN no .env)"
            print(f"[ERROR] {err_msg}")
            return False, err_msg
            
        XP_LOGIN = int(XP_LOGIN_STR)
            
        # 1. Silenciosamente verifica se já está conectado na conta correta
        # Se terminal_info e account_info existirem, e o login bater, ignora o resto
        if mt5.terminal_info() is not None:
            acc_info = mt5.account_info()
            if acc_info is not None and acc_info.login == XP_LOGIN:
                return True, None
                
        # 2. Se chegar aqui, significa que PRECISA inicializar ou conectar
        print("[INFO] Iniciando Modulo de Seguranca MT5 (XP Simulador)...")
        
        if not mt5.initialize():
            print(f"[ERROR] Erro MT5 Initialize: {mt5.last_error()}")
            return False, str(mt5.last_error())
            
        print(f"[INFO] Forcando conexao segura para Simulacao XP (Login: {XP_LOGIN})...")
        if mt5.login(login=XP_LOGIN, password=XP_PASSWORD, server=XP_SERVER):
            acc = mt5.account_info()
            print(f"[SUCCESS] PROTEGIDO: Conectado ao Simulador XP! Corretora: {acc.company} | Saldo: R${acc.balance:.2f}")
            return True, None
        else:
            print(f"[ERROR] ERRO DE LOGIN NA XP: {mt5.last_error()}")
            return False, f"Falha no MT5 Login: {mt5.last_error()}"
            
    except Exception as e:
        print(f"[ERROR] Exception MT5: {e}")
        return False, str(e)

# 🚨 CHAMA IMEDIATAMENTE NA INICIALIZAÇÃO DO APP 🚨
# Para garantir que as threads do Flask/Telegram não usem a conta de Produção (BTG)
if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or __name__ == "__main__":
    ensure_mt5_connected()

# --- GLOBAL CONFIG & STATE ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
MONITOR_SYMBOL = "WINJ26" # Default monitored symbol (Deprecated in favor of full list)
MONITOR_TIMEFRAME = "H1" # Timeframe do Monitoramento (M1, M5, H1, etc)
LAST_SIGNAL_STATE = {} # Dict para guardar estado de cada ativo: { "WINJ26": 1, ... }
# Novo dict de persistência
SENT_ALERTS_TODAY = {} # {"PETR4F": "2026-03-02"}
ALERTS_FILE = "alertas_enviados.json"

def load_alerts_state():
    global SENT_ALERTS_TODAY
    if os.path.exists(ALERTS_FILE):
        try:
            with open(ALERTS_FILE, "r") as f:
                SENT_ALERTS_TODAY = json.load(f)
        except Exception as e:
            print(f"⚠️ Erro ao carregar arquivo de alertas: {e}")
            SENT_ALERTS_TODAY = {}
    else:
        SENT_ALERTS_TODAY = {}

def save_alerts_state():
    try:
        with open(ALERTS_FILE, "w") as f:
            json.dump(SENT_ALERTS_TODAY, f, indent=4)
    except Exception as e:
        print(f"⚠️ Erro ao salvar arquivo de alertas: {e}")

# Controle On/Off do bot de alertas Telegram
BOT_RUNNING = False
BOT_START_TIME = None
TOTAL_ALERTS = 0
ALERTS_PER_ASSET = {}

# Carrega persistência imediatamente na inicialização
load_alerts_state()

# Instância global do Notifier para o listener e alertas
global_notifier = TelegramNotifier(token=TELEGRAM_TOKEN, chat_id=TELEGRAM_CHAT_ID)

def get_bot_status_text():
    global BOT_RUNNING, SENT_ALERTS_TODAY
    status = "🟢 *ONLINE*" if BOT_RUNNING else "🔴 *OFFLINE*"
    
    hoje_str = datetime.now().strftime('%Y-%m-%d')
    alertas_hoje = []
    
    for asset, info in SENT_ALERTS_TODAY.items():
        if isinstance(info, dict) and info.get("data") == hoje_str:
            alertas_hoje.append(asset)
        elif isinstance(info, str) and info == hoje_str:
            alertas_hoje.append(asset)
            
    total_hoje = len(alertas_hoje)
    
    text = f"📊 *Status do Sistema*\n\n"
    text += f"Status: {status}\n"
    text += f"Total de Alertas Hoje: {total_hoje}\n\n"
    
    if total_hoje > 0:
        text += "*Ativos Alertados Hoje:*\n"
        for asset in alertas_hoje:
            text += f"▫️ {asset}\n"
    else:
        text += "Nenhum alerta enviado hoje."
        
    return text

def gerar_resumo_diario_ativo():
    """
    Realiza um Scanner Ativo de Fim de Dia:
    Varre todos os ativos, puxa os candles de hoje e verifica 
    se houve algum cruzamento de médias independentemente do JSON.
    """
    print("🔄 [Scanner] Iniciando Varredura Ativa para o Resumo Diário...")
    
    # 1. Garante que o MT5 está conectado
    ensure_mt5_connected()
    
    # 2. Carrega a lista de ativos
    from utils.asset_filter import load_clean_assets
    assets_data = load_clean_assets()
    if isinstance(assets_data, dict):
        assets = assets_data.get("Indices", []) + assets_data.get("Acoes", [])
    else:
        assets = assets_data
        
    mt5_tf = TIMEFRAMES.get(MONITOR_TIMEFRAME, mt5.TIMEFRAME_M5)
    start_hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    compras_hoje = []
    vendas_hoje = []
    
    for symbol in assets:
        try:
            rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, 100)
            if rates is None or len(rates) < 55:
                continue
                
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            df['SMA_Short'] = df['close'].rolling(window=20).mean()
            df['SMA_Long'] = df['close'].rolling(window=50).mean()
            
            df_hoje = df[df['time'] >= start_hoje]
            if df_hoje.empty or len(df_hoje) < 2:
                continue
                
            ultimo_cruzamento = None
            hora_cruzamento = None
            
            for i in range(1, len(df_hoje)):
                idx_current = df_hoje.index[i]
                idx_prev = df_hoje.index[i-1]
                
                c_short = df.loc[idx_current, 'SMA_Short']
                c_long = df.loc[idx_current, 'SMA_Long']
                p_short = df.loc[idx_prev, 'SMA_Short']
                p_long = df.loc[idx_prev, 'SMA_Long']
                
                if pd.isna(c_short) or pd.isna(c_long):
                    continue
                    
                if p_short <= p_long and c_short > c_long:
                    ultimo_cruzamento = "COMPRA"
                    hora_cruzamento = df.loc[idx_current, 'time'].strftime('%H:%M')
                elif p_short >= p_long and c_short < c_long:
                    ultimo_cruzamento = "VENDA"
                    hora_cruzamento = df.loc[idx_current, 'time'].strftime('%H:%M')
                    
            if ultimo_cruzamento == "COMPRA":
                compras_hoje.append(f"🔹 {symbol} - COMPRA (às {hora_cruzamento})")
            elif ultimo_cruzamento == "VENDA":
                vendas_hoje.append(f"🔹 {symbol} - VENDA (às {hora_cruzamento})")
                
        except Exception as e:
            pass
            
    # 3. Formatação da Mensagem
    total = len(compras_hoje) + len(vendas_hoje)
    
    if total == 0:
        return "Nenhum cruzamento de médias foi detectado no mercado hoje."
        
    final_text = (
        f"📊 *Scanner de Fim de Dia (Hoje):*\n"
        f"O mercado apresentou os seguintes cruzamentos hoje:\n\n"
    )
    
    if compras_hoje:
        final_text += "🟢 *COMPRAS (Golden Cross):*\n"
        final_text += "\n".join(compras_hoje) + "\n\n"
        
    if vendas_hoje:
        final_text += "🔴 *VENDAS (Death Cross):*\n"
        final_text += "\n".join(vendas_hoje) + "\n"
        
    print("✅ [Scanner] Resumo Diário gerado com sucesso!")
    return final_text

def toggle_bot_from_telegram(turn_on: bool):
    global BOT_RUNNING, BOT_START_TIME, TOTAL_ALERTS, ALERTS_PER_ASSET
    if turn_on:
        if BOT_RUNNING:
            return "O robô já está 🟢 LIGADO."
        BOT_RUNNING = True
        BOT_START_TIME = datetime.now()
        TOTAL_ALERTS = 0 # Mantendo para não quebrar compatibilidade
        ALERTS_PER_ASSET.clear()
        return "▶️ O robô foi 🟢 LIGADO pelo Telegram e começou a monitorar os ativos."
    else:
        if not BOT_RUNNING:
            return "O robô já está 🔴 DESLIGADO."
        BOT_RUNNING = False
        BOT_START_TIME = None
        return "⏸️ O robô foi 🔴 DESLIGADO pelo Telegram. O monitoramento parou."

def ver_carteira_mt5():
    connected, err = ensure_mt5_connected()
    if not connected:
        return f"❌ Erro de conexão com MT5: {err}", None
        
    positions = mt5.positions_get()
    if positions is None or len(positions) == 0:
        return "💼 *Sua Carteira está vazia!*\nNenhuma posição aberta no momento.", None
        
    text = "💼 *Sua Carteira (Posições Abertas)*\n\n"
    total_profit = 0.0
    inline_kb = []
    
    for pos in positions:
        ticker = pos.symbol
        volume = pos.volume
        price_open = pos.price_open
        price_current = pos.price_current
        profit = pos.profit
        ticket = pos.ticket
        total_profit += profit
        
        tipo = "🟢 COMPRA" if pos.type == mt5.ORDER_TYPE_BUY else "🔴 VENDA"
        text += f"*{ticker}* ({tipo})\n"
        text += f"Volume: {volume}\n"
        text += f"Preço Médio: R$ {price_open:.2f}\n"
        text += f"Preço Atual: R$ {price_current:.2f}\n"
        text += f"Lucro/Prej: R$ {profit:.2f}\n"
        text += "------------------------\n"
        
        # Add a close button for this position
        inline_kb.append([{"text": f"❌ Fechar {ticker} ({volume}x)", "callback_data": f"close_{ticket}"}])
        
    text += f"\n📊 *Resultado Aberto Total:* R$ {total_profit:.2f}"
    
    # Add a global cancel button to dismiss the menu
    inline_kb.append([{"text": "Esconder", "callback_data": "cancel"}])
    
    return text, inline_kb

def fechar_posicao_mt5(ticket):
    connected, err = ensure_mt5_connected()
    if not connected:
        return False, f"Erro MT5: {err}"
        
    position = mt5.positions_get(ticket=int(ticket))
    if position is None or len(position) == 0:
        return False, f"Posição {ticket} não encontrada."
        
    pos = position[0]
    symbol = pos.symbol
    lot = pos.volume
    order_type = pos.type
    
    # To close a BUY, we SELL. To close a SELL, we BUY.
    if order_type == mt5.ORDER_TYPE_BUY:
        close_type = mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).bid
    else:
        close_type = mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).ask
        
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": float(lot),
        "type": close_type,
        "position": pos.ticket,
        "price": price,
        "deviation": 20,
        "magic": 101010,
        "comment": "Bot_FinSense_Close",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_RETURN,
    }
    
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        return False, f"Erro ao fechar posição: {result.comment} (Code: {result.retcode})"
        
    return True, f"✅ Posição de {symbol} (Ticket {ticket}) fechada com sucesso!"

def ver_historico_mt5():
    connected, err = ensure_mt5_connected()
    if not connected:
        return f"❌ Erro de conexão com MT5: {err}"
        
    agora = datetime.now()
    hoje_inicio = agora.replace(hour=0, minute=0, second=0, microsecond=0)
    hoje_fim = hoje_inicio + timedelta(days=1)
    
    # Busca histórico dos últimos 30 dias para ter uma visão ampla
    inicio_historico = hoje_inicio - timedelta(days=30)
    
    deals = mt5.history_deals_get(inicio_historico, hoje_fim)
    if deals is None or len(deals) == 0:
        return "📜 *Histórico Vazio*\nNenhuma operação foi encontrada nos últimos 30 dias."
        
    deals_hoje = []
    deals_passado = []
    
    for deal in deals:
        if getattr(deal, 'entry', 0) == 1 or deal.profit != 0:
            if deal.symbol == "":
                continue
                
            deal_time = datetime.utcfromtimestamp(deal.time)
            if deal_time >= hoje_inicio:
                deals_hoje.append(deal)
            else:
                deals_passado.append(deal)

    def formatar_deals(deal_list, titulo, mostrar_data=False, limit_display=None):
        if not deal_list:
            return f"_{titulo}_\nNenhuma operação.\n\n", 0, 0, 0, 0
            
        texto = f"*{titulo}*\n"
        total_profit = 0.0
        trades_count = 0
        gain_count = 0
        loss_count = 0
        
        # Inverter para mostrar os mais recentes primeiro
        for deal in reversed(deal_list):
            ticker = deal.symbol
            profit = deal.profit
            dt = datetime.utcfromtimestamp(deal.time)
            
            hora = dt.strftime('%d/%m %H:%M') if mostrar_data else dt.strftime('%H:%M:%S')
            
            total_profit += profit
            trades_count += 1
            if profit >= 0:
                gain_count += 1
                icon = "✅"
            else:
                loss_count += 1
                icon = "❌"
                
            if limit_display is None or trades_count <= limit_display:
                texto += f"{icon} {ticker} ({hora}) ➔ R$ {profit:.2f}\n"
                
        if limit_display is not None and len(deal_list) > limit_display:
            ocultos = len(deal_list) - limit_display
            texto += f"...e mais {ocultos} operações ocultas.\n"
            
        texto += f"\n📊 *Resumo ({titulo.lower()}):*\n"
        texto += f"Trades: {trades_count} ({gain_count} Gain / {loss_count} Loss)\n"
        texto += f"Resultado: *R$ {total_profit:.2f}*\n\n"
        
        return texto, total_profit, trades_count, gain_count, loss_count

    txt_hoje, p_h, t_h, g_h, l_h = formatar_deals(deals_hoje, "Hoje", mostrar_data=False)
    
    # Passa todos os trades, mas limita a exibição aos últimos 15
    txt_passado, p_p, t_p, g_p, l_p = formatar_deals(deals_passado, "Últimos Dias (Até 15 mostrados)", mostrar_data=True, limit_display=15)
    
    final_text = "📜 *SEU HISTÓRICO DE TRADES*\n━━━━━━━━━━━━━━━━━━\n\n"
    final_text += txt_hoje
    final_text += "━━━━━━━━━━━━━━━━━━\n\n"
    final_text += txt_passado
    final_text += "━━━━━━━━━━━━━━━━━━\n"
    
    total_geral = p_h + p_p
    total_trades = t_h + t_p
    
    winrate_valor = ((g_h + g_p) / total_trades * 100) if total_trades > 0 else 0.0
    
    final_text += f"🏆 *SALDO TOTAL (30 dias):* R$ {total_geral:.2f}\n"
    final_text += f"📈 *Winrate:* {winrate_valor:.1f}%"
    
    return final_text

def executar_ordem_mt5(action, symbol, volume):
    connected, err = ensure_mt5_connected()
    if not connected:
        return False, f"Erro MT5: {err}"
        
    if not mt5.symbol_select(symbol, True):
        return False, f"Ativo {symbol} não encontrado no Market Watch."

    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        return False, f"Falha ao obter dados do ativo {symbol}."

    if action == "buy":
        order_type = mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).ask
    else:
        order_type = mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).bid

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": float(volume),
        "type": order_type,
        "price": price,
        "deviation": 20,
        "magic": 101010,
        "comment": "Bot_FinSense",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_RETURN,
    }

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        return False, f"Erro ao enviar ordem: {result.comment} (Code: {result.retcode})"
        
    tipo_str = "COMPRA" if action == "buy" else "VENDA"
    return True, f"✅ Ordem de {tipo_str} de {volume}x {symbol} executada com sucesso!\nPreço: R$ {result.price:.2f}"

def handle_telegram_callback(data, chat_id, message_id):
    if data == "cancel":
        global_notifier.editar_mensagem(chat_id, message_id, "❌ *Operação Cancelada.*")
        return
        
    parts = data.split('_')
    if len(parts) >= 3 and parts[0] == "prep":
        action = parts[1]
        symbol = parts[2]
        action_str = "COMPRA" if action == "buy" else "VENDA"
        
        texto = f"⚙️ *Preparando envio de ordem*\nQuantas ações de *{symbol}* deseja operar? ({action_str})"
        inline_kb = [
            [
                {"text": "1", "callback_data": f"exec_{action}_{symbol}_1"},
                {"text": "5", "callback_data": f"exec_{action}_{symbol}_5"},
                {"text": "10", "callback_data": f"exec_{action}_{symbol}_10"},
                {"text": "20", "callback_data": f"exec_{action}_{symbol}_20"}
            ],
            [
                {"text": "❌ Cancelar", "callback_data": "cancel"}
            ]
        ]
        global_notifier.editar_mensagem(chat_id, message_id, texto, inline_kb)
        
    elif len(parts) >= 4 and parts[0] == "exec":
        action = parts[1]
        symbol = parts[2]
        volume = float(parts[3])
        
        global_notifier.editar_mensagem(chat_id, message_id, f"⏳ *Enviando ordem de {volume}x {symbol} para o MetaTrader 5...*")
        
        
        success, result_msg = executar_ordem_mt5(action, symbol, volume)
        global_notifier.editar_mensagem(chat_id, message_id, result_msg)
        
    elif len(parts) >= 2 and parts[0] == "close":
        ticket = parts[1]
        
        global_notifier.editar_mensagem(chat_id, message_id, f"⏳ *Fechando posição Ticket {ticket}...*")
        
        success, result_msg = fechar_posicao_mt5(ticket)
        global_notifier.editar_mensagem(chat_id, message_id, result_msg)

def enviar_alerta_teste(chat_id):
    symbol = "PETR4F"
    signal_text = "COMPRA"
    tipo = "Golden Cross"
    price = 40.00
    c_short = 39.80
    c_long = 39.50
    agora = datetime.now()
    
    msg = (
        f"🚨 *FINSENSE ALERT (TESTE)* 🚨\n\n"
        f"🟢 *SINAL:* {signal_text} ({tipo})\n"
        f"🎯 *ATIVO:* {symbol}  |  ⏱️ *TF:* TESTE\n\n"
        f"💰 *PREÇO ATUAL:* {price:.2f}\n\n"
        f"📊 *CRUZAMENTO DAS MÉDIAS:*\n"
        f"🔸 SMA 20: {c_short:.2f}\n"
        f"🔹 SMA 50: {c_long:.2f}\n\n"
        f"📅 *DATA/HORA:* {agora.strftime('%d/%m/%Y às %H:%M:%S')}"
    )
    
    inline_kb = [
        [{"text": f"🛒 Executar {signal_text}", "callback_data": f"prep_{'buy' if signal_text=='COMPRA' else 'sell'}_{symbol}"}]
    ]
    
    try:
        # Gera o grafico falso de teste
        rates = mt5.copy_rates_from_pos("PETR4", mt5.TIMEFRAME_H1, 0, 1000)
        df_test = pd.DataFrame(rates)
        df_test['time'] = pd.to_datetime(df_test['time'], unit='s')
        df_test.set_index('time', inplace=True)
        
        df_test['SMA_Short'] = df_test['close'].rolling(window=20).mean()
        df_test['SMA_Long'] = df_test['close'].rolling(window=50).mean()
        
        # Mantem so as ultimas 100 velas pro plot ficar clean
        df_plot = df_test.tail(100).copy()
        
        mc = mpf.make_marketcolors(up='#00e676', down='#ff1744', edge='inherit', wick='inherit', volume='in', ohlc='i')
        s  = mpf.make_mpf_style(marketcolors=mc, facecolor='#121212', edgecolor='#2c2c2c', figcolor='#121212', gridcolor='#2c2c2c', gridstyle='--')
        
        ap = [
            mpf.make_addplot(df_plot['SMA_Short'], color='#FFFF00', width=1.5),
            mpf.make_addplot(df_plot['SMA_Long'], color='#00BFFF', width=1.5)
        ]
        
        buf = io.BytesIO()
        mpf.plot(df_plot, type='candle', style=s, addplot=ap, volume=False,
                 figsize=(8, 4), tight_layout=True,
                 axisoff=True, savefig=dict(fname=buf, dpi=100, bbox_inches='tight', pad_inches=0.1))
        
        global_notifier.enviar_foto(buf, msg, target_chat_id=chat_id, inline_keyboard=inline_kb)
    except Exception as e:
        print(f"Erro ao gerar grafico de teste: {e}")
        global_notifier.enviar_mensagem(msg, target_chat_id=chat_id, inline_keyboard=inline_kb)

# ==========================================
# ROTAS DO MÓDULO SCALPER WIN (IN NAVE MÃE)
# ==========================================
CONTROLE_SCALPER_FILE = "controle_scalper.json"

def get_scalper_state():
    if os.path.exists(CONTROLE_SCALPER_FILE):
        try:
            with open(CONTROLE_SCALPER_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"status": "OFF", "trades_hoje": 0, "lucro_hoje": 0.0}

@app.route('/api/toggle_scalper', methods=['POST'])
def toggle_scalper():
    state = get_scalper_state()
    state['status'] = "ON" if state['status'] == "OFF" else "OFF"
    
    with open(CONTROLE_SCALPER_FILE, "w") as f:
        json.dump(state, f, indent=4)
        
    return jsonify({"success": True, "new_status": state['status']})

@app.route('/api/stats_scalper', methods=['GET'])
def stats_scalper():
    return jsonify(get_scalper_state())

def handle_telegram_toggle_scalper():
    state = get_scalper_state()
    state['status'] = "ON" if state['status'] == "OFF" else "OFF"
    with open(CONTROLE_SCALPER_FILE, "w") as f:
        json.dump(state, f, indent=4)
        
    return f"O Robô Scalper de Índice foi {'🟢 LIGADO' if state['status'] == 'ON' else '🔴 DESLIGADO'} com sucesso."

def handle_telegram_stats_scalper():
    state = get_scalper_state()
    status_fmt = "ON 🟢" if state['status'] == "ON" else "OFF 🔴"
    return (
        f"🤖 *Status Scalper WIN*\n\n"
        f"Status: {status_fmt}\n"
        f"Trades Hoje: {state.get('trades_hoje', 0)}\n"
        f"Lucro/Prej: R$ {float(state.get('lucro_hoje', 0.0)):.2f}"
    )

# Inicia o Listener de Comandos (/start) apenas no processo principal (não no reloader inicial)
if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or __name__ == "__main__":
    global_notifier.start_listener(
        status_callback=get_bot_status_text, 
        toggle_callback=toggle_bot_from_telegram,
        summary_callback=gerar_resumo_diario_ativo,
        carteira_callback=ver_carteira_mt5,
        callback_query_handler=handle_telegram_callback,
        teste_callback=enviar_alerta_teste,
        historico_callback=ver_historico_mt5,
        toggle_scalper_cb=handle_telegram_toggle_scalper,
        stats_scalper_cb=handle_telegram_stats_scalper
    )

def sincronizar_historico_hoje():
    """
    Roda UMA VEZ ao ligar o bot para buscar no histórico do MT5 se houve algum
    cruzamento MAIS CEDO NO MESMO DIA (hoje). Se sim, registra silenciosamente
    no JSON de persistência para evitar flood ao usuário.
    """
    global SENT_ALERTS_TODAY
    
    print("🔄 [Catch-Up] Sincronizando histórico de hoje para evitar alertas repetidos...")
    hoje_str = datetime.now().strftime('%Y-%m-%d')
    start_hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    from utils.asset_filter import load_clean_assets
    assets_data = load_clean_assets()
    if isinstance(assets_data, dict):
        assets = assets_data.get("Indices", []) + assets_data.get("Acoes", [])
    else:
        assets = assets_data
        
    mt5_tf = TIMEFRAMES.get(MONITOR_TIMEFRAME, mt5.TIMEFRAME_M5)
    sinal_encontrado_count = 0
    
    for symbol in assets:
        try:
            # Puxa candles suficientes para cruzar médias (ex: 100)
            rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, 100)
            if rates is None or len(rates) < 55:
                continue
                
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            df['SMA_Short'] = df['close'].rolling(window=20).mean()
            df['SMA_Long'] = df['close'].rolling(window=50).mean()
            
            # Precisamos iterar sobre os candles apenas do DIA DE HOJE
            # Para não enviar sinais antigos da semana passada "retroativamente pra hoje"
            df_hoje = df[df['time'] >= start_hoje]
            if df_hoje.empty or len(df_hoje) < 2:
                continue
                
            ultimo_cruzamento = None
            hora_cruzamento = None
            
            # Procura pelo ÚLTIMO cruzamento que ocorreu HOJE
            for i in range(1, len(df_hoje)):
                idx_current = df_hoje.index[i]
                idx_prev = df_hoje.index[i-1]
                
                c_short = df.loc[idx_current, 'SMA_Short']
                c_long = df.loc[idx_current, 'SMA_Long']
                p_short = df.loc[idx_prev, 'SMA_Short']
                p_long = df.loc[idx_prev, 'SMA_Long']
                
                if pd.isna(c_short) or pd.isna(c_long):
                    continue
                    
                if p_short <= p_long and c_short > c_long:
                    ultimo_cruzamento = "COMPRA"
                    hora_cruzamento = df.loc[idx_current, 'time'].strftime('%H:%M')
                elif p_short >= p_long and c_short < c_long:
                    ultimo_cruzamento = "VENDA"
                    hora_cruzamento = df.loc[idx_current, 'time'].strftime('%H:%M')
                    
            if ultimo_cruzamento:
                # Verifica se JÁ NÃO ESTAVA no JSON para não sobrescrever a hora atoa
                ja_alertado = False
                info = SENT_ALERTS_TODAY.get(symbol)
                if isinstance(info, dict) and info.get("data") == hoje_str:
                    ja_alertado = True
                elif isinstance(info, str) and info == hoje_str:
                    ja_alertado = True
                    
                if not ja_alertado:
                    SENT_ALERTS_TODAY[symbol] = {
                        "data": hoje_str,
                        "hora": hora_cruzamento,
                        "sinal": ultimo_cruzamento
                    }
                    LAST_SIGNAL_STATE[symbol] = 1 if ultimo_cruzamento == "COMPRA" else -1
                    sinal_encontrado_count += 1
                    
        except Exception as e:
            pass # Erros individuais blindados no loop de sync
            
    if sinal_encontrado_count > 0:
        save_alerts_state()
        print(f"✅ [Catch-Up] {sinal_encontrado_count} cruzamentos passados de hoje encontrados e salvos silenciosamente.")
    else:
        print("✅ [Catch-Up] Nenhum cruzamento perdido no histórico de hoje.")

def run_telegram_monitor():
    """
    Função que roda em thread separada para monitorar cruzamento de médias
    e enviar alertas no Telegram.
    """
    global LAST_SIGNAL_STATE, BOT_RUNNING, TOTAL_ALERTS, ALERTS_PER_ASSET, SENT_ALERTS_TODAY
    
    # Carrega lista de ativos
    from utils.asset_filter import load_clean_assets
    
    # Aguarda até o usuário ligar o BOT via API antes de conectar/monitorar
    print("⏳ [Thread] Monitor Telegram carregado e aguardando ativação...", flush=True)
    time.sleep(2) # Delay inicial para afastar da inicialização do Flask/MT5
    
    while True:
        # Espera o botão ligar
        while not BOT_RUNNING:
            time.sleep(1)

        # Quando o BOT for ligado, tenta garantir conexão com MT5
        connected, err = ensure_mt5_connected()
        if not connected:
            print(f"⚠️ [Monitor] MT5 não conectado: {err}. Tentando novamente em 5s...")
            time.sleep(5)
            continue
            
        # Sincroniza retroativamente os cruzamentos esquecidos de hoje CADA VEZ que liga
        sincronizar_historico_hoje()

        print(f"🚀 [Monitor] Iniciando Thread de Monitoramento para TODOS os ativos...")
        print(f"⏰ Timeframe: {MONITOR_TIMEFRAME} | Delay entre ativos: 0.1s | Ciclo: 60s")

        # Inicia ciclo de monitoramento enquanto BOT_RUNNING for True
        while BOT_RUNNING:

            # Recarrega lista a cada ciclo (caso mude)
            assets_data = load_clean_assets()
            # Flatten se for dict
            if isinstance(assets_data, dict):
                assets = assets_data.get("Indices", []) + assets_data.get("Acoes", [])
            else:
                assets = assets_data

            print(f"🔎 [Monitor] Iniciando ciclo de verificação em {len(assets)} ativos...")
            
            for symbol in assets:
                # Checa se foi desligado durante o processamento de ativos
                if not BOT_RUNNING:
                    print("💤 [Monitor] Interrompendo ciclo: BOT_RUNNING=False")
                    break

                try:
                    # 1. Pega dados
                    # Define Timeframe (Default M5 se não achar)
                    mt5_tf = TIMEFRAMES.get(MONITOR_TIMEFRAME, mt5.TIMEFRAME_M5)
                    
                    # 1000 velas para dar o warm-up matematico exato da plataforma
                    rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, 1000)
                    if rates is None or len(rates) < 55: # Precisa de pelo menos 50 + buffer
                        continue

                    df = pd.DataFrame(rates)
                    df['time'] = pd.to_datetime(df['time'], unit='s')
                    
                    # 2. Calcula SMA 20 e 50
                    df['SMA_Short'] = df['close'].rolling(window=20).mean()
                    df['SMA_Long'] = df['close'].rolling(window=50).mean()
                    
                    # 3. Verifica Cruzamento (usando apenas vela fechada para evitar sinais falsos)
                    current = df.iloc[-2]
                    prev = df.iloc[-3]
                    
                    c_short = current['SMA_Short']
                    c_long = current['SMA_Long']
                    p_short = prev['SMA_Short']
                    p_long = prev['SMA_Long']
                    
                    if not (pd.isna(c_short) or pd.isna(c_long) or pd.isna(p_short) or pd.isna(p_long)):
                        signal_text = None
                        
                        # Recupera estado anterior deste ativo especifico
                        last_state = LAST_SIGNAL_STATE.get(symbol, 0)
                        new_state = last_state
                        
                        # Golden Cross
                        if p_short <= p_long and c_short > c_long:
                            if last_state != 1:
                                signal_text = "COMPRA"
                                new_state = 1
                        # Death Cross
                        elif p_short >= p_long and c_short < c_long:
                            if last_state != -1:
                                signal_text = "VENDA"
                                new_state = -1
                                
                        if signal_text:
                            # Filtro Temporal: Só alerta se o cruzamento for MAIS RECENTE que o start do Bot
                            sinal_time = current['time']
                            
                            # Filtro de Persistência (JSON)
                            # Verifica se já alertamos sobre este cruzamento HOJE
                            hoje_str = sinal_time.strftime('%Y-%m-%d')
                            ultimo_alerta_data = SENT_ALERTS_TODAY.get(symbol)
                            
                            # Atualiza estado na RAM igual
                            LAST_SIGNAL_STATE[symbol] = new_state
                            
                            if BOT_START_TIME and sinal_time <= BOT_START_TIME:
                                print(f"🕒 [Monitor] Ignorando sinal passado de {symbol} em {sinal_time}")
                                continue
                                
                            # Se já mandamos hoje para esse ticker na mesma data, ignora
                            is_already_sent = False
                            if isinstance(ultimo_alerta_data, str) and ultimo_alerta_data == hoje_str:
                                is_already_sent = True
                            elif isinstance(ultimo_alerta_data, dict) and ultimo_alerta_data.get("data") == hoje_str:
                                is_already_sent = True

                            if is_already_sent:
                                print(f"🔒 [Monitor] Sinal de {symbol} bloqueado pelo controle Anti-Spam (Já enviado hoje).")
                                continue
                            
                            TOTAL_ALERTS += 1
                            ALERTS_PER_ASSET[symbol] = ALERTS_PER_ASSET.get(symbol, 0) + 1

                            icone = "🟢" if signal_text == "COMPRA" else "🔴"
                            tipo = "Golden Cross" if signal_text == "COMPRA" else "Death Cross"
                            
                            msg = (
                                f"🚨 *FINSENSE ALERT* 🚨\n\n"
                                f"{icone} *SINAL:* {signal_text} ({tipo})\n"
                                f"🎯 *ATIVO:* {symbol}  |  ⏱️ *TF:* {MONITOR_TIMEFRAME}\n\n"
                                f"💰 *PREÇO ATUAL:* {current['close']:.2f}\n\n"
                                f"📊 *CRUZAMENTO DAS MÉDIAS:*\n"
                                f"🔸 SMA 20: {c_short:.2f}\n"
                                f"🔹 SMA 50: {c_long:.2f}\n\n"
                                f"📅 *DATA/HORA:* {current['time'].strftime('%d/%m/%Y às %H:%M:%S')}"
                            )
                            print(f"\n⚡ [Monitor] ALERTA ENVIADO para {symbol}: {signal_text}")
                            
                            try:
                                inline_kb = [
                                    [{"text": f"🛒 Executar {signal_text}", "callback_data": f"prep_{'buy' if signal_text=='COMPRA' else 'sell'}_{symbol}"}]
                                ]
                                
                                # -- GERAÇÃO DO GRÁFICO (Dark Mode Institutional) --
                                df_plot = df.tail(100).copy()
                                df_plot.set_index('time', inplace=True)
                                
                                mc = mpf.make_marketcolors(
                                    up='#00e676', down='#ff1744', 
                                    edge='inherit', wick='inherit', 
                                    volume='in', ohlc='i'
                                )
                                s = mpf.make_mpf_style(
                                    marketcolors=mc, 
                                    facecolor='#121212', 
                                    edgecolor='#2c2c2c', 
                                    figcolor='#121212', 
                                    gridcolor='#2c2c2c', 
                                    gridstyle='--'
                                )
                                
                                ap = [
                                    mpf.make_addplot(df_plot['SMA_Short'], color='#FFFF00', width=1.5),
                                    mpf.make_addplot(df_plot['SMA_Long'], color='#00BFFF', width=1.5)
                                ]
                                
                                buf = io.BytesIO()
                                mpf.plot(
                                    df_plot, 
                                    type='candle', 
                                    style=s, 
                                    addplot=ap, 
                                    volume=False,
                                    figsize=(8, 4), 
                                    tight_layout=True,
                                    axisoff=True, 
                                    savefig=dict(fname=buf, dpi=100, bbox_inches='tight', pad_inches=0.1)
                                )
                                
                                # Envia como Foto com Caption
                                global_notifier.enviar_foto(buf, msg, inline_keyboard=inline_kb)
                                
                                # SE SUCESSO NO ENVIO, SALVA NO JSON PARA NÃO REPETIR HOJE
                                SENT_ALERTS_TODAY[symbol] = {
                                    "data": hoje_str,
                                    "hora": current['time'].strftime('%H:%M'),
                                    "sinal": signal_text
                                }
                                save_alerts_state()
                            except Exception as env_erro:
                                print(f"❌ Erro ao enviar mensagem Telegram para {symbol}: {env_erro}")

                except Exception as e:
                    # Silencia erros individuais para nao flodar o log, ou imprime so o simbolo
                    # print(f"❌ [Monitor] Erro em {symbol}: {e}")
                    pass
                
                # Pequeno delay entre ativos para não travar CPU/MT5
                time.sleep(0.1)

                # Checa novamente após pequeno delay para permitir parada imediata
                if not BOT_RUNNING:
                    print("💤 [Monitor] Parada solicitada durante o ciclo; saindo imediatamente.")
                    break

            # Aguarda fim do ciclo
            print(f"💤 [Monitor] Ciclo finalizado. Aguardando 60s...")
            sleep_seconds = 60
            # Durante a espera, permita desligar mais responsivo
            for _ in range(int(sleep_seconds)):
                if not BOT_RUNNING:
                    break
                time.sleep(1)

# Inicia a thread de monitoramento apenas se não for o reloader do Flask (para não duplicar)
if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or __name__ == "__main__":
    import atexit
    
    def on_shutdown():
        if BOT_RUNNING:
            msg = "🛑 *ALERTA CRÍTICO!*\n\nO servidor do seu Robô (Python) foi fechado ou reiniciado manualmente.\nO monitoramento de ativos foi **interrompido**!"
            try:
                global_notifier.enviar_mensagem(msg)
            except:
                pass
                
    atexit.register(on_shutdown)

    monitor_thread = threading.Thread(target=run_telegram_monitor, daemon=True)
    monitor_thread.start()



# Conexão MT5 forçada agora ocorre no início do arquivo.

from utils.asset_filter import load_clean_assets

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/dashboard')
def dashboard():
    assets_data = load_clean_assets()
    
    # Flatten dictionary to list for the datalist in frontend
    # Prioritizing Indices then Stocks
    if isinstance(assets_data, dict):
        assets = assets_data.get("Indices", []) + assets_data.get("Acoes", [])
    else:
        assets = assets_data
        
    return render_template('index.html', assets=assets)

def format_rates(rates):
    data = []
    for r in rates:
        data.append({
            "time": int(r['time']),
            "open": float(r['open']),
            "high": float(r['high']),
            "low": float(r['low']),
            "close": float(r['close'])
        })
    return data


# Mapeamento de Timeframes
TIMEFRAMES = {
    "M1": mt5.TIMEFRAME_M1,
    "M2": mt5.TIMEFRAME_M2,
    "M3": mt5.TIMEFRAME_M3,
    "M4": mt5.TIMEFRAME_M4,
    "M5": mt5.TIMEFRAME_M5,
    "M6": mt5.TIMEFRAME_M6,
    "M10": mt5.TIMEFRAME_M10,
    "M12": mt5.TIMEFRAME_M12,
    "M15": mt5.TIMEFRAME_M15,
    "M20": mt5.TIMEFRAME_M20,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H2": mt5.TIMEFRAME_H2,
    "H3": mt5.TIMEFRAME_H3,
    "H4": mt5.TIMEFRAME_H4,
    "H6": mt5.TIMEFRAME_H6,
    "H8": mt5.TIMEFRAME_H8,
    "H12": mt5.TIMEFRAME_H12,
    "D1": mt5.TIMEFRAME_D1,
    "W1": mt5.TIMEFRAME_W1,
    "MN1": mt5.TIMEFRAME_MN1
}

@app.route('/api/history')
def get_history():
    symbol = request.args.get('symbol', 'WINJ26')
    tf_str = request.args.get('timeframe', 'M5')
    count = int(request.args.get('count', 1000))
    
    # 0. Check connection
    connected, err = ensure_mt5_connected()
    if not connected:
        return jsonify({"error": f"Erro de conexão com MT5. Certifique-se que o terminal está aberto. Erro: {err}"}), 503

    timeframe = TIMEFRAMES.get(tf_str, mt5.TIMEFRAME_M5)
    
    # Garante que o simbolo esta selecionado no Market Watch
    if not mt5.symbol_select(symbol, True):
        print(f"Falha ao selecionar {symbol}, tentando mesmo assim...")

    # Pega 'count' velas do timeframe escolhido
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    
    if rates is None or len(rates) == 0:
        err = mt5.last_error()
        print(f"Erro ao pegar histórico para {symbol}. Code={err}")
        return jsonify({"error": f"Sem dados de histórico para {symbol}. MT5 Error: {err}"}), 404
        
    data = format_rates(rates)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Enviando histórico {tf_str} ({len(data)} velas) de {symbol}")
    
    return jsonify(data)

@app.route('/api/candle')
def get_candle():
    symbol = request.args.get('symbol', 'WINJ26')
    tf_str = request.args.get('timeframe', 'M5')
    
    # Parametros SMA (se nao vier, usa padrao mas nao retorna erro)
    short_window = int(request.args.get('short', 20))
    long_window = int(request.args.get('long', 50))
    
    # 0. Check connection
    connected, err = ensure_mt5_connected()
    if not connected:
        return jsonify({"error": "Erro de conexão com MT5"}), 503

    timeframe = TIMEFRAMES.get(tf_str, mt5.TIMEFRAME_M5)
    
    # Precisa de historico suficiente para calcular a SMA Longa
    # Pega Long + Buffer (ex: +10 velas)
    count = long_window + 10
    
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    
    if rates is None or len(rates) == 0:
        return jsonify({"error": "Sem dados"}), 404
        
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Calculate SMA
    df['SMA_Short'] = df['close'].rolling(window=short_window).mean()
    df['SMA_Long'] = df['close'].rolling(window=long_window).mean()
    
    # Pega ultima vela (LIVE) para o grafico de precos
    last_row = df.iloc[-1]
    candle_data = {
        "time": int(last_row['time'].value // 10**9) if isinstance(last_row['time'], pd.Timestamp) else int(last_row['time']),
        "open": float(last_row['open']),
        "high": float(last_row['high']),
        "low": float(last_row['low']),
        "close": float(last_row['close'])
    }
    
    # Pega penultima vela (FECHADA) para a SMA
    # Se o usuario quer "apenas na passagem", o dado mais confiavel eh o da vela anterior fechada
    prev_row = df.iloc[-2] if len(df) > 1 else last_row
    
    sma_data = {
        "time": int(prev_row['time'].value // 10**9) if isinstance(prev_row['time'], pd.Timestamp) else int(prev_row['time']),
        "short": float(prev_row['SMA_Short']) if not pd.isna(prev_row['SMA_Short']) else None,
        "long": float(prev_row['SMA_Long']) if not pd.isna(prev_row['SMA_Long']) else None
    }
    
    response = jsonify({
        "candle": candle_data,
        "sma": sma_data
    })
    response.headers.add("Cache-Control", "no-cache, no-store, must-revalidate")
    response.headers.add("Pragma", "no-cache")
    response.headers.add("Expires", "0")
    
    # Debug print to confirm request (SILENCIADO a pedido do usuário)
    # print(f"[{datetime.now().strftime('%H:%M:%S')}] Enviando tick: {candle_data['close']}")
    
    return response

@app.route('/api/timeframes')
def get_timeframes():
    return jsonify(list(TIMEFRAMES.keys()))


# --- BOT CONTROL ROUTES ---
@app.route('/api/bot/start', methods=['POST'])
def bot_start():
    """Ativa o bot de alertas (liga o loop)."""
    global BOT_RUNNING, BOT_START_TIME
    BOT_RUNNING = True
    
    # Define o Marco Zero respeitando o fechamento da B3 (18:00)
    # Se o usuário ligar o bot DEPOIS das 18h, voltamos o relógio do start para 17:00
    # para não ignorar as últimas velas do leilão e fechamento do dia!
    now = datetime.now()
    if now.hour >= 18:
        BOT_START_TIME = now.replace(hour=17, minute=0, second=0, microsecond=0)
    else:
        BOT_START_TIME = now
        
    print(f"🚀 [Monitor] Bot Iniciado via API (BOT_RUNNING=True, START_TIME={BOT_START_TIME})")
    
    # Enviar notificação no Telegram
    msg = "🚀 **MONITORAMENTO INICIADO!**\n\nO robô de alertas foi ativado e está rastreando cruzamentos de médias nos ativos configurados."
    global_notifier.enviar_mensagem(msg)
    
    return jsonify({"message": "Bot Iniciado", "running": True})


@app.route('/api/bot/stop', methods=['POST'])
def bot_stop():
    """Pausa o bot de alertas (desliga o loop)."""
    global BOT_RUNNING
    BOT_RUNNING = False
    print("💤 [Monitor] Bot Pausado via API (BOT_RUNNING=False)")
    
    # Enviar notificação no Telegram
    msg = "💤 **MONITORAMENTO PAUSADO!**\n\nO robô de alertas foi desativado. Você não receberá mais notificações de sinais até ligá-lo novamente."
    global_notifier.enviar_mensagem(msg)
    
    return jsonify({"message": "Bot Pausado", "running": False})


@app.route('/api/bot/status')
def bot_status():
    """Retorna status atual do bot para o frontend."""
    return jsonify({"running": bool(BOT_RUNNING)})

# --- BACKTESTING ROUTES ---

# --- BACKTESTING ROUTES ---
from backtester import strategy_sma_crossover, calculate_metrics_advanced, calculate_trade_stats, optimize_sma

@app.route('/api/backtest')
def run_backtest():
    symbol = request.args.get('symbol', 'WINJ26')
    tf_str = request.args.get('timeframe', 'M5')
    count = int(request.args.get('count', 1000))
    short_window = int(request.args.get('short', 20))
    long_window = int(request.args.get('long', 50))
    do_optimize = request.args.get('optimize', 'false').lower() == 'true'
    
    # 0. Check connection
    connected, err = ensure_mt5_connected()
    if not connected:
        return jsonify({"error": f"Erro de conexão com MT5: {err}"}), 503

    timeframe = TIMEFRAMES.get(tf_str, mt5.TIMEFRAME_M5)
    
    # Garante que o simbolo esta selecionado
    mt5.symbol_select(symbol, True)
    
    # 1. Fetch Data
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None or len(rates) == 0:
        err = mt5.last_error()
        return jsonify({"error": f"No data found. MT5 Error: {err}"}), 404
        
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    
    # 2. Optimization (Optional)
    best_params = None
    if do_optimize:
        # returns (short, long)
        opt_short, opt_long = optimize_sma(df)
        short_window, long_window = opt_short, opt_long
        best_params = {"short": short_window, "long": long_window}

    # 3. Run Strategy
    # strategy_sma_crossover espera colunas 'close' que já existem no df do MT5 (lowercase)
    df_res = strategy_sma_crossover(df, short_window, long_window)
    
    
    # 3. Calculate Advanced Metrics (FULL DATASET)
    metrics = calculate_metrics_advanced(df_res['Strategy_Returns'])
    trade_stats = calculate_trade_stats(df_res)
    
    # 5. Prepare Chart Data
    
    # SMA Lines
    sma_short_data = []
    sma_long_data = []
    
    for idx, row in df_res.iterrows():
        ts = int(idx.value // 10**9) if isinstance(idx, pd.Timestamp) else int(row['time'].value // 10**9) if isinstance(row['time'], pd.Timestamp) else int(row['time'])
        
        if not pd.isna(row['SMA_Short']):
            sma_short_data.append({"time": ts, "value": float(row['SMA_Short'])})
            
        if not pd.isna(row['SMA_Long']):
            sma_long_data.append({"time": ts, "value": float(row['SMA_Long'])})

    # Markers (Buy/Sell)
    markers = []
    trade_signal = df_res['Signal'].diff().fillna(0)
    
    # Identify Buy/Sell rows
    buys = df_res[trade_signal == 1]
    sells = df_res[trade_signal == -1]
    
    for idx, row in buys.iterrows():
        ts = int(row['time'].value // 10**9) if isinstance(row['time'], pd.Timestamp) else int(row['time'])
        markers.append({
            "time": ts,
            "position": "belowBar",
            "color": "#00E5FF", # Neon Cyan
            "shape": "arrowUp",
            "text": "Buy"
        })
        
    for idx, row in sells.iterrows():
        ts = int(row['time'].value // 10**9) if isinstance(row['time'], pd.Timestamp) else int(row['time'])
        markers.append({
            "time": ts,
            "position": "aboveBar",
            "color": "#FF9100", # Neon Orange
            "shape": "arrowDown",
            "text": "Sell"
        })
    
    # CRITICAL: Sort markers by time. Lightweight Charts requires sorted markers.
    markers.sort(key=lambda x: x['time'])
        
    # Fix candle time serialization in candles dict
    candles_dict = df_res[['time', 'open', 'high', 'low', 'close']].copy()
    candles_dict['time'] = candles_dict['time'].apply(lambda x: int(x.value // 10**9) if isinstance(x, pd.Timestamp) else int(x))
    
    return jsonify({
        "metrics": metrics,
        "trade_stats": trade_stats,
        "sma_short": sma_short_data,
        "sma_long": sma_long_data,
        "markers": markers,
        "best_params": best_params,
        "candles": candles_dict.to_dict('records') # Send Candle Data
    })

@app.route('/api/backtest_scalper')
def run_backtest_scalper():
    symbol = request.args.get('symbol', 'WINJ26')
    tf_str = request.args.get('timeframe', 'M1')
    
    connected, err = ensure_mt5_connected()
    if not connected:
        return jsonify({"error": f"Erro MT5: {err}"}), 503

    mt5.symbol_select(symbol, True)
    
    timeframe = TIMEFRAMES.get(tf_str, mt5.TIMEFRAME_M1)
    
    # Define data_inicio como 18/02/2026 00:00 (UTC do terminal geralmente)
    # data_fim como o momento atual
    data_inicio = datetime(2026, 2, 18, 0, 0)
    data_fim = datetime.now()

    # Busca dados por Range
    rates = mt5.copy_rates_range(symbol, timeframe, data_inicio, data_fim)
    if rates is None or len(rates) == 0:
        err = mt5.last_error()
        return jsonify({"error": f"Sem dados para o período selecionado ({data_inicio} até {data_fim}). MT5 Error: {err}"}), 404
        
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')

    # Auditoria de Retorno
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Buscando dados de {data_inicio} até {data_fim}. Velas encontradas: {len(df)}")
    
    # 1. Análise de Volatilidade (Tamanho Médio do Candle)
    df['time_only'] = df['time'].dt.time
    from datetime import time as dt_time
    hora_inicio = dt_time(9, 15)
    hora_fim = dt_time(12, 30)

    # Filtra candles pelo horário operacional
    df_operacional = df[(df['time_only'] >= hora_inicio) & (df['time_only'] <= hora_fim)].copy()
    if not df_operacional.empty:
        df_operacional['candle_size'] = df_operacional['high'] - df_operacional['low']
        tamanho_medio_candle = round(df_operacional['candle_size'].mean(), 2)
    else:
        tamanho_medio_candle = 0.0

    # Calcula VWAP Diária (Reset a cada dia) para usar no backtest
    df['date'] = df['time'].dt.date
    df['Typical_Price'] = (df['high'] + df['low'] + df['close']) / 3
    df['Vol_x_TP'] = df['tick_volume'] * df['Typical_Price']
    df['Cum_Vol_x_TP'] = df.groupby('date')['Vol_x_TP'].cumsum()
    df['Cum_Vol'] = df.groupby('date')['tick_volume'].cumsum()
    df['VWAP'] = df['Cum_Vol_x_TP'] / df['Cum_Vol']

    # Captura Stop Loss e Take Profit manuais do usuário
    try:
        sl_manual = float(request.args.get('sl', 150))
        tp_manual = float(request.args.get('tp', 300))
    except (ValueError, TypeError):
        sl_manual = 150.0
        tp_manual = 300.0

    # Média de 9 (Exponencial) e 21 (Simples)
    df['EMA9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['SMA21'] = df['close'].rolling(window=21).mean()
    
    # Variáveis de Simulação (Iteração Visual Original)
    in_position = False
    trade_type = None # 'BUY' ou 'SELL'
    entry_price = 0.0
    
    total_trades = 0
    win_count = 0
    total_profit_pts = 0.0
    
    gross_profit_pts = 0.0
    gross_loss_pts = 0.0
    consecutive_losses = 0
    max_consecutive_losses = 0
    
    max_drawdown_rs = 0.0
    peak_rs = 0.0
    current_balance_rs = 0.0
    
    current_trade_date = None
    trades_today = 0
    
    for i in range(2, len(df)):
        row = df.iloc[i]
        ts_current = int(row['time'].value // 10**9) if isinstance(row['time'], pd.Timestamp) else int(row['time'])
        
        # Reseta contador de trades diários
        row_date = row['date']
        if current_trade_date != row_date:
            current_trade_date = row_date
            trades_today = 0
        
        if in_position:
            # Check TP/SL
            high = row['high']
            low = row['low']
            closed_trade = False
            profit_pts = 0.0
            
            # SL = 100, TP = 200 (em simulação conservadora, se ambos atingirem, assumimos SL)
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
                    gross_profit_pts += profit_pts
                    consecutive_losses = 0
                else:
                    gross_loss_pts += abs(profit_pts)
                    consecutive_losses += 1
                    if consecutive_losses > max_consecutive_losses:
                        max_consecutive_losses = consecutive_losses
                        
                total_profit_pts += profit_pts
                
                # Atualiza Drawdown (em R$ 0.20 por ponto)
                current_balance_rs = total_profit_pts * 0.20
                if current_balance_rs > peak_rs:
                    peak_rs = current_balance_rs
                
                dd = peak_rs - current_balance_rs
                if dd > max_drawdown_rs:
                    max_drawdown_rs = dd
                    
            continue 
            
        # Não posicionado: Procura entrada
        hora_atual = row['time_only']
        
        # Só opera na golden zone e se não bateu o limite de 3 trades no dia
        if hora_inicio <= hora_atual <= hora_fim and trades_today < 3:
            # Lógica da vela fechada (i-1 = vela que acabou de fechar, i-2 = anterior a ela)
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
            
            # Sinal de COMPRA: EMA9 passa pra cima E o preço atual está acima do VWAP
            if cross_up and c_close > c_vwap:
                in_position = True
                trade_type = 'BUY'
                entry_price = row['open']
                trades_today += 1
                df.at[df.index[i], 'trade_signal'] = 'BUY'

            # Sinal de VENDA: EMA9 passa pra baixo E o preço atual está abaixo do VWAP
            elif cross_down and c_close < c_vwap:
                in_position = True
                trade_type = 'SELL'
                entry_price = row['open']
                trades_today += 1
                df.at[df.index[i], 'trade_signal'] = 'SELL'

    lucro_total_rs = total_profit_pts * 0.20
    gross_profit_rs = gross_profit_pts * 0.20
    gross_loss_rs = gross_loss_pts * 0.20
    
    winrate = (win_count / total_trades * 100) if total_trades > 0 else 0.0
    profit_factor = (gross_profit_rs / gross_loss_rs) if gross_loss_rs > 0 else (999.99 if gross_profit_rs > 0 else 0.0)
    media_por_trade = (lucro_total_rs / total_trades) if total_trades > 0 else 0.0

    # ----- PREPARAÇÃO DOS DADOS VISUAIS (CHART) -----
    
    # 1. Candles
    candles_list = []
    for _, row in df.iterrows():
        ts = int(row['time'].value // 10**9) if isinstance(row['time'], pd.Timestamp) else int(row['time'])
        candles_list.append({
            "time": ts,
            "open": float(row['open']),
            "high": float(row['high']),
            "low": float(row['low']),
            "close": float(row['close'])
        })
        
    # 2. Indicadores (EMA Fast, EMA Slow, VWAP)
    indicators_list = []
    for _, row in df.iterrows():
        ts = int(row['time'].value // 10**9) if isinstance(row['time'], pd.Timestamp) else int(row['time'])
        indicators_list.append({
            "time": ts,
            "ema9": float(row['EMA9']) if not pd.isna(row['EMA9']) else None,
            "sma21": float(row['SMA21']) if not pd.isna(row['SMA21']) else None,
            "vwap": float(row['VWAP']) if not pd.isna(row['VWAP']) else None
        })
        
    # 3. Markers (Setas de Compra/Venda)
    markers_list = []
    if 'trade_signal' in df.columns:
        trades_df = df.dropna(subset=['trade_signal'])
        for _, row in trades_df.iterrows():
            ts = int(row['time'].value // 10**9) if isinstance(row['time'], pd.Timestamp) else int(row['time'])
            action = row['trade_signal']
            
            if action == 'BUY':
                markers_list.append({
                    "time": ts,
                    "position": "belowBar",
                    "color": "#00E676",
                    "shape": "arrowUp",
                    "text": "COMPRA",
                    "size": 2
                })
            elif action == 'SELL':
                markers_list.append({
                    "time": ts,
                    "position": "aboveBar",
                    "color": "#FF5252",
                    "shape": "arrowDown",
                    "text": "VENDA",
                    "size": 2
                })
            elif action == 'WIN_BUY':
                markers_list.append({
                    "time": ts,
                    "position": "aboveBar",
                    "color": "#00E676",
                    "shape": "circle",
                    "text": f"TP (+R$ {tp_manual * 0.20:.0f})",
                    "size": 1
                })
            elif action == 'LOSS_BUY':
                markers_list.append({
                    "time": ts,
                    "position": "belowBar",
                    "color": "#FF5252",
                    "shape": "circle",
                    "text": f"SL (-R$ {sl_manual * 0.20:.0f})",
                    "size": 1
                })
            elif action == 'WIN_SELL':
                markers_list.append({
                    "time": ts,
                    "position": "belowBar",
                    "color": "#00E676",
                    "shape": "circle",
                    "text": f"TP (+R$ {tp_manual * 0.20:.0f})",
                    "size": 1
                })
            elif action == 'LOSS_SELL':
                markers_list.append({
                    "time": ts,
                    "position": "aboveBar",
                    "color": "#FF5252",
                    "shape": "circle",
                    "text": f"SL (-R$ {sl_manual * 0.20:.0f})",
                    "size": 1
                })

    return jsonify({
        "total_trades": total_trades,
        "winrate": round(winrate, 1),
        "lucro_total": round(lucro_total_rs, 2),
        "max_drawdown": round(max_drawdown_rs, 2),
        "profit_factor": round(profit_factor, 2),
        "media_por_trade": round(media_por_trade, 2),
        "max_consecutive_losses": max_consecutive_losses,
        "tamanho_medio_candle": tamanho_medio_candle,

        "candles": candles_list,
        "indicators": indicators_list,
        "markers": markers_list
    })

@app.route('/api/batch_backtest', methods=['POST'])
def batch_backtest():
    import time
    import json
    from flask import Response, stream_with_context
    
    req = request.get_json()
    
    timeframe_str = req.get('timeframe', 'M5')
    count = int(req.get('candles', 1000))
    short_window = int(req.get('sma_short', 20))
    long_window = int(req.get('sma_long', 50))
    do_optimize = req.get('optimize', False)
    
    # Check connection once before starting the stream
    connected, err = ensure_mt5_connected()
    if not connected:
        def err_gen():
            yield json.dumps({"type": "progress", "value": 0, "text": f"Erro: MT5 desconectado ({err})"}) + "\n"
        return Response(stream_with_context(err_gen()), mimetype='application/x-ndjson')

    mt5_tf = TIMEFRAMES.get(timeframe_str, mt5.TIMEFRAME_M5)

    def generate():
        print(f"[{datetime.now()}] Iniciando gerador do Scanner...")
        
        # 0. Ping imediato para destravar o buffer do navegador
        yield json.dumps({"type": "progress", "value": 0, "text": "Conectado. Preparando..."}) + "\n"
        time.sleep(0.1) 

        # 1. Get Assets
        try:
            assets_data = load_clean_assets()
            if isinstance(assets_data, dict):
                assets = assets_data.get("Indices", []) + assets_data.get("Acoes", [])
            else:
                assets = assets_data
        except Exception as e:
            print(f"Erro ao carregar assets: {e}")
            yield json.dumps({"type": "progress", "value": 0, "text": f"Erro assets: {str(e)}"}) + "\n"
            return
            
        total_assets = len(assets)
        yield json.dumps({"type": "progress", "value": 0, "text": f"Iniciando scan de {total_assets} ativos..."}) + "\n"
        
        results = []
        processed_count = 0
        start_time = time.time()
        
        for i, symbol in enumerate(assets):
            processed_count += 1
            
            # Emitir progresso
            pct = int((processed_count / total_assets) * 100)
            yield json.dumps({"type": "progress", "value": pct, "text": f"[{processed_count}/{total_assets}] Analisando {symbol}..."}) + "\n"
            
            # Sleep pequeno para permitir que o servidor envie o buffer e não trave a thread
            time.sleep(0.01) 
            
            try:
                # Select symbol
                selected = mt5.symbol_select(symbol, True)
                if not selected:
                    # Tenta forçar adicionar se não estiver no Market Watch
                    # (Alguns MT5 precisam disso)
                    continue

                rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, count)
                if rates is None or len(rates) < long_window + 10:
                    continue
                
                df = pd.DataFrame(rates)
                if 'close' not in df.columns:
                    continue

                # Run Logic
                current_short = short_window
                current_long = long_window

                if do_optimize:
                     opt_short, opt_long = optimize_sma(df)
                     current_short = opt_short
                     current_long = opt_long

                df_res = strategy_sma_crossover(df, current_short, current_long)
                
                trade_stats = calculate_trade_stats(df_res)
                if trade_stats['total_trades'] == 0:
                    continue
                    
                metrics = calculate_metrics_advanced(df_res['Strategy_Returns'])
                
                results.append({
                    "symbol": symbol,
                    "total_return": metrics['total_return'],
                    "win_rate": trade_stats['win_rate'],
                    "total_trades": trade_stats['total_trades'],
                    "profit_factor": trade_stats['profit_factor'],
                    "sharpe": metrics['sharpe'],
                    "params": {"short": current_short, "long": current_long} if do_optimize else None
                })
                
            except Exception as e:
                print(f"Erro ao processar {symbol}: {e}")
                continue

        # Sort and Finish
        results.sort(key=lambda x: x['total_return'], reverse=True)
        elapsed = time.time() - start_time
        
        final_msg = f"Finalizado em {elapsed:.1f}s. {len(results)} ativos qualificados."
        yield json.dumps({"type": "progress", "value": 100, "text": final_msg}) + "\n"
        
        # Send Data
        yield json.dumps({"type": "result", "data": results}) + "\n"

    response = Response(stream_with_context(generate()), mimetype='application/x-ndjson')
    response.headers['X-Accel-Buffering'] = 'no'  # Nginx/Proxy buffering
    response.headers['Cache-Control'] = 'no-cache' # Browser caching
    return response

if __name__ == '__main__':
    import subprocess
    import sys
    import atexit
    import signal
    import platform
    
    # Auto-start scalper script in background
    print("🚀 Iniciando Módulo Scalper em plano de fundo...")
    scalper_process = None
    try:
        # Popen roda sem travar o Flask
        # Em Windows evitamos que o Ctrl+C mate tudo magicamente e cause bugs, 
        # e tratamos no atexit
        import os
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scalper_win.py")
        
        # Inicia o subprocesso forçando o flush do Python (unbuffered)
        my_env = os.environ.copy()
        my_env["PYTHONUNBUFFERED"] = "1"
        
        scalper_process = subprocess.Popen(
            [sys.executable, script_path], 
            env=my_env,
            stdout=sys.stdout, 
            stderr=sys.stderr
        )
        print(f"✅ Scalper iniciado com PID: {scalper_process.pid} ({script_path})", flush=True)
        
        # Sistema Anti-Zumbi
        def kill_scalper(*args):
            if scalper_process:
                print(f"🛑 [Graceful Shutdown] Encerrando o Robô Scalper (PID: {scalper_process.pid})...")
                scalper_process.terminate()
                try:
                    scalper_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    scalper_process.kill() # Força parada se rejeitar terminação suave
                print("💀 Zumbi Eliminado!")

        # Registra a captura da saída normal e comandos de teclado (Ctrl+C)
        atexit.register(kill_scalper)
        signal.signal(signal.SIGINT, kill_scalper)  # Ctrl+C
        signal.signal(signal.SIGTERM, kill_scalper) # Finalização do terminal

    except Exception as e:
        print(f"❌ Falha ao iniciar Scalper: {e}")
        
    print("🚀 Servidor PoC WINJ26 rodando em http://localhost:5002")
    try:
        app.run(debug=True, port=5002, use_reloader=False) # Important: Turn off reloader to avoid opening 2 scalpers!
    except KeyboardInterrupt:
        # O KeyboardInterrupt será capturado e processado pelos signals acima
        pass

