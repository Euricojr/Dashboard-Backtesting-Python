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
        if hist.empty or 'Dividends' not in hist.columns: return []
        divs = hist[hist['Dividends'] > 0]['Dividends']
        if divs.empty: return []
        df_divs = divs.groupby(divs.index.year).sum().reset_index()
        df_divs.columns = ['ano', 'total_pago']
        return df_divs.to_dict('records')
    except Exception as e:
        print(f"Erro ao obter dividendos: {e}")
        return []

def processar_ativo(ticker):
    """
    Busca dados fundamentalistas usando yfinance com reconciliação Status Invest.
    """
    ticker = ticker.upper().strip()
    symbols_to_try = [f"{ticker}.SA", ticker] if not ticker.endswith('.SA') else [ticker, ticker.replace('.SA', '')]
    
    info = {}
    stock = None
    symbol = ""
    for s in symbols_to_try:
        try:
            stock = yf.Ticker(s)
            temp_info = stock.info
            if temp_info and len(temp_info) > 10:
                info = temp_info
                symbol = s
                break
        except: continue

    if not info:
        symbol = symbols_to_try[0]
        stock = yf.Ticker(symbol)
        info = {}

    def get_val(key, default=0):
        val = info.get(key)
        return val if val is not None else default

    # Preço Atual
    price = get_val('currentPrice', get_val('regularMarketPrice', 0))
    if price == 0:
        try:
            price = stock.fast_info.last_price
            if price == 0:
                h1d = stock.history(period="1d")
                if not h1d.empty: price = h1d['Close'].iloc[-1]
        except: price = 0

    if price == 0: return None

    # Variação do Dia
    var_dia = get_val('regularMarketChangePercent', 0)
    if var_dia == 0:
        try:
            pc = stock.fast_info.previous_close
            var_dia = ((price / pc) - 1) * 100 if pc and pc > 0 else 0
        except: pass
    if -1 < var_dia < 1 and var_dia != 0 and abs(var_dia) < 0.001: # Converte se estiver em decimal puro
        var_dia *= 100

    # BLOCO DE MERCADO (Status Invest Alignment)
    try:
        # Usamos auto_adjust=True para Rentabilidade Real (Total Return)
        h = stock.history(period="1y", auto_adjust=True)
        # Limpeza radical contra lixo
        h = h[(h['Low'] > 0.1) & (h['Close'] > 0.1)].dropna()
    except:
        h = pd.DataFrame()

    min_52sem, max_52sem = price, price
    val_12m, val_mes = 0, 0
    min_mes, max_mes = price, price

    if not h.empty and len(h) > 5:
        # Mínimas e Máximas
        min_52sem = h['Low'].min()
        max_52sem = h['High'].max()
        
        # 12 Meses
        p_ini_1y = h['Close'].iloc[0]
        val_12m = ((price / p_ini_1y) - 1) * 100
        
        # Mês Atual
        try:
            now = datetime.now()
            mask = (h.index.month == now.month) & (h.index.year == now.year)
            h_m = h[mask]
            if not h_m.empty:
                idx0 = h_m.index[0]
                try:
                    pos = h.index.get_loc(idx0)
                    p_base = h['Close'].iloc[pos-1] if pos > 0 else h_m['Open'].iloc[0]
                except: p_base = h_m['Open'].iloc[0]
                val_mes = ((price / p_base) - 1) * 100
                min_mes, max_mes = h_m['Low'].min(), h_m['High'].max()
        except: pass

    # Valuation e Eficiência
    lpa = get_val('trailingEps', 0)
    pl = (price / lpa) if lpa != 0 else get_val('trailingPE', 0)
    vpa = get_val('bookValue', 0)
    pvp = (price / vpa) if vpa != 0 else get_val('priceToBook', 0)
    
    # Dividend Yield
    total_divs = h['Dividends'].sum() if (not h.empty and 'Dividends' in h.columns) else 0
    dy = (total_divs / price * 100) if price > 0 else (get_val('dividendYield', 0) * 100)

    # Eficiência e Endividamento
    shares = get_val('sharesOutstanding', 0)
    lucro = get_val('netIncomeToCommon', get_val('netIncome', 0))
    roe = (lucro / (vpa * shares) * 100) if (shares > 0 and vpa > 0) else get_val('returnOnEquity', 0) * 100
    total_debt = get_val('totalDebt', 0)
    total_cash = get_val('totalCash', 0)
    ebitda = get_val('ebitda', 0)
    div_ebitda = ((total_debt - total_cash) / ebitda) if ebitda != 0 else 0

    return {
        'meta': {
            'ticker': ticker, 'empresa': info.get('longName', ticker), 'ano_base': 'TTM',
            'url_relatorio': f"https://finance.yahoo.com/quote/{symbol}",
            'setor': info.get('sector', 'N/A'), 'industria': info.get('industry', 'N/A'),
            'descricao': info.get('longBusinessSummary', ''), 'website': info.get('website', 'N/A'),
            'erro_api': not bool(info)
        },
        'price': price,
        'mercado': {
            'preco_atual': price, 'variacao_dia': round(var_dia, 2),
            'max_52sem': round(max_52sem, 2), 'min_52sem': round(min_52sem, 2),
            'max_mes': round(max_mes, 2), 'min_mes': round(min_mes, 2),
            'valorizacao_12m': round(val_12m, 2), 'valorizacao_mes': round(val_mes, 2)
        },
        'valuation': {
            'P/L': round(pl, 2), 'P/VP': round(pvp, 2), 'EV_Ebitda': round(get_val('enterpriseToEbitda', 0), 2),
            'Div_Yield': round(dy, 2), 'LPA': round(lpa, 2), 'VPA': round(vpa, 2),
            'peg_ratio': round(get_val('pegRatio', 0), 2), 'beta': round(get_val('beta', 0), 2),
            'max_52sem': round(max_52sem, 2), 'min_52sem': round(min_52sem, 2)
        },
        'eficiencia': {
            'Margem_Bruta': round(get_val('grossMargins', 0) * 100, 2),
            'Margem_Liquida': round(get_val('profitMargins', 0) * 100, 2),
            'ROE': round(roe, 2), 'ROIC': 0
        },
        'endividamento': {
            'DivLiq_Ebitda': round(div_ebitda, 2), 'Liq_Corrente': round(get_val('currentRatio', 0), 2),
            'Div_Bruta': total_debt
        },
        'proventos': obter_historico_dividendos(symbol),
        'raw': {
            'receita_liquida': get_val('totalRevenue', 0), 'ebitda': ebitda,
            'lucro_liquido': lucro, 'patrimonio_liquido': vpa * shares if shares > 0 else 0,
            'divida_bruta': total_debt, 'disponibilidades': total_cash
        }
    }

if __name__ == "__main__":
    import json
    d = processar_ativo("PETR4")
    if d: print(json.dumps(d, indent=4, ensure_ascii=False))
