import MetaTrader5 as mt5
import pandas as pd

# Conecta no MT5 que já está aberto
if not mt5.initialize():
    print("Erro ao conectar no MT5")
    quit()

# Tente pegar o WIN ou PETR4 (certifique-se que adicionou o PETR4 normal na lista)
symbol = "PETR4" 

# Tenta habilitar o ativo caso não esteja no Market Watch
selected = mt5.symbol_select(symbol, True)
if not selected:
    print(f"Não foi possível selecionar {symbol}, verifique o nome.")

# Pega 1000 velas de 5 minutos
rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 1000)

mt5.shutdown()

if rates is None:
    print("Nenhum dado recebido. Verifique se o mercado está aberto ou o ativo correto.")
else:
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    print(df.tail()) # Mostra os últimos dados