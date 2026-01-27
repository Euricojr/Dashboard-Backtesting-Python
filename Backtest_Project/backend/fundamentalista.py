import yfinance as yf
import pandas as pd
import numpy as np

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
    # 1. Ajuste do Ticker (.SA)
    ticker = ticker.upper().strip()
    if not ticker.endswith('.SA'):
        symbol = f"{ticker}.SA"
    else:
        symbol = ticker
        
    print(f"--- Buscando dados no Yahoo Finance para: {symbol} ---")
    
    try:
        # 2. Busca objeto Ticker
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # Helper para pegar valor seguro (0 se None)
        def get_val(key, default=0):
            val = info.get(key)
            return val if val is not None else default

        # Fallback de Preço: Yahoo às vezes falha no info['regularMarketPrice']
        price = get_val('currentPrice', get_val('regularMarketPrice', 0))
        if price == 0:
            try:
                # 1. Tenta via fast_info (mais rápido)
                price = stock.fast_info.last_price
                if price is None or price == 0:
                    # 2. Tenta via history (mais pesado mas garantido)
                    hist_now = stock.history(period="1d")
                    if not hist_now.empty:
                        price = hist_now['Close'].iloc[-1]
            except:
                price = 0

        # Verifica se pelo menos o preço foi encontrado
        if price == 0 and (not info or len(info) < 5):
            print(f"Dados insuficientes para {symbol}. Abortando.")
            return None

        # 3. Mapeamento de Dados
        
        # --- Preço e Meta ---
        company_name = info.get('longName', ticker)
        
        # Novos campos em Meta
        setor = info.get('sector', 'N/A')
        industria = info.get('industry', 'N/A')
        descricao = info.get('longBusinessSummary', '')
        if len(descricao) > 500:
            descricao = descricao[:497] + "..."
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
        # Yahoo 'dividendYield' no Brasil é muito instável (mistura decimal com %).
        # Calculamos via histórico de 1 ano para ser preciso (TTM).
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

        # Trava de segurança para evitar erros de split/grupamento mal processados
        if div_yield > 100: div_yield = 0
            
        # 4. EV/EBITDA
        ev_ebitda = get_val('enterpriseToEbitda', 0)
        
        # Novos campos em Valuation
        peg_ratio = get_val('pegRatio', 0)
        beta = get_val('beta', 0)
        max_52sem = get_val('fiftyTwoWeekHigh', 0)
        min_52sem = get_val('fiftyTwoWeekLow', 0)

        # --- Eficiência ---
        margem_bruta = get_val('grossMargins', 0) * 100
        margem_liquida = get_val('profitMargins', 0) * 100
        
        # ROE Calculado
        shares = get_val('sharesOutstanding', 0)
        vpa_val = get_val('bookValue', 0)
        lucro_l = get_val('netIncomeToCommon', get_val('netIncome', 0))
        
        if shares > 0 and vpa_val > 0 and lucro_l != 0:
            patrimonio_estimado = vpa_val * shares
            roe = (lucro_l / patrimonio_estimado) * 100
        else:
            roe = get_val('returnOnEquity', 0) * 100
            
        roic = 0 

        # --- Calculo de Dívida Líquida e Liquidez ---
        total_debt = get_val('totalDebt', 0)
        total_cash = get_val('totalCash', 0)
        ebitda = get_val('ebitda', 0)
        
        net_debt = total_debt - total_cash
        if ebitda != 0:
            div_liq_ebitda = net_debt / ebitda
        else:
            div_liq_ebitda = 0
            
        liq_corrente = get_val('currentRatio', 0)

        # --- Histórico de Proventos ---
        proventos_hist = obter_historico_dividendos(symbol)

        # --- Estrutura para Gráficos (Raw Data) ---
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
                'website': website
            },
            'price': price,
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
