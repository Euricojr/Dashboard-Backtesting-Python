import requests
import time
import sys

# URL da API
URL = "http://localhost:5002/api/candle?symbol=WINJ26&timeframe=M5"

print(f"📡 Testando endpoint de Candle: {URL}")
print("Pressione Ctrl+C para parar.")

last_price = None

try:
    for i in range(5):
        try:
            r = requests.get(URL, timeout=2)
            if r.status_code == 200:
                data = r.json()
                candle = data.get('candle')
                price = candle.get('close')
                time_ts = candle.get('time')
                
                print(f"[{time.strftime('%H:%M:%S')}] Preço: {price} | Time: {time_ts}")
                
                if last_price and price != last_price:
                    print(f"   ⚡ Preço mudou! {last_price} -> {price}")
                
                last_price = price
            else:
                print(f"❌ Erro {r.status_code}: {r.text}")
        except Exception as e:
            print(f"❌ Erro de conexão: {e}")
            
        time.sleep(1)

except KeyboardInterrupt:
    print("\nParado.")
