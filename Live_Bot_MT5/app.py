from flask import Flask, render_template, jsonify, request
import MetaTrader5 as mt5
from datetime import datetime
import pandas as pd
import numpy as np


app = Flask(__name__)

# Se conecta ao MT5 ao iniciar
if not mt5.initialize():
    print("❌ Falha ao inicializar MT5")
else:
    print("✅ MT5 Conectado com sucesso")

from utils.asset_filter import load_clean_assets

@app.route('/')
def index():
    assets = load_clean_assets()
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
    "M1": mt5.TIMEFRAME_M1, "M2": mt5.TIMEFRAME_M2, "M3": mt5.TIMEFRAME_M3, "M4": mt5.TIMEFRAME_M4,
    "M5": mt5.TIMEFRAME_M5, "M6": mt5.TIMEFRAME_M6, "M10": mt5.TIMEFRAME_M10, "M12": mt5.TIMEFRAME_M12,
    "M15": mt5.TIMEFRAME_M15, "M20": mt5.TIMEFRAME_M20, "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1, "H2": mt5.TIMEFRAME_H2, "H3": mt5.TIMEFRAME_H3, "H4": mt5.TIMEFRAME_H4,
    "H6": mt5.TIMEFRAME_H6, "H8": mt5.TIMEFRAME_H8, "H12": mt5.TIMEFRAME_H12,
    "D1": mt5.TIMEFRAME_D1, "W1": mt5.TIMEFRAME_W1, "MN1": mt5.TIMEFRAME_MN1
}

# --- ASSET LIBRARY ---
BR_STOCKS = {
    "PETR4": "Petrobras", "VALE3": "Vale", "ITUB4": "Itaú", "BBDC4": "Bradesco", "BBAS3": "Banco do Brasil",
    "WEGE3": "WEG", "ABEV3": "Ambev", "JBSS3": "JBS", "ELET3": "Eletrobras", "RENT3": "Localiza",
    "GGBR4": "Gerdau", "SUZB3": "Suzano", "PRIO3": "Prio", "RDOR3": "Rede D'Or", "HAPV3": "Hapvida",
    "B3SA3": "B3", "RADL3": "RaiaDrogasil", "CSAN3": "Cosan", "VIVT3": "Vivo", "CMIG4": "Cemig",
    "LREN3": "Lojas Renner", "EQTL3": "Equatorial", "CPLE6": "Copel", "EMBR3": "Embraer", "TIMS3": "TIM"
}

CATEGORIES = {
    "🇧🇷 Ações Brasil (Top 25)": BR_STOCKS,
    "📈 Futuros": {"WIN$": "WIN (Série Contínua)", "WDO$": "WDO (Série Contínua)"},
    "📋 Todos os Ativos (Base Completa)": {t: t for t in load_clean_assets()}
}

def clean_for_json(obj):
    if isinstance(obj, dict): return {k: clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list): return [clean_for_json(i) for i in obj]
    elif isinstance(obj, (float, np.float64, np.float32)):
        return 0.0 if (np.isnan(obj) or np.isinf(obj)) else float(obj)
    elif isinstance(obj, (int, np.int64, np.int32)): return int(obj)
    return obj


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
    
    # CRITICAL: Sort markers by time.
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

@app.route('/api/assets', methods=['GET'])
def get_assets_categories():
    return jsonify(CATEGORIES)

@app.route('/api/batch_backtest', methods=['POST'])
def run_batch_backtest():
    try:
        data_req = request.json
        category_key = data_req.get('category')
        
        # Determine ticker list
        tickers_map = {}
        if category_key and category_key in CATEGORIES:
            tickers_map = CATEGORIES[category_key]
        else:
            # Fallback or "All" logic from local CSV if needed
            tickers_map = {t: t for t in load_clean_assets()}

        sma_short = int(data_req.get('sma_short', 20))
        sma_long = int(data_req.get('sma_long', 50))
        # Note: Timeframe for batch usually D1, but let's allow parameter
        tf_str = data_req.get('timeframe', 'D1')
        timeframe = TIMEFRAMES.get(tf_str, mt5.TIMEFRAME_D1)
        
        # Count or Date Range? API usually sends start/end date, but MT5 copy_rates logic 
        # is easier with count for quick tests, OR dates.
        # Let's support count for speed in batch, mirroring single test
        count = int(data_req.get('count', 1000))
        
        results = []
        total_assets = len(tickers_map)
        print(f"🔄 Iniciando Batch para {total_assets} ativos. TF: {tf_str}")
        print(f"📋 Filtro usado: {category_key if category_key else 'Todos (CSV detectado)'}")

        current_idx = 0
        for ticker, name in tickers_map.items():
            current_idx += 1
            if current_idx % 5 == 0 or current_idx == 1 or current_idx == total_assets:
                print(f"   [{current_idx}/{total_assets}] Processando {ticker}...")

            # 1. Select Symbol
            if not mt5.symbol_select(ticker, True):
                # Try adding '.SA' if missing and failing?
                # For now assume ticker is correct
                print(f"   ⚠️ Falha ao selecionar {ticker}")
                continue
            
            # 2. Fetch Data
            rates = mt5.copy_rates_from_pos(ticker, timeframe, 0, count)
            if rates is None or len(rates) < 100:
                # Silently skip bad data to reduce noise, or log debug
                continue
                
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # 3. Strategy
            try:
                # strategy_sma_crossover expect lowercase 'close' which we have from copy_rates_from_pos
                res = strategy_sma_crossover(df, short_window=sma_short, long_window=sma_long)
                
                # 4. Split
                limit = int(len(res) * 0.7) # Using 70/30 like the single test
                res_oos = res.iloc[limit:].copy()
                
                # 5. Metrics
                m_oos = calculate_metrics_advanced(res_oos['Strategy_Returns'])
                
                results.append({
                    "ticker": ticker,
                    "name": name,
                    "return_out": m_oos.get('total_return', 0),
                    "sharpe_out": m_oos.get('sharpe', 0),
                    "drawdown_out": m_oos.get('max_drawdown', 0)
                })
            except Exception as e:
                print(f"   ❌ Erro em {ticker}: {e}")
                continue
        
        print(f"✅ Batch finalizado. {len(results)} ativos retornados com sucesso.")
        
        # Sort by Return Descending
        results.sort(key=lambda x: x['return_out'], reverse=True)
        
        return jsonify(clean_for_json(results))

    except Exception as e:
        print(f"Batch Error: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("🚀 Servidor PoC WING26 rodando em http://localhost:5002")
    app.run(debug=True, port=5002)
