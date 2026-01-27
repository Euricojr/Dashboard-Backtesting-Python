import pandas as pd
import requests
import zipfile
import io
import yfinance as yf
import os
import urllib3

# --- CACHE GLOBAL (Para não baixar toda hora) ---
DATA_CACHE = {
    "BPA": None, "BPP": None, "DRE": None, "DFC": None, "ANO": None
}

# --- DICIONÁRIO DE TRADUÇÃO (Ticker -> Razão Social na CVM) ---
TICKER_TO_CVM_NAME = {
    "PETR4": "PETROLEO BRASILEIRO", "PETR3": "PETROLEO BRASILEIRO",
    "VALE3": "VALE",
    "ITUB4": "ITAU UNIBANCO", "ITUB3": "ITAU UNIBANCO",
    "BBDC4": "BANCO BRADESCO", "BBDC3": "BANCO BRADESCO",
    "BBAS3": "BANCO DO BRASIL",
    "WEGE3": "WEG",
    "ABEV3": "AMBEV",
    "MGLU3": "MAGAZINE LUIZA",
    "VIIA3": "VIA", "BHIA3": "CASAS BAHIA",
    "JBSS3": "JBS",
    "SUZB3": "SUZANO",
    "GGBR4": "GERDAU",
    "CSNA3": "SIDERURGICA NACIONAL",
    "PRIO3": "PRIO",
    "RAIZ4": "RAIZEN",
    "RENT3": "LOCALIZA",
    "B3SA3": "B3",
    "ELET3": "ELETROBRAS", "ELET6": "ELETROBRAS",
    "EMBR3": "EMBRAER",
    "HAPV3": "HAPVIDA",
    "RDOR3": "REDE D'OR",
    "RADL3": "RAIA DROGASIL",
    "EQTL3": "EQUATORIAL",
    "LREN3": "LOJAS RENNER",
    "VIVT3": "TELEFONICA BRASIL", # Vivo é Telefonica na CVM
    "TIMS3": "TIM",
    "CMIG4": "CEMIG",
    "SBSP3": "SABESP",
    "CPLE6": "COPEL",
    "CSAN3": "COSAN",
    "TOTS3": "TOTVS",
    "VBBR3": "VIBRA ENERGIA",
    "BBSE3": "BB SEGURIDADE",
    "ALOS3": "ALLOS", # Antiga Aliansce
    "EGIE3": "ENGIE BRASIL",
    "ENEV3": "ENEVA",
}

def carregar_dados_cache(ano=2024):
    """
    Carrega os dados na memória global apenas uma vez.
    Tenta o ano solicitado. Se falhar, tenta o ano anterior.
    """
    global DATA_CACHE
    
    # Se já carregou este ano e tem dados, retorna do cache
    if DATA_CACHE["ANO"] == ano and DATA_CACHE["BPA"] is not None:
        return DATA_CACHE["BPA"], DATA_CACHE["BPP"], DATA_CACHE["DRE"], DATA_CACHE["DFC"]

    bpa, bpp, dre, dfc = obter_dados_cvm(ano)
    
    # Fallback no Carregamento: Se o arquivo do ano não existir na CVM, tenta anterior
    if bpa is None:
        print(f"⚠️ Dados brutos de {ano} não encontrados. Tentando {ano-1}...")
        if ano < 2020:
            return None, None, None, None
        return carregar_dados_cache(ano - 1)

    # Salva no Cache
    DATA_CACHE["BPA"], DATA_CACHE["BPP"], DATA_CACHE["DRE"], DATA_CACHE["DFC"], DATA_CACHE["ANO"] = bpa, bpp, dre, dfc, ano
    return bpa, bpp, dre, dfc

def processar_ativo(ticker):
    """
    Função Mestra chamada pela API.
    Aplica validação de dados zerados para garantir robustez.
    """
    # 1. Limpeza
    ticker_clean = ticker.upper().replace(".SA", "").strip()
    
    # 2. Tradução (Ticker -> Nome CVM)
    nome_cvm = TICKER_TO_CVM_NAME.get(ticker_clean)
    if not nome_cvm:
        print(f"⚠️ Ticker {ticker_clean} não mapeado, tentando busca fuzzy...")
        nome_cvm = ticker_clean 

    # 3. Preço Yahoo
    try:
        yf_sym = f"{ticker_clean}.SA"
        hist = yf.Ticker(yf_sym).history(period="1d")
        if hist.empty:
            return {"error": "Ticker não encontrado no Yahoo Finance"}
        price = float(hist['Close'].iloc[-1])
    except Exception as e:
        return {"error": f"Erro Yahoo: {str(e)}"}

    # 4. Tenta Dados de 2024 (Ano Base Seguro)
    ano_alvo = 2024
    bpa, bpp, dre, dfc = carregar_dados_cache(ano=ano_alvo)
    
    if bpa is None:
        return {"error": "Dados CVM indisponíveis no momento."}

    # 5. Cálculo Inicial
    try:
        resultado = calcular_fundamentos(
            ticker=ticker_clean,
            preco_atual=price,
            bpa=bpa, bpp=bpp, dre=dre, dfc=dfc,
            nome_empresa=nome_cvm
        )
        
        # 6. Validação "Zero Data"
        # Se Ativo Total for 0, provavelmente a empresa não mandou DFP 2024 ainda ou o nome não bateu.
        # Vamos tentar forçar o ano anterior (2023).
        if resultado['raw']['ativo_total'] == 0:
            print(f"⚠️ Dados zerados em {ano_alvo} para {ticker_clean}. Tentando ano anterior ({ano_alvo - 1})...")
            
            # Força carregamento do ano anterior
            # Nota: Isso vai sobrescrever o cache global, o que é aceitável para buscar dados válidos.
            # Se quiser otimizar depois, poderiamos ter cache por ano.
            global DATA_CACHE
            DATA_CACHE["ANO"] = None # Invalida cache atual para forçar reload
            
            bpa_old, bpp_old, dre_old, dfc_old = carregar_dados_cache(ano=ano_alvo - 1)
            
            if bpa_old is not None:
                resultado = calcular_fundamentos(
                    ticker=ticker_clean,
                    preco_atual=price,
                    bpa=bpa_old, bpp=bpp_old, dre=dre_old, dfc=dfc_old,
                    nome_empresa=nome_cvm
                )
                ano_alvo = ano_alvo - 1 # Atualiza para informar meta correta
            else:
                 print("⚠️ Dados do ano anterior também falharam.")

        # Injeta o ano dos dados no JSON
        resultado["meta"] = {"ano_balanco": ano_alvo, "empresa_cvm": nome_cvm}
        return resultado
        
    except Exception as e:
        print(f"Erro cálculo: {e}")
        return {"error": "Empresa não encontrada nos dados da CVM."}

def obter_dados_cvm(ano):
    """
    Baixa e lê os arquivos de dados financeiros da CVM (DFP) para o ano especificado.
    """
    base_url = f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_{ano}.zip"
    print(f"⬇️ [CVM] Baixando dados de {ano} (Pode demorar)...")
    
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(base_url, headers=headers, verify=False, timeout=120)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro CVM {ano}: {e}")
        return None, None, None, None

    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        try:
            print("[CVM] Lendo CSVs...")
            # Definir nomes dos arquivos esperados dentro do ZIP
            file_bpa = f'dfp_cia_aberta_BPA_con_{ano}.csv'
            file_bpp = f'dfp_cia_aberta_BPP_con_{ano}.csv'
            file_dre = f'dfp_cia_aberta_DRE_con_{ano}.csv'
            file_dfc = f'dfp_cia_aberta_DFC_MI_con_{ano}.csv'

            bpa = pd.read_csv(z.open(file_bpa), sep=';', encoding='ISO-8859-1')
            bpp = pd.read_csv(z.open(file_bpp), sep=';', encoding='ISO-8859-1')
            dre = pd.read_csv(z.open(file_dre), sep=';', encoding='ISO-8859-1')
            dfc = pd.read_csv(z.open(file_dfc), sep=';', encoding='ISO-8859-1')
            
            # Filtro 'ÚLTIMO'
            return (
                bpa[bpa['ORDEM_EXERC'] == 'ÚLTIMO'],
                bpp[bpp['ORDEM_EXERC'] == 'ÚLTIMO'],
                dre[dre['ORDEM_EXERC'] == 'ÚLTIMO'],
                dfc[dfc['ORDEM_EXERC'] == 'ÚLTIMO']
            )

        except KeyError as e:
            print(f"❌ Arquivo não encontrado no ZIP: {e}")
            return None, None, None, None

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
        },
        "price": preco_atual
    }


