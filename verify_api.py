import requests
import json
import sys

# URL da API
url = "http://localhost:5000/run_backtest"

# Payload de teste
payload = {
    "ticker": "PETR4.SA",
    "start": "2020-01-01",
    "end": "2024-01-01",
    "sma_short": 20,
    "sma_long": 50,
    "strategy": "SMA"
}

try:
    print(f"Enviando requisição para {url}...")
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ Resposta recebida com sucesso!")
        
        # Verificando chaves principais
        required_keys = ["metrics_in", "metrics_out", "candle_data", "equity_data", "split_date"]
        missing_keys = [key for key in required_keys if key not in data]
        
        if missing_keys:
            print(f"❌ Chaves faltando no JSON: {missing_keys}")
            sys.exit(1)
        else:
            print("✅ Estrutura JSON principal correta.")
            
        # Verificando métricas (exemplo)
        print("\nMétricas In-Sample:")
        print(json.dumps(data["metrics_in"], indent=2))
        
        print("\nMétricas Out-of-Sample:")
        print(json.dumps(data["metrics_out"], indent=2))
        
        # Verificando snake_case
        if "total_return" in data["metrics_in"]:
            print("✅ Keys estão em snake_case (total_return encontrado).")
        else:
            print("❌ Keys NÃO estão em snake_case.")
            
    else:
        print(f"❌ Erro na requisição: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"❌ Erro ao conectar: {e}")
