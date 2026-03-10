import requests
import json
import traceback

try:
    print("Requesting API...")
    res = requests.get('http://127.0.0.1:5000/api/backtest_scalper?timeframe=M5&symbol=WINJ26')
    print("Status Code:", res.status_code)
    
    if res.status_code == 200:
        data = res.json()
        print("Keys returned:", data.keys())
        print("Total Trades:", data.get('total_trades'))
        print("Len Candles:", len(data.get('candles', [])))
        print("Len Indicators:", len(data.get('indicators', [])))
        
        # Verify if indicators list has any NaNs or weird values
        inds = data.get('indicators', [])
        valid_vwap = [i for i in inds if i.get('vwap') is not None]
        print(f"Candles with valid VWAP: {len(valid_vwap)}")
    else:
        print("Error Response:", res.text)
except Exception as e:
    print("Exception!")
    traceback.print_exc()
