import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

def obter_historico_dividendos(ticker_sa):
    """
    Baixa o histórico de 5 anos e agrupa dividendos por ano.
    """
    try:
        stock = yf.Ticker(ticker_sa)
        hist = stock.history(period="5y")
        
        if hist.empty or 'Dividends' not in hist.columns:
            return []
            
        # Filtra apenas dias com dividendos > 0
        divs = hist[hist['Dividends'] > 0]['Dividends']
        
        if divs.empty:
            return []
            
        # Agrupa por ano e soma
        df_divs = divs.groupby(divs.index.year).sum().reset_index()
        df_divs.columns = ['ano', 'total_pago']
        
        # Converte para lista de dicts
        return df_divs.to_dict('records')
    except Exception as e:
        print(f"Erro ao obter dividendos para {ticker_sa}: {e}")
        return []

def processar_ativo(ticker):
    """
    Busca dados fundamentalistas usando yfinance (Yahoo Finance)
    e retorna no formato esperado pelo Frontend do FinSense.
    """
    # 1. Normalização de Ticker Robusta
    ticker = ticker.upper().strip()
    symbols_to_try = [f"{ticker}.SA", ticker] if not ticker.endswith('.SA') else [ticker, ticker.replace('.SA', '')]
    
    info = {}
    stock = None
    symbol = ""
    erro_api = False

    # 2. Mecanismo de Tentativa (Retry)
    for s in symbols_to_try:
        try:
            print(f"--- Tentando Yahoo Finance para: {s} ---")
            stock = yf.Ticker(s)
            # Acessar uma propriedade leve para validar se o ticker existe no Yahoo
            temp_info = stock.info
            if temp_info and len(temp_info) > 10:
                info = temp_info
                symbol = s
                break
        except Exception as e:
            print(f"Falha ao tentar {s}: {e}")
            continue

    # 3. Fallback: Se não encontrou 'info' robusto, tentamos pelo menos o preço
    if not info:
        print(f"Aviso: .info vazio para {ticker}. Tentando extração mínima de emergência.")
        erro_api = True
        symbol = symbols_to_try[0] # Assume .SA como padrão para BR
        stock = yf.Ticker(symbol)
        info = {} # Garante que info seja um dict

    # Helper para pegar valor seguro (0 se None)
    def get_val(key, default=0):
        val = info.get(key)
        return val if val is not None else default

    # Fallback de Preço Prioritário
    price = get_val('currentPrice', get_val('regularMarketPrice', 0))
    if price == 0:
        try:
            # Tenta via fast_info (mais rápido)
            price = stock.fast_info.last_price
            if not price:
                # Tenta via history (último recurso)
                hist_now = stock.history(period="1d")
                if not hist_now.empty:
                    price = hist_now['Close'].iloc[-1]
        except:
            price = 0

    # Variação do Dia
    var_dia = get_val('regularMarketChangePercent', 0)
    # Se for decimal (0.02), converte para (2.0)
    if -1 < var_dia < 1 and var_dia != 0:
        var_dia *= 100
        
    if var_dia == 0 and price > 0:
        try:
            prev_close = stock.fast_info.previous_close
            if prev_close and prev_close > 0:
                var_dia = ((price - prev_close) / prev_close) * 100
        except: pass

    # Se ainda assim o preço for 0, o ativo realmente não está disponível
    if price == 0:
        print(f"Dados insuficientes (Preço=0) para {ticker}. Abortando.")
        return None

    try:
        # 3. Mapeamento de Dados
        
        # --- Preço e Meta ---
        company_name = info.get('longName', ticker)
        
        # Novos campos em Meta
        setor = info.get('sector', 'N/A')
        industria = info.get('industry', 'N/A')
        descricao = info.get('longBusinessSummary', '')
        website = info.get('website', 'N/A')
        
        # --- Valuation ---
        # 1. P/L (Preço / Lucro por Ação)
        lpa = get_val('trailingEps', 0)
        if lpa != 0:
            pl = price / lpa
        else:
            pl = get_val('trailingPE', 0)
            
        # 2. P/VP
        vpa = get_val('bookValue', 0)
        if vpa != 0:
            pvp = price / vpa
        else:
            pvp = get_val('priceToBook', 0)
            
        # 3. Dividend Yield (TTM Manual)
        try:
            hist_1y = stock.history(period="1y")
            if not hist_1y.empty and 'Dividends' in hist_1y.columns:
                total_divs_1y = hist_1y['Dividends'].sum()
                if price > 0:
                    div_yield = (total_divs_1y / price) * 100
                else:
                    div_yield = 0
            else:
                div_yield = get_val('dividendYield', 0)
                div_yield = div_yield * 100 if div_yield < 1 and div_yield > 0 else div_yield
        except:
            div_yield = 0

        if div_yield > 100: div_yield = 0
            
        # 4. EV/EBITDA
        ev_ebitda = get_val('enterpriseToEbitda', 0)
        
        peg_ratio = get_val('pegRatio', 0)
        beta = get_val('beta', 0)
        max_52sem = get_val('fiftyTwoWeekHigh', 0)
        min_52sem = get_val('fiftyTwoWeekLow', 0)

        # --- Eficiência ---
        margem_bruta = get_val('grossMargins', 0) * 100
        margem_liquida = get_val('profitMargins', 0) * 100
        
        shares = get_val('sharesOutstanding', 0)
        vpa_val = get_val('bookValue', 0)
        lucro_l = get_val('netIncomeToCommon', get_val('netIncome', 0))
        
        if shares > 0 and vpa_val > 0 and lucro_l != 0:
            patrimonio_estimado = vpa_val * shares
            roe = (lucro_l / patrimonio_estimado) * 100
        else:
            roe = get_val('returnOnEquity', 0) * 100
            
        roic = 0 

        total_debt = get_val('totalDebt', 0)
        total_cash = get_val('totalCash', 0)
        ebitda = get_val('ebitda', 0)
        
        net_debt = total_debt - total_cash
        if ebitda != 0:
            div_liq_ebitda = net_debt / ebitda
        else:
            div_liq_ebitda = 0
            
        liq_corrente = get_val('currentRatio', 0)

        proventos_hist = obter_historico_dividendos(symbol)

        val_12m = 0
        val_mes = 0
        try:
            if 'hist_1y' not in locals():
                hist_1y = stock.history(period="1y", auto_adjust=False)
            
            if not hist_1y.empty:
                ref_price = price if price > 0 else hist_1y['Close'].iloc[-1]
                preco_ini_12m = hist_1y['Close'].iloc[0]
                if preco_ini_12m > 0:
                    val_12m = ((ref_price - preco_ini_12m) / preco_ini_12m) * 100
                
                now = datetime.now()
                hist_mes = hist_1y[
                    (hist_1y.index.month == now.month) & 
                    (hist_1y.index.year == now.year)
                ]
                
                if not hist_mes.empty:
                    preco_ini_mes = hist_mes['Open'].iloc[0]
                    val_mes = ((ref_price - preco_ini_mes) / preco_ini_mes) * 100
                    min_mes = hist_mes['Low'].min()
                    max_mes = hist_mes['High'].max()
                else:
                    min_mes = ref_price
                    max_mes = ref_price

                min_52sem = hist_1y['Low'].min()
                max_52sem = hist_1y['High'].max()
        except Exception as e:
            print(f"Erro ao calcular valorização para {symbol}: {e}")

        receita_liquida = get_val('totalRevenue', 0)
        lucro_liquido = get_val('netIncomeToCommon', get_val('netIncome', 0))
        
        if shares > 0 and vpa_val > 0:
            patrimonio_liquido = vpa_val * shares
        else:
            patrimonio_liquido = 0

        # Montagem do JSON Final
        result = {
            'meta': {
                'ticker': ticker,
                'empresa': company_name,
                'ano_base': 'TTM (Yahoo)',
                'url_relatorio': f"https://finance.yahoo.com/quote/{symbol}",
                'setor': setor,
                'industria': industria,
                'descricao': descricao,
                'website': website,
                'erro_api': erro_api
            },
            'price': price,
            'mercado': {
                'preco_atual': price,
                'variacao_dia': round(var_dia, 2),
                'max_52sem': round(max_52sem, 2),
                'min_52sem': round(min_52sem, 2),
                'max_mes': round(max_mes if 'max_mes' in locals() else price, 2),
                'min_mes': round(min_mes if 'min_mes' in locals() else price, 2),
                'valorizacao_12m': round(val_12m, 2),
                'valorizacao_mes': round(val_mes, 2)
            },
            'valuation': {
                'P/L': round(pl, 2),
                'P/VP': round(pvp, 2),
                'EV_Ebitda': round(ev_ebitda, 2),
                'Div_Yield': round(div_yield, 2),
                'LPA': round(lpa, 2),
                'VPA': round(vpa, 2),
                'peg_ratio': round(peg_ratio, 2),
                'beta': round(beta, 2),
                'max_52sem': round(max_52sem, 2),
                'min_52sem': round(min_52sem, 2)
            },
            'eficiencia': {
                'Margem_Bruta': round(margem_bruta, 2),
                'Margem_Liquida': round(margem_liquida, 2),
                'ROE': round(roe, 2),
                'ROIC': round(roic, 2)
            },
            'endividamento': {
                'DivLiq_Ebitda': round(div_liq_ebitda, 2),
                'Liq_Corrente': round(liq_corrente, 2),
                'Div_Bruta': total_debt
            },
            'proventos': proventos_hist,
            'raw': {
                'receita_liquida': receita_liquida,
                'ebitda': ebitda,
                'lucro_liquido': lucro_liquido,
                'patrimonio_liquido': patrimonio_liquido,
                'divida_bruta': total_debt,
                'disponibilidades': total_cash
            }
        }
        
        print("✅ Dados processados com sucesso via Yahoo Finance!")
        return result

    except Exception as e:
        print(f"❌ Erro ao processar via Yahoo: {e}")
        return None

if __name__ == "__main__":
    import json
    t = "WEGE3"
    data = processar_ativo(t)
    if data:
        print(json.dumps(data, indent=4, ensure_ascii=False))
