import threading
import time
from flask import Flask, render_template, jsonify, request
import MetaTrader5 as mt5
from datetime import datetime
import pandas as pd
from utils.telegram_notifier import TelegramNotifier
import os

app = Flask(__name__)

# --- GLOBAL CONFIG & STATE ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
MONITOR_SYMBOL = "WINJ26" # Default monitored symbol (Deprecated in favor of full list)
MONITOR_TIMEFRAME = "H1" # Timeframe do Monitoramento (M1, M5, H1, etc)
LAST_SIGNAL_STATE = {} # Dict para guardar estado de cada ativo: { "WINJ26": 1, ... }
# Controle On/Off do bot de alertas Telegram
BOT_RUNNING = False

def run_telegram_monitor():
    """
    Função que roda em thread separada para monitorar cruzamento de médias
    e enviar alertas no Telegram.
    """
    global LAST_SIGNAL_STATE, BOT_RUNNING
    
    # Carrega lista de ativos
    from utils.asset_filter import load_clean_assets
    
    # Nota: não imprime nada enquanto o bot estiver desligado.
    
    # Aguarda até o usuário ligar o BOT via API antes de conectar/monitorar
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

        # Cria o notifier somente quando for realmente iniciar o monitor
        notifier = TelegramNotifier(token=TELEGRAM_TOKEN, chat_id=TELEGRAM_CHAT_ID)
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
                    
                    rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, 100)
                    if rates is None or len(rates) < 55: # Precisa de pelo menos 50 + buffer
                        continue

                    df = pd.DataFrame(rates)
                    df['time'] = pd.to_datetime(df['time'], unit='s')
                    
                    # 2. Calcula SMA 20 e 50
                    df['SMA_Short'] = df['close'].rolling(window=20).mean()
                    df['SMA_Long'] = df['close'].rolling(window=50).mean()
                    
                    # 3. Verifica Cruzamento
                    current = df.iloc[-1]
                    prev = df.iloc[-2]
                    
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
                                signal_text = "COMPRA (Golden Cross)"
                                new_state = 1
                        # Death Cross
                        elif p_short >= p_long and c_short < c_long:
                            if last_state != -1:
                                signal_text = "VENDA (Death Cross)"
                                new_state = -1
                                
                        if signal_text:
                            LAST_SIGNAL_STATE[symbol] = new_state
                            msg = (
                                f"🚀 **ALERTA FINSENSE** 🚀\n"
                                f"Ativo: {symbol}\n"
                                f"Sinal: {signal_text}\n"
                                f"Preço: {current['close']:.2f}\n"
                                f"Horário: {current['time'].strftime('%H:%M')}\n"
                                f"TF: {MONITOR_TIMEFRAME}"
                            )
                            print(f"\n⚡ [Monitor] ALERTA ENVIADO para {symbol}: {signal_text}")
                            notifier.enviar_mensagem(msg)

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
if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    monitor_thread = threading.Thread(target=run_telegram_monitor, daemon=True)
    monitor_thread.start()



# Helper para garantir conexão com MT5
def ensure_mt5_connected():
    # Verifica se já está inicializado e com terminal rodando
    try:
        if mt5.terminal_info() is None:
            print("🔄 Tentando inicializar MT5...")
            if not mt5.initialize():
                err = mt5.last_error()
                print(f"❌ Erro MT5 Initialize: {err}")
                return False, err
        return True, None
    except Exception as e:
        print(f"❌ Exception MT5: {e}")
        return False, str(e)

# Nota: não forçamos conexão com MT5 na inicialização.
# A conexão será efetuada quando o monitor for ligado via API (/api/bot/start).

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
        "time": int(last_row['time'].timestamp()),
        "open": float(last_row['open']),
        "high": float(last_row['high']),
        "low": float(last_row['low']),
        "close": float(last_row['close'])
    }
    
    # Pega penultima vela (FECHADA) para a SMA
    # Se o usuario quer "apenas na passagem", o dado mais confiavel eh o da vela anterior fechada
    prev_row = df.iloc[-2] if len(df) > 1 else last_row
    
    sma_data = {
        "time": int(prev_row['time'].timestamp()),
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
    
    # Debug print to confirm request
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Enviando tick: {candle_data['close']}")
    
    return response

@app.route('/api/timeframes')
def get_timeframes():
    return jsonify(list(TIMEFRAMES.keys()))


# --- BOT CONTROL ROUTES ---
@app.route('/api/bot/start', methods=['POST'])
def bot_start():
    """Ativa o bot de alertas (liga o loop)."""
    global BOT_RUNNING
    BOT_RUNNING = True
    print("🚀 [Monitor] Bot Iniciado via API (BOT_RUNNING=True)")
    return jsonify({"message": "Bot Iniciado", "running": True})


@app.route('/api/bot/stop', methods=['POST'])
def bot_stop():
    """Pausa o bot de alertas (desliga o loop)."""
    global BOT_RUNNING
    BOT_RUNNING = False
    print("💤 [Monitor] Bot Pausado via API (BOT_RUNNING=False)")
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
        ts = int(idx.timestamp()) if isinstance(idx, pd.Timestamp) else int(row['time'].timestamp())
        
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
        ts = int(row['time'].timestamp())
        markers.append({
            "time": ts,
            "position": "belowBar",
            "color": "#00E5FF", # Neon Cyan
            "shape": "arrowUp",
            "text": "Buy"
        })
        
    for idx, row in sells.iterrows():
        ts = int(row['time'].timestamp())
        markers.append({
            "time": ts,
            "position": "aboveBar",
            "color": "#FF9100", # Neon Orange
            "shape": "arrowDown",
            "text": "Sell"
        })
    
    # CRITICAL: Sort markers by time. Lightweight Charts requires sorted markers.
    markers.sort(key=lambda x: x['time'])
        
    return jsonify({
        "metrics": metrics,
        "trade_stats": trade_stats,
        "sma_short": sma_short_data,
        "sma_long": sma_long_data,
        "markers": markers,
        "best_params": best_params,
        "candles": df_res[['time', 'open', 'high', 'low', 'close']].rename(columns={'time': 'time'}).to_dict('records') # Send Candle Data
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
    print("🚀 Servidor PoC WINJ26 rodando em http://localhost:5002")
    app.run(debug=True, port=5002)
