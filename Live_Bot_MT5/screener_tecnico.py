"""
Script de Filtro Quântico de Universo na B3 (Universe Screener) via MT5
Objetivo: Filtrar ~120 ativos da B3 mantendo apenas aqueles com boa liquidez, 
alta volatilidade percentual e forte tendência, usando dados diretos do MetaTrader 5.

REQUISITOS - Instale estas bibliotecas antes de rodar:
pip install MetaTrader5 pandas numpy tabulate
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
from tabulate import tabulate

# Lista inicial de ~120 ativos da B3 (TICKERS LIMPOS para MT5 BTG Pactual)
TICKERS = [
    'ABEV3', 'ALPA4', 'AMER3', 'ARZZ3', 'ASAI3', 'AZUL4', 'B3SA3', 'BBAS3', 
    'BBDC3', 'BBDC4', 'BBSE3', 'BEEF3', 'BPAC11', 'BRAP4', 'BRFS3', 'BRKM5', 
    'CASH3', 'CCRO3', 'CEAB3', 'CIEL3', 'CMIG4', 'COGN3', 'CPFE3', 'CPLE6', 
    'CRFB3', 'CSAN3', 'CSNA3', 'CVCB3', 'CYRE3', 'DIRR3', 'DXCO3', 'EGIE3', 
    'ELET3', 'ELET6', 'EMBR3', 'ENBR3', 'ENEV3', 'ENGI11', 'EQTL3', 'EZTC3', 
    'FLRY3', 'GGBR4', 'GOAU4', 'GOLL4', 'HAPV3', 'HYPE3', 'IGTI11', 'IRBR3', 
    'ITSA4', 'ITUB4', 'JBSS3', 'JHSF3', 'KLBN11', 'LIGT3', 'LREN3', 'LWSA3', 
    'MGLU3', 'MRFG3', 'MRVE3', 'MULT3', 'NTCO3', 'PCAR3', 'PETR3', 'PETR4', 
    'PETZ3', 'POMO4', 'PRIO3', 'QUAL3', 'RADL3', 'RAIL3', 'RAIZ4', 'RAPT4', 
    'RDOR3', 'RECV3', 'RENT3', 'RRRP3', 'SANB11', 'SBSP3', 'SLCE3', 'SMAL11', 
    'SMTO3', 'SOMA3', 'SUZB3', 'TAEE11', 'TASA4', 'TIMS3', 'TOTS3', 'UGPA3', 
    'USIM5', 'VALE3', 'VBBR3', 'VIIA3', 'VIVT3', 'VULC3', 'WEGE3', 'YDUQ3',
    'AERI3', 'AGRO3', 'ALOS3', 'AMBP3', 'ANIM3', 'ARML3', 'AURE3', 'BLAU3', 
    'BOVA11', 'BRSR6', 'CAML3', 'CBAV3', 'CLSA3', 'CMIN3', 'CURY3', 'DASA3', 
    'DEXP3', 'ECOR3', 'FESA4', 'GFSA3', 'GRND3', 'GUAR3', 'IFCM3', 'INTB3', 
    'KEPL3', 'LOGG3', 'MDIA3', 'MEAL3', 'MOVI3', 'NEOE3', 'ODPV3', 'ONCO3', 
    'PARD3', 'PORT3', 'POSI3', 'PTBL3', 'PSSA3', 'RANI3', 'RCSL3', 'ROMI3'
]

def format_currency(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_percentage(value):
    return f"{value * 100:.2f}%"

def wilder_smoothing(series, window):
    """Implementação do Wilder's Smoothing Method (WWMA) usado no ADX original"""
    ewm = series.ewm(alpha=1/window, min_periods=window, adjust=False).mean()
    return ewm

def calculate_atr_adx(df, window=14):
    """Calcula ATR e ADX usando as fórmulas clássicas do J. Welles Wilder"""
    # 1. True Range (TR)
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    
    # 2. ATR (Average True Range com Wilder's Smoothing)
    atr = wilder_smoothing(tr, window)
    
    # 3. Directional Movement (DM)
    up_move = df['high'] - df['high'].shift()
    down_move = df['low'].shift() - df['low']
    
    pos_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    neg_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    
    pos_dm = pd.Series(pos_dm, index=df.index)
    neg_dm = pd.Series(neg_dm, index=df.index)
    
    # 4. Smoothed Directional Movement (+DI e -DI)
    pos_di = 100 * (wilder_smoothing(pos_dm, window) / atr)
    neg_di = 100 * (wilder_smoothing(neg_dm, window) / atr)
    
    # 5. Directional Index (DX) e ADX
    dx = 100 * np.abs(pos_di - neg_di) / (pos_di + neg_di)
    adx = wilder_smoothing(dx, window)
    
    return atr, adx

def run_screener():
    print(f"Iniciando Universe Screener (via MT5) para {len(TICKERS)} ativos...")
    start_time = time.time()
    
    if not mt5.initialize():
        print(f"Erro Crítico ao inicializar o MT5: {mt5.last_error()}")
        return
        
    ativos_aprovados = []
    resultados_finais = []
    
    print("Baixando dados do MetaTrader 5 e processando filtros matemáticos...")
    
    for ticker in TICKERS:
        try:
            # Seleciona o símbolo no Market Watch do MT5
            if not mt5.symbol_select(ticker, True):
                continue
                
            # Baixa 90 candles diários
            rates = mt5.copy_rates_from_pos(ticker, mt5.TIMEFRAME_D1, 0, 90)
            
            if rates is None or len(rates) < 50:
                continue
                
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Padronizando colunas de volume de acordo com a API do MT5
            if 'real_volume' in df.columns:
                df['volume'] = df['real_volume']
            elif 'tick_volume' in df.columns:
                df['volume'] = df['tick_volume']
            else:
                continue
                
            current_close = df['close'].iloc[-1]
            if pd.isna(current_close) or current_close <= 0:
                continue

            # ---------------------------------------------------------
            # FILTRO 1: LIQUIDEZ (Volume Financeiro)
            # Volume Financeiro = Volume * Preço de Fechamento
            # ---------------------------------------------------------
            df['vol_financeiro'] = df['volume'] * df['close']
            df['vol_fin_med_20'] = df['vol_financeiro'].rolling(window=20).mean()
            current_liquidity = df['vol_fin_med_20'].iloc[-1]
            
            if pd.isna(current_liquidity) or current_liquidity < 5_000_000:
                continue

            # ---------------------------------------------------------
            # CÁLCULOS: ATR E ADX NATIVOS (Pandas Puro)
            # Para evitar dependência de bibliotecas defeituosas como pandas-ta,
            # usamos as fórmulas puras de J. Welles Wilder implementadas acima.
            # ---------------------------------------------------------
            atr_series, adx_series = calculate_atr_adx(df, window=14)
            df['atr_14'] = atr_series
            df['adx_14'] = adx_series
            
            # FILTRO 2: VOLATILIDADE RELATIVA (ATR %)
            current_atr = df['atr_14'].iloc[-1]
            if pd.isna(current_atr):
                continue
                
            atr_percent = current_atr / current_close
            if atr_percent <= 0.02: # Menor ou igual a 2% (Muito lateral)
                continue
                
            # FILTRO 3: FORÇA DA TENDÊNCIA (ADX 14)
            current_adx = df['adx_14'].iloc[-1]
            if pd.isna(current_adx) or current_adx <= 25:
                continue

            # =========================================================
            # ATIVO PASSOU EM TODOS OS FILTROS!
            # =========================================================
            ativos_aprovados.append(ticker)
            
            resultados_finais.append({
                "Ticker": ticker,
                "Preço": current_close,
                "Vol. Financeiro (Média 20d)": current_liquidity,
                "Volatilidade (ATR %)": atr_percent,
                "Tendência (ADX 14)": current_adx
            })

        except Exception as e:
            # Erros silenciosos
            pass
            
    # Logout e Cleanup MT5
    mt5.shutdown()
            
    # --- OUTPUT ---
    print("\n")
    if not resultados_finais:
        print("Triste dia... Nenhum ativo sobreviveu à peneira dos deuses quânticos hoje.")
    else:
        # Ordenando a tabela pelo maior ADX (Ativos em tendência mais forte primeiro)
        resultados_finais.sort(key=lambda x: x["Tendência (ADX 14)"], reverse=True)
        
        # Formatando valores para a tabela bonita
        for r in resultados_finais:
            r["Preço"] = f"R$ {r['Preço']:.2f}"
            r["Vol. Financeiro (Média 20d)"] = format_currency(r["Vol. Financeiro (Média 20d)"])
            r["Volatilidade (ATR %)"] = format_percentage(r["Volatilidade (ATR %)"])
            r["Tendência (ADX 14)"] = f"{r['Tendência (ADX 14)']:.2f}"
            
        print("✅ FILTRO CONCLUÍDO! Ativos que sobreviveram às métricas de Liquidez, Volatilidade e Tendência:\n")
        
        print(tabulate(
            resultados_finais, 
            headers="keys", 
            tablefmt="grid", 
            colalign=("left", "right", "right", "right", "right")
        ))
        
        print("\n" + "="*80)
        print("🔥 ARRAY FINAL PARA O SEU ROBÔ (COPY/PASTE): 🔥")
        print("="*80)
        
        print(f"ATIVOS_FILTRADOS = {ativos_aprovados}")

    elapsed = time.time() - start_time
    print(f"\nTempo total de execução: {elapsed:.2f} segundos.")


if __name__ == "__main__":
    run_screener()
