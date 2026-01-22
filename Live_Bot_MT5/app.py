from flask import Flask, render_template, jsonify, request
import MetaTrader5 as mt5
from datetime import datetime
import pandas as pd

app = Flask(__name__)

# Se conecta ao MT5 ao iniciar
if not mt5.initialize():
    print("❌ Falha ao inicializar MT5")
else:
    print("✅ MT5 Conectado com sucesso")

from utils.asset_filter import load_clean_assets

@app.route('/')
def index():
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
    symbol = request.args.get('symbol', 'WING26')
    tf_str = request.args.get('timeframe', 'M5')
    count = int(request.args.get('count', 1000))
    
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
    symbol = request.args.get('symbol', 'WING26')
    tf_str = request.args.get('timeframe', 'M5')
    
    timeframe = TIMEFRAMES.get(tf_str, mt5.TIMEFRAME_M5)
    
    # Pega apenas a ultima vela (1) do timeframe escolhido
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 1)
    
    if rates is None or len(rates) == 0:
        return jsonify({"error": "Sem dados"}), 404
        
    data = format_rates(rates)
    
    # Retorna objeto único para o update
    return jsonify(data[0])

@app.route('/api/timeframes')
def get_timeframes():
    return jsonify(list(TIMEFRAMES.keys()))

# --- BACKTESTING ROUTES ---
from backtester import strategy_sma_crossover, calculate_metrics_advanced, calculate_trade_stats

@app.route('/api/backtest')
def run_backtest():
    symbol = request.args.get('symbol', 'WING26')
    tf_str = request.args.get('timeframe', 'M5')
    count = int(request.args.get('count', 1000))
    short_window = int(request.args.get('short', 20))
    long_window = int(request.args.get('long', 50))
    
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
    
    # 2. Run Strategy
    # strategy_sma_crossover espera colunas 'close' que já existem no df do MT5 (lowercase)
    df_res = strategy_sma_crossover(df, short_window, long_window)
    
    
    # 3. SPLIT TRAIN/TEST (70% Train, 30% Test)
    split_idx = int(len(df_res) * 0.7)
    df_in = df_res.iloc[:split_idx]
    df_out = df_res.iloc[split_idx:]
    
    # 4. Calculate Advanced Metrics for Both
    metrics_in = calculate_metrics_advanced(df_in['Strategy_Returns'])
    metrics_out = calculate_metrics_advanced(df_out['Strategy_Returns'])
    
    trade_stats_in = calculate_trade_stats(df_in)
    trade_stats_out = calculate_trade_stats(df_out)
    
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
        "metrics": {
            "in": metrics_in,
            "out": metrics_out
        },
        "trade_stats": {
            "in": trade_stats_in,
            "out": trade_stats_out
        },
        "sma_short": sma_short_data,
        "sma_long": sma_long_data,
        "markers": markers
    })

@app.route('/api/batch_backtest', methods=['POST'])
def batch_backtest():
    import time
    
    start_time = time.time()
    req = request.get_json()
    
    timeframe_str = req.get('timeframe', 'M5')
    count = int(req.get('candles', 1000))
    short_window = int(req.get('sma_short', 20))
    long_window = int(req.get('sma_long', 50))
    
    # 1. Get Assets
    assets_data = load_clean_assets()
    if isinstance(assets_data, dict):
        assets = assets_data.get("Indices", []) + assets_data.get("Acoes", [])
    else:
        assets = assets_data
        
    print(f"🔍 Escaneando {len(assets)} ativos (Sequencial)...")
    
    results = []
    
    # Pre-resolve timeframe logic
    mt5_tf = TIMEFRAMES.get(timeframe_str, mt5.TIMEFRAME_M5)
    
    # Sequential Execution to prevent MT5 IPC crashes
    processed_count = 0
    
    for symbol in assets:
        processed_count += 1
        if processed_count % 10 == 0:
            print(f"⏳ Processando {processed_count}/{len(assets)}: {symbol}...")
            
        try:
            # Select symbol
            selected = mt5.symbol_select(symbol, True)
            if not selected:
                continue

            rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, count)
            if rates is None or len(rates) < long_window + 10:
                continue
            
            df = pd.DataFrame(rates)
            # Basic validation
            if 'close' not in df.columns:
                continue

            # Run Logic
            # We don't need 'time' conversion for strategy calc, only for charts if needed
            # Optimization: Skip datetime conversion if not needed strictly for logic
            # But strategy_sma_crossover might not need it? It uses rolling on close.
            # But let's keep it safe.
            # df['time'] = pd.to_datetime(df['time'], unit='s') 
            
            df_res = strategy_sma_crossover(df, short_window, long_window)
            
            # Metrics
            # Only calc if we have signals?
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
                "sharpe": metrics['sharpe']
            })
            
        except Exception as e:
            print(f"Erro ao processar {symbol}: {e}")
            continue

    # Sort by Total Return Desc
    results.sort(key=lambda x: x['total_return'], reverse=True)
    
    elapsed = time.time() - start_time
    print(f"✅ Scan concluído em {elapsed:.2f}s. {len(results)} ativos encontrados.")
    
    return jsonify(results)

if __name__ == '__main__':
    print("🚀 Servidor PoC WING26 rodando em http://localhost:5002")
    app.run(debug=True, port=5002)
