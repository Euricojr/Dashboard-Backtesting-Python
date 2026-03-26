import pandas as pd
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Importa a engine de backtest recém restaurada
from backtester import backtest_scalper_engine

load_dotenv()

SYMBOL = "WINJ26" # Atualize conforme contrato vigente

def load_data(symbol, timeframe, days=30):
    mt5_tf = mt5.TIMEFRAME_M5 if timeframe == "M5" else mt5.TIMEFRAME_M1
    
    fim = datetime.now()
    inicio = fim - timedelta(days=days)
    
    print(f"Buscando dados de {symbol} ({timeframe}) de {inicio.strftime('%d/%m')} até {fim.strftime('%d/%m')}...")
    rates = mt5.copy_rates_range(symbol, mt5_tf, inicio, fim)
    
    if rates is None or len(rates) == 0:
        print(f"Erro ao buscar dados do MT5. Loop ignorado. Erro: {mt5.last_error()}")
        return None
        
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Preparação Mandatória de features para a Engine
    df['date'] = df['time'].dt.date
    df['time_only'] = df['time'].dt.time
    
    df['EMA9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['SMA21'] = df['close'].rolling(window=21).mean()
    
    # Cálculo do VWAP diário
    df['Typical_Price'] = (df['high'] + df['low'] + df['close']) / 3
    df['Vol_x_TP'] = df['tick_volume'] * df['Typical_Price']
    df['Cum_Vol_x_TP'] = df.groupby('date')['Vol_x_TP'].cumsum()
    df['Cum_Vol'] = df.groupby('date')['tick_volume'].cumsum()
    df['VWAP'] = df['Cum_Vol_x_TP'] / df['Cum_Vol']
    
    return df

def run_grid_search(timeframe="M5", sl_manual=150.0, tp_manual=300.0):
    df = load_data(SYMBOL, timeframe, days=30)
    if df is None:
        return
        
    # Grid Search Inputs informados pelo usuário
    start_times = ["09:05", "09:15", "09:30", "10:00", "10:30"]
    end_times = ["11:30", "12:00", "12:30", "13:00", "15:00", "16:00", "17:00"]
    
    resultados = []
    
    print(f"\n⚙️ Iniciando Otimização Grid Search para {SYMBOL} ({timeframe})...")
    
    total_combinacoes = 0
    for st in start_times:
        for et in end_times:
            if datetime.strptime(st, "%H:%M") < datetime.strptime(et, "%H:%M"):
                total_combinacoes += 1
                
    print(f"Total de Janelas Válidas a Testar: {total_combinacoes}")
    
    for st in start_times:
        for et in end_times:
            # Pula combinações inválidas (ex: start_time >= end_time)
            if datetime.strptime(st, "%H:%M") >= datetime.strptime(et, "%H:%M"):
                continue
                
            # Cópia leve para limpar trade_signals residuais a cada loop iterativo
            df_teste = df.copy()
            
            res = backtest_scalper_engine(
                df=df_teste,
                sl_manual=sl_manual,
                tp_manual=tp_manual,
                start_time=st,
                end_time=et
            )
            
            # Filtro Estatístico exigido: Acima de 10 trades reais
            if res["total_trades"] >= 10:
                resultados.append(res)
                
    if not resultados:
        print(f"⚠️ Nenhuma janela de tempo gerou pelo menos 10 trades para o {timeframe}.")
        return
        
    df_res = pd.DataFrame(resultados)
    
    # Ordenação (Score final): 1º Mais Lucrativo, 2º Menor Drawdown
    # Max Drawdown vem sempre positivo, então ordenar ascending=True pro Drawdown quer dizer 'o menor estrago sobrado'
    df_res = df_res.sort_values(by=["lucro_total_rs", "max_drawdown_rs"], ascending=[False, True])
    
    print(f"\n🏆 TOP 5 JANELAS DE OPERAÇÃO - TIMEFRAME: {timeframe} 🏆")
    print("-" * 75)
    print(f"{'Janela Horário':<15} | {'Lucro (R$)':<12} | {'Trades':<8} | {'WinRate (%)':<12} | {'Max Drawdown (R$)'}")
    print("-" * 75)
    
    top5 = df_res.head(5)
    for _, row in top5.iterrows():
        janela = f"{row['start_time']} - {row['end_time']}"
        lucro = f"R$ {row['lucro_total_rs']:.2f}"
        trades = int(row['total_trades'])
        winrate = f"{row['winrate']:.1f}%"
        dd = f"R$ {row['max_drawdown_rs']:.2f}"
        
        print(f"{janela:<15} | {lucro:<12} | {trades:<8} | {winrate:<12} | {dd}")
    print("-" * 75 + "\n")

if __name__ == "__main__":
    print("Iniciando Módulo de Otimização e Conectando com a XP Simulador...")
    
    login_xp = os.getenv("XP_DEMO_LOGIN")
    password_xp = os.getenv("XP_DEMO_PASSWORD")
    
    # Inicialização crua pra standalone mode
    if login_xp:
        success = mt5.initialize(login=int(login_xp), password=password_xp, server="XPMT5-DEMO")
    else:
        success = mt5.initialize()
        
    if not success:
        print(f"Falha ao inicializar MT5. Erro: {mt5.last_error()}")
    else:
        print("\n--- CONFIGURAÇÃO DO OTIMIZADOR ---")
        try:
            sl_input = input("Digite o STOP LOSS em pontos (Pressione Enter para 150): ").strip()
            sl_val = float(sl_input) if sl_input else 150.0
            
            tp_input = input("Digite o TAKE PROFIT em pontos (Pressione Enter para 300): ").strip()
            tp_val = float(tp_input) if tp_input else 300.0
        except ValueError:
            print("Valor inválido! Usando padrão SL=150 e TP=300.")
            sl_val = 150.0
            tp_val = 300.0

        # Roda Otimização pro Gráfico M5
        run_grid_search("M5", sl_manual=sl_val, tp_manual=tp_val)
        
        # Roda Otimização pro Gráfico M1
        run_grid_search("M1", sl_manual=sl_val, tp_manual=tp_val)
        
        mt5.shutdown()
