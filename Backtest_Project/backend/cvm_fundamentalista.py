import pandas as pd
import requests
import zipfile
import io
import yfinance as yf

def obter_dados_cvm(ano):
    """
    Baixa e lê os arquivos de dados financeiros da CVM (DFP) para o ano especificado.
    Retorna dataframes contendo BPA, BPP, DRE e DFC (Método Indireto).
    """
    base_url = f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_{ano}.zip"
    print(f"[CVM] Baixando dados de {ano}...")
    
    try:
        response = requests.get(base_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao baixar dados da CVM: {e}")
        return None, None, None, None

    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        # Definir nomes dos arquivos esperados dentro do ZIP
        file_bpa = f'dfp_cia_aberta_BPA_con_{ano}.csv'
        file_bpp = f'dfp_cia_aberta_BPP_con_{ano}.csv'
        file_dre = f'dfp_cia_aberta_DRE_con_{ano}.csv'
        file_dfc = f'dfp_cia_aberta_DFC_MI_con_{ano}.csv' # Fluxo de Caixa Método Indireto

        try:
            # Ler arquivos CSV com encoding ISO-8859-1 (padrão CVM)
            print("[CVM] Processando BPA...")
            bpa = pd.read_csv(z.open(file_bpa), sep=';', encoding='ISO-8859-1')
            
            print("[CVM] Processando BPP...")
            bpp = pd.read_csv(z.open(file_bpp), sep=';', encoding='ISO-8859-1')
            
            print("[CVM] Processando DRE...")
            dre = pd.read_csv(z.open(file_dre), sep=';', encoding='ISO-8859-1')
            
            print("[CVM] Processando DFC (Método Indireto)...")
            dfc = pd.read_csv(z.open(file_dfc), sep=';', encoding='ISO-8859-1')
            
            # Filtro básico para garantir 'ORDEM_EXERC' == 'ÚLTIMO' se aplicável
            bpa = bpa[bpa['ORDEM_EXERC'] == 'ÚLTIMO']
            bpp = bpp[bpp['ORDEM_EXERC'] == 'ÚLTIMO']
            dre = dre[dre['ORDEM_EXERC'] == 'ÚLTIMO']
            dfc = dfc[dfc['ORDEM_EXERC'] == 'ÚLTIMO']

        except KeyError as e:
            print(f"Arquivo não encontrado no ZIP: {e}")
            return None, None, None, None

    return bpa, bpp, dre, dfc

def extrair_valor_conta(df, cd_conta, ticker_cvm=None, nome_empresa=None):
    """
    Helper para encontrar valor de uma conta específica usando CD_CONTA.
    """
    # Filtrar pela empresa
    if ticker_cvm:
        df_filtrado = df[df['CD_CVM'] == int(ticker_cvm)]
    elif nome_empresa:
        df_filtrado = df[df['DENOM_CIA'].str.contains(nome_empresa, case=False, na=False)]
    else:
        return 0.0

    if df_filtrado.empty:
        return 0.0
    
    # Pegar o dado mais recente
    df_filtrado = df_filtrado.copy()
    df_filtrado['DT_FIM_EXERC'] = pd.to_datetime(df_filtrado['DT_FIM_EXERC'])
    df_filtrado = df_filtrado.sort_values(by='DT_FIM_EXERC', ascending=False)
    
    # Filtrar pela conta
    linha_conta = df_filtrado[df_filtrado['CD_CONTA'] == str(cd_conta)]
    
    if linha_conta.empty:
        return 0.0
    
    valor = linha_conta.iloc[0]['VL_CONTA']
    escala = linha_conta.iloc[0]['ESCALA_MOEDA']
    if escala == 'MIL':
        valor = valor * 1000
    
    return valor

def extrair_depreciacao(dfc, ticker_cvm=None, nome_empresa=None):
    """
    Helper para encontrar Depreciação/Amortização na DFC.
    Busca por termos na descrição da conta (DS_CONTA) dentro do grupo 6.01.
    """
    if ticker_cvm:
        df_filtrado = dfc[dfc['CD_CVM'] == int(ticker_cvm)]
    elif nome_empresa:
        df_filtrado = dfc[dfc['DENOM_CIA'].str.contains(nome_empresa, case=False, na=False)]
    else:
        return 0.0

    if df_filtrado.empty:
        return 0.0
    
    # Pegar dado mais recente
    df_filtrado = df_filtrado.copy()
    df_filtrado['DT_FIM_EXERC'] = pd.to_datetime(df_filtrado['DT_FIM_EXERC'])
    df_filtrado = df_filtrado.sort_values(by='DT_FIM_EXERC', ascending=False)
    
    # Filtrar contas relevantes 
    # Segurança: Apenas contas que começam com 6.01 (Ajustes do Lucro na DFC-MI)
    df_filtrado = df_filtrado[df_filtrado['CD_CONTA'].astype(str).str.startswith('6.01', na=False)]
    
    if df_filtrado.empty:
        return 0.0

    # Termos expandidos para Commodities (Oil & Gas)
    termo_regex = r'Deprec|Amort|Exaust|Impairment|Perda\sRecup|Vida\sUtil'
    
    df_filtro_contas = df_filtrado[
        df_filtrado['DS_CONTA'].str.contains(termo_regex, case=False, na=False)
    ]
    
    if df_filtro_contas.empty:
        return 0.0
    
    # Somar todos os valores encontrados
    # Importante: Na DFC Método Indireto, estes são ajustes positivos ao lucro.
    valor_total = df_filtro_contas['VL_CONTA'].sum()
    
    # Ajustar escala
    escala = df_filtro_contas.iloc[0]['ESCALA_MOEDA']
    if escala == 'MIL':
        valor_total = valor_total * 1000
        
    return abs(valor_total) # Força positivo

def calcular_fundamentos(ticker, preco_atual, bpa, bpp, dre, dfc, nome_empresa=None, cvm_code=None):
    """
    Calcula indicadores fundamentalistas, incluindo EBITDA real via DFC.
    """
    
    search_name = nome_empresa if nome_empresa else ticker
    search_cvm = cvm_code

    print(f"Calculando fundamentos para: {search_name if search_name else search_cvm} | Preço: {preco_atual}")

    # --- Extração de Dados ---
    
    # Balanço Patrimonial
    ativo_total = extrair_valor_conta(bpa, '1', search_cvm, search_name)
    ativo_circulante = extrair_valor_conta(bpa, '1.01', search_cvm, search_name)
    caixa_equivalentes = extrair_valor_conta(bpa, '1.01.01', search_cvm, search_name)
    passivo_circulante = extrair_valor_conta(bpp, '2.01', search_cvm, search_name)
    patrimonio_liquido = extrair_valor_conta(bpp, '2.03', search_cvm, search_name)
    
    divida_cp = extrair_valor_conta(bpp, '2.01.04', search_cvm, search_name)
    divida_lp = extrair_valor_conta(bpp, '2.02.01', search_cvm, search_name)
    divida_bruta = divida_cp + divida_lp
    divida_liquida = divida_bruta - caixa_equivalentes
    
    # DRE
    receita_liquida = extrair_valor_conta(dre, '3.01', search_cvm, search_name)
    ebit = extrair_valor_conta(dre, '3.05', search_cvm, search_name)
    lucro_liquido = extrair_valor_conta(dre, '3.11', search_cvm, search_name)
    lucro_bruto = extrair_valor_conta(dre, '3.03', search_cvm, search_name)
    
    # DFC (Depreciação)
    depreciacao = extrair_depreciacao(dfc, search_cvm, search_name)
    
    # EBITDA
    ebitda = ebit + depreciacao

    # --- Cálculos ---
    
    try:
        yf_ticker = yf.Ticker(f"{ticker}.SA")
        info = yf_ticker.info
        shares = info.get('sharesOutstanding', 0)
    except:
        shares = 0
        print("Aviso: Não foi possível obter número de ações do Yahoo Finance.")

    # Valuation Simples
    vpa = patrimonio_liquido / shares if shares > 0 else 0
    lpa = lucro_liquido / shares if shares > 0 else 0
    pl = preco_atual / lpa if lpa > 0 else 0
    pvp = preco_atual / vpa if vpa > 0 else 0
    
    # Enterprise Value (EV) = Market Cap + Dívida Líquida
    market_cap = preco_atual * shares
    ev = market_cap + divida_liquida
    
    # EV/EBITDA
    ev_ebitda = ev / ebitda if ebitda > 0 else 0
    
    # Margens
    margem_liquida = (lucro_liquido / receita_liquida) * 100 if receita_liquida > 0 else 0
    margem_bruta = (lucro_bruto / receita_liquida) * 100 if receita_liquida > 0 else 0
    
    # ROE
    roe = (lucro_liquido / patrimonio_liquido) * 100 if patrimonio_liquido > 0 else 0
    
    # Liquidez
    liq_corrente = ativo_circulante / passivo_circulante if passivo_circulante > 0 else 0
    
    # Dívida Líquida / EBITDA
    div_liq_ebitda = divida_liquida / ebitda if ebitda > 0 else 0

    return {
        "valuation": {
            "P/L": round(pl, 2),
            "P/VP": round(pvp, 2),
            "LPA": round(lpa, 2),
            "VPA": round(vpa, 2),
            "EV_Ebitda": round(ev_ebitda, 2)
        },
        "endividamento": {
            "DivLiq_Ebitda": round(div_liq_ebitda, 2),
            "Liq_Corrente": round(liq_corrente, 2),
            "Div_Bruta": round(divida_bruta, 2)
        },
        "eficiencia": {
            "Margem_Bruta": round(margem_bruta, 2),
            "Margem_Liquida": round(margem_liquida, 2),
            "ROE": round(roe, 2)
        },
        "raw": {
            "receita_liquida": receita_liquida,
            "ebit": ebit,
            "depreciacao": depreciacao,
            "ebitda": ebitda,
            "lucro_liquido": lucro_liquido,
            "ativo_total": ativo_total,
            "patrimonio_liquido": patrimonio_liquido,
            "divida_bruta": divida_bruta,
            "market_cap": market_cap,
            "ev": ev
        }
    }

if __name__ == "__main__":
    # Teste rápido
    import sys
    
    ano_teste = 2023
    print(f"--- Iniciando Teste (Ano {ano_teste}) ---")
    
    bpa, bpp, dre, dfc = obter_dados_cvm(ano_teste)
    
    if bpa is not None and dfc is not None:
        # Exemplo: PETR4 (Petrobras)
        ticker_teste = "PETR4"
        nome_empresa_simulada = "PETROLEO BRASILEIRO" 
        
        pk_price = 38.0 
        
        try:
             t = yf.Ticker(f"{ticker_teste}.SA")
             hist = t.history(period="1d")
             if not hist.empty:
                 pk_price = hist['Close'].iloc[-1]
                 print(f"Preço Yahoo: {pk_price}")
        except Exception as e:
            print(f"Erro yahoo: {e}")

        resultado = calcular_fundamentos(
            ticker=ticker_teste, 
            preco_atual=pk_price, 
            bpa=bpa, 
            bpp=bpp, 
            dre=dre, 
            dfc=dfc,
            nome_empresa=nome_empresa_simulada
        )
        
        import json
        print("\nResultado JSON:")
        print(json.dumps(resultado, indent=4))
