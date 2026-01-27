import yfinance as yf
import pandas as pd
import numpy as np

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
        
        # Verifica se retornou algo válido (algum campo chave)
        if not info or 'regularMarketPrice' not in info:
            # Tenta verificar se é um erro de ticker ou dado vazio
            # Às vezes o yfinance retorna dict incompleto
            if not info or len(info) < 5:
                print(f"Dados insuficientes retornados para {symbol}.")
                return None

        # Helper para pegar valor seguro (0 se None)
        def get_val(key, default=0):
            val = info.get(key)
            return val if val is not None else default

        # 3. Mapeamento de Dados
        
        # --- Preço e Meta ---
        price = get_val('currentPrice', get_val('regularMarketPrice', 0))
        company_name = info.get('longName', ticker)
        
        # --- Valuation ---
        # 1. P/L (Preço / Lucro por Ação)
        # Yahoo 'trailingPE' falha muito em ativos BR; calculamos manualmente.
        lpa = get_val('trailingEps', 0)
        if lpa != 0:
            pl = price / lpa
        else:
            pl = get_val('trailingPE', 0) # Fallback
            
        # 2. P/VP (Preço / Valor Patrimonial por Ação)
        vpa = get_val('bookValue', 0)
        if vpa != 0:
            pvp = price / vpa
        else:
            pvp = get_val('priceToBook', 0) # Fallback
            
        # 3. Dividend Yield
        # Multiplicamos por 100 se vier em decimal (0.03 -> 3%)
        div_yield_raw = get_val('dividendYield', 0)
        if div_yield_raw < 1 and div_yield_raw > 0:
            div_yield = div_yield_raw * 100
        else:
            div_yield = div_yield_raw # Já veio em % (ex: 15.64)
            
        # 4. EV/EBITDA
        ev_ebitda = get_val('enterpriseToEbitda', 0)
        
        # 5. LPA (EPS Trailing) - Já calculado acima
        # 6. VPA (Book Value per Share) - Já calculado acima

        # --- Eficiência ---
        # Margens (Yahoo retorna decimal, ex: 0.15 para 15%)
        margem_bruta = get_val('grossMargins', 0) * 100
        margem_liquida = get_val('profitMargins', 0) * 100
        
        # 1. ROE (Lucro Líquido / Patrimônio Líquido)
        # Yahoo 'returnOnEquity' costuma ser impreciso para BR.
        # PL = VPA * Quantidade de Ações
        shares = get_val('sharesOutstanding', 0)
        vpa_val = get_val('bookValue', 0)
        lucro_l = get_val('netIncomeToCommon', get_val('netIncome', 0))
        
        if shares > 0 and vpa_val > 0 and lucro_l != 0:
            patrimonio_estimado = vpa_val * shares
            roe = (lucro_l / patrimonio_estimado) * 100
        else:
            roe = get_val('returnOnEquity', 0) * 100 # Fallback 0.05 -> 5%
        # Front espera 0 se não tiver.
        roic = 0 

        # --- Calculo de Dívida Líquida e Liquidez ---
        total_debt = get_val('totalDebt', 0)
        total_cash = get_val('totalCash', 0) # Disponibilidades
        ebitda = get_val('ebitda', 0)
        
        # Dívida Líquida = Dívida Bruta - Caixa
        net_debt = total_debt - total_cash
        
        # Dívida Liq / EBITDA
        if ebitda != 0:
            div_liq_ebitda = net_debt / ebitda
        else:
            div_liq_ebitda = 0
            
        # Liquidez Corrente
        liq_corrente = get_val('currentRatio', 0)

        # --- Estrutura para Gráficos (Raw Data) ---
        receita_liquida = get_val('totalRevenue', 0)
        lucro_liquido = get_val('netIncomeToCommon', get_val('netIncome', 0))
        
        # Patrimônio Líquido (Nem sempre explícito, calculamos via VPA * Ações se faltar, ou usamos bookValue direto??)
        # Yahoo tem 'totalStockholderEquity' em alguns endpoints, mas bookValue * sharesOutstanding é seguro.
        shares = get_val('sharesOutstanding', 0)
        if shares > 0 and vpa > 0:
            patrimonio_liquido = vpa * shares
        else:
            patrimonio_liquido = 0 # Fallback

        # Montagem do JSON Final (Mantendo contrato com fundamentals.js)
        result = {
            'meta': {
                'ticker': ticker,
                'empresa_cvm': company_name,
                'ano_base': 'TTM (Yahoo)',
                'url_relatorio': f"https://finance.yahoo.com/quote/{symbol}"
            },
            'price': price,
            'valuation': {
                'P/L': round(pl, 2),
                'P/VP': round(pvp, 2),
                'EV_Ebitda': round(ev_ebitda, 2),
                'Div_Yield': round(div_yield, 2),
                'LPA': round(lpa, 2),
                'VPA': round(vpa, 2)
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
    # Teste rápido
    import json
    t = "WEGE3"
    data = processar_ativo(t)
    if data:
        print(json.dumps(data, indent=4))
