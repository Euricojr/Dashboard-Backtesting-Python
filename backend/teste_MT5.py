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
    return render_template('teste_live.html')

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

@app.route('/api/history')
def get_history():
    symbol = request.args.get('symbol', 'WING26')
    # Pega 1000 velas de M5 (5 minutos)
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 1000)
    
    if rates is None or len(rates) == 0:
        print(f"Erro ao pegar histórico para {symbol}. Verifique se o ativo existe no Market Watch.")
        return jsonify({"error": f"Sem dados de histórico para {symbol}"}), 404
        
    data = format_rates(rates)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Enviando histórico M5 ({len(data)} velas) de {symbol}")
    
    return jsonify(data)

@app.route('/api/candle')
def get_candle():
    symbol = request.args.get('symbol', 'WING26')
    
    # Pega apenas a ultima vela (1) de M5
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 1)
    
    if rates is None or len(rates) == 0:
        return jsonify({"error": "Sem dados"}), 404
        
    data = format_rates(rates)
    
    # Retorna objeto único para o update
    return jsonify(data[0])

if __name__ == '__main__':
    print("🚀 Servidor PoC WING26 rodando em http://localhost:5002")
    app.run(debug=True, port=5002)
