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

@app.route('/')
def index():
    return render_template('index.html')

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
    
    # Pega 'count' velas do timeframe escolhido
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    
    if rates is None or len(rates) == 0:
        print(f"Erro ao pegar histórico para {symbol}. Verifique se o ativo existe no Market Watch.")
        return jsonify({"error": f"Sem dados de histórico para {symbol}"}), 404
        
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

if __name__ == '__main__':
    print("🚀 Servidor PoC WING26 rodando em http://localhost:5002")
    app.run(debug=True, port=5002)
