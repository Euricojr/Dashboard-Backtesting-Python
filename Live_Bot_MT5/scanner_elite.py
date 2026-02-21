import yfinance as yf
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

# Extraímos a lista do seu filtered_assets_debug.csv adicionando o '.SA' para o yfinance.
ALL_ASSETS = [
    "ABEV3.SA", "AESB3.SA", "ALOS3.SA", "ALUP11.SA", "ARZZ3.SA", "ASAI3.SA", "AURE3.SA", 
    "AZUL4.SA", "B3SA3.SA", "BBAS3.SA", "BBDC3.SA", "BBDC4.SA", "BBSE3.SA", "BEEF3.SA", 
    "BHIA3.SA", "BOVA11.SA", "BPAC11.SA", "BRAP4.SA", "BRAV3.SA", "BRFS3.SA", "BRKM5.SA", 
    "CAML3.SA", "CASH3.SA", "CCRO3.SA", "CIEL3.SA", "CMIG4.SA", "CMIN3.SA", "COGN3.SA", 
    "CPFE3.SA", "CPLE6.SA", "CRFB3.SA", "CSAN3.SA", "CSNA3.SA", "CURY3.SA", "CVCB3.SA", 
    "CXSE3.SA", "CYRE3.SA", "DIRR3.SA", "DXCO3.SA", "ECOR3.SA", "EGIE3.SA", "ELET3.SA", 
    "ELET6.SA", "EMBR3.SA", "ENAT3.SA", "ENEV3.SA", "ENGI11.SA", "EQTL3.SA", "EZTC3.SA", 
    "FLRY3.SA", "GGBR4.SA", "GGPS3.SA", "GOAU4.SA", "GOLL4.SA", "HAPV3.SA", "HYPE3.SA", 
    "IGTI11.SA", "INTB3.SA", "IRBR3.SA", "ITSA4.SA", "ITUB4.SA", "IVVB11.SA", "JBSS3.SA", 
    "JHSF3.SA", "KEPL3.SA", "KLBN11.SA", "LREN3.SA", "LWSA3.SA", "MATD3.SA", "MGLU3.SA", 
    "MILS3.SA", "MOVI3.SA", "MRFG3.SA", "MRVE3.SA", "MULT3.SA", "MYPK3.SA", "NEOE3.SA", 
    "NTCO3.SA", "PCAR3.SA", "PETR3.SA", "PETR4.SA", "PETZ3.SA", "POSI3.SA", "PRIO3.SA", 
    "PSSA3.SA", "RADL3.SA", "RAIL3.SA", "RAIZ4.SA", "RANI3.SA", "RDOR3.SA", "RECV3.SA", 
    "RENT3.SA", "ROMI3.SA", "RRRP3.SA", "SANB11.SA", "SAPR11.SA", "SAPR4.SA", "SBSP3.SA", 
    "SLCE3.SA", "SMAL11.SA", "SMTO3.SA", "SOMA3.SA", "STBP3.SA", "SUZB3.SA", "TAEE11.SA", 
    "TIMS3.SA", "TOTS3.SA", "TRPL4.SA", "UGPA3.SA", "UNIP6.SA", "USIM5.SA", "VALE3.SA", 
    "VAMO3.SA", "VBBR3.SA", "VIVA3.SA", "VIVT3.SA", "WEGE3.SA", "YDUQ3.SA"
]

def run_backtest(ticker, data):
    # Calcular as Médias Móveis (Trend Following)
    data['SMA20'] = data['Close'].rolling(window=20).mean()
    data['SMA50'] = data['Close'].rolling(window=50).mean()
    
    # Remover NaNs (os primeiros 50 candles onde a SMA50 não existe)
    data = data.dropna(subset=['SMA20', 'SMA50']).copy()
    
    in_position = False
    buy_price = 0.0
    trades = []
    
    for i in range(1, len(data)):
        prev_sma20 = data['SMA20'].iloc[i-1]
        prev_sma50 = data['SMA50'].iloc[i-1]
        curr_sma20 = data['SMA20'].iloc[i]
        curr_sma50 = data['SMA50'].iloc[i]
        curr_close = data['Close'].iloc[i]
        
        # Cruzamento para cima (SMA20 cruza SMA50 de baixo para cima) -> Comprar
        if not in_position and prev_sma20 <= prev_sma50 and curr_sma20 > curr_sma50:
            in_position = True
            buy_price = curr_close
            
        # Cruzamento para baixo (SMA20 cruza SMA50 de cima para baixo) -> Vender
        elif in_position and prev_sma20 >= prev_sma50 and curr_sma20 < curr_sma50:
            in_position = False
            sell_price = curr_close
            profit_pct = (sell_price - buy_price) / buy_price
            trades.append(profit_pct)
            
    # Caso um trade fique aberto no final da série, podemos "fechá-lo" no último preço para avaliar o resultado atual
    if in_position:
        sell_price = data['Close'].iloc[-1]
        profit_pct = (sell_price - buy_price) / buy_price
        trades.append(profit_pct)

    return trades

def analyze_trades(trades):
    if not trades:
        return 0.0, 0, 0.0, 0.0
    
    total_trades = len(trades)
    winning_trades = [t for t in trades if t > 0]
    losing_trades = [t for t in trades if t <= 0]
    
    win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0.0
    
    sum_profits = sum(winning_trades)
    # Valor absoluto das perdas para o divisor ser positivo
    sum_losses = abs(sum(losing_trades))
    net_profit = sum(trades)
    
    # Tratando casos onde não houve nenhuma perda
    if sum_losses == 0:
        profit_factor = float('inf') if sum_profits > 0 else 0.0
    else:
        profit_factor = sum_profits / sum_losses
        
    return profit_factor, total_trades, win_rate, net_profit

def main():
    # Período: 12 meses
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    print("=========================================")
    print("        SCANNER ELITE (YFINANCE)         ")
    print("=========================================")
    print(f"Estratégia: Cruzamento de Médias (20/50)")
    print(f"Timeframe: 1h")
    print(f"Período: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
    print(f"Total de ativos: {len(ALL_ASSETS)}")
    print("=========================================\n")
    
    approved_assets = []
    results = []
    
    for ticker in ALL_ASSETS:
        print(f"Analisando {ticker:10s} ... ", end="", flush=True)
        try:
            # Baixando o histórico do yfinance no timeframe de 1h
            data = yf.Ticker(ticker).history(start=start_date, end=end_date, interval='1h')
            
            if data.empty or len(data) < 50:
                print("DADOS INSUFICIENTES")
                results.append({
                    'Ticker': ticker, 'Status': 'ERRO/SEM DADOS', 'Profit Factor': 0,
                    'Total Trades': 0, 'Win Rate (%)': 0, 'Net Profit (%)': 0
                })
                continue
            
            trades = run_backtest(ticker, data)
            pf, total_trades, win_rate, net_profit = analyze_trades(trades)
            
            # A PENEIRA MATEMÁTICA: PF > 1.20 e Trades > 5
            if pf > 1.20 and total_trades > 5:
                status = "APROVADO"
                print(f"[APROVADO]  | PF: {pf:5.2f} | Trades: {total_trades:2d} | Win Rate: {win_rate:5.1%} | Net: {net_profit:6.1%}")
                approved_assets.append(ticker)
            else:
                status = "REPROVADO"
                if pf == float('inf'):
                    print(f"[REPROVADO] | PF:  INF  | Trades: {total_trades:2d} | Win Rate: {win_rate:5.1%} | Net: {net_profit:6.1%}")
                else:
                    print(f"[REPROVADO] | PF: {pf:5.2f} | Trades: {total_trades:2d} | Win Rate: {win_rate:5.1%} | Net: {net_profit:6.1%}")
            
            results.append({
                'Ticker': ticker,
                'Status': status,
                'Profit Factor': round(pf, 2) if pf != float('inf') else 'INF',
                'Total Trades': total_trades,
                'Win Rate (%)': round(win_rate * 100, 2),
                'Net Profit (%)': round(net_profit * 100, 2)
            })
                
        except Exception as e:
            print(f"ERRO ({e})")
            results.append({
                'Ticker': ticker, 'Status': f'ERRO ({e})', 'Profit Factor': 0,
                'Total Trades': 0, 'Win Rate (%)': 0, 'Net Profit (%)': 0
            })
            
    print("\n=========================================")
    print("             RESUMO FINAL                ")
    print("=========================================")
    print(f"Aprovados:  {len(approved_assets)} / {len(ALL_ASSETS)}")
    # Pegar o diretório raiz de onde o script está (Live_Bot_MT5)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data')
    
    # Criar a pasta data para o CSV dentro da raiz do script
    os.makedirs(data_dir, exist_ok=True)
    
    # Salvar resultados completos em CSV
    df_results = pd.DataFrame(results)
    
    # Ordenar pelos mais rentáveis (Net Profit)
    df_results = df_results.sort_values(by='Net Profit (%)', ascending=False)
    
    csv_file = os.path.join(data_dir, 'backtest_results.csv')
    df_results.to_csv(csv_file, index=False, sep=';', decimal=',')
    print(f"\n[+] Resultados completos salvos em CSV para analise: {csv_file}")

if __name__ == '__main__':
    main()
