from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import yfinance as yf
import sys
import os
import traceback
from datetime import datetime

# Adiciona o diretório raiz ao path para importar o backtest.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backtest import strategy_sma_crossover, calculate_metrics

app = Flask(__name__)
CORS(app)

# --- BIBLIOTECAS DE ATIVOS ---
BR_STOCKS = {
    "PETR4.SA": "Petrobras (PETR4)", "VALE3.SA": "Vale (VALE3)", "ITUB4.SA": "Itaú Unibanco (ITUB4)",
    "BBAS3.SA": "Banco do Brasil (BBAS3)", "BBDC4.SA": "Bradesco (BBDC4)", "ABEV3.SA": "Ambev (ABEV3)",
    "WEGE3.SA": "Weg (WEGE3)", "JBSS3.SA": "JBS (JBSS3)", "ELET3.SA": "Eletrobras (ELET3)",
    "B3SA3.SA": "B3 (B3SA3)", "RENT3.SA": "Localiza (RENT3)", "SUZB3.SA": "Suzano (SUZB3)",
    "GGBR4.SA": "Gerdau (GGBR4)", "RDOR3.SA": "Rede D'Or (RDOR3)", "RADL3.SA": "RaiaDrogasil (RADL3)",
    "HAPV3.SA": "Hapvida (HAPV3)", "CSAN3.SA": "Cosan (CSAN3)", "VIVT3.SA": "Vivo (VIVT3)",
    "CPLE6.SA": "Copel (CPLE6)", "EQTL3.SA": "Equatorial (EQTL3)", "BBSE3.SA": "BB Seguridade (BBSE3)",
    "RAIZ4.SA": "Raízen (RAIZ4)", "UGPA3.SA": "Ultrapar (UGPA3)", "LREN3.SA": "Lojas Renner (LREN3)",
    "PRIO3.SA": "Prio (PRIO3)", "CMIG4.SA": "Cemig (CMIG4)", "ENEV3.SA": "Eneva (ENEV3)",
    "ASAI3.SA": "Assaí (ASAI3)", "TOTS3.SA": "Totvs (TOTS3)", "SBSP3.SA": "Sabesp (SBSP3)",
    "VBBR3.SA": "Vibra (VBBR3)", "CCRO3.SA": "CCR (CCRO3)", "TIMS3.SA": "TIM (TIMS3)",
    "CPFE3.SA": "CPFL Energia (CPFE3)", "STBP3.SA": "Santos Brasil (STBP3)", "EMBR3.SA": "Embraer (EMBR3)",
    "GOAU4.SA": "Gerdau Metalúrgica (GOAU4)", "ALOS3.SA": "Allos (ALOS3)", "CYRE3.SA": "Cyrela (CYRE3)",
    "EGIE3.SA": "Engie (EGIE3)", "CSNA3.SA": "Siderúrgica Nac (CSNA3)", "YDUQ3.SA": "Yduqs (YDUQ3)",
    "MRFG3.SA": "Marfrig (MRFG3)", "COGN3.SA": "Cogna (COGN3)", "MRVE3.SA": "MRV (MRVE3)",
    "BRKM5.SA": "Braskem (BRKM5)", "MULT3.SA": "Multiplan (MULT3)", "CRFB3.SA": "Carrefour BR (CRFB3)",
    "PCAR3.SA": "Pão de Açúcar (PCAR3)", "MGLU3.SA": "Magalu (MGLU3)"
}

US_STOCKS = {
    "AAPL": "Apple (AAPL)", "MSFT": "Microsoft (MSFT)", "NVDA": "NVIDIA (NVDA)", "GOOGL": "Alphabet (GOOGL)",
    "AMZN": "Amazon (AMZN)", "META": "Meta (META)", "TSLA": "Tesla (TSLA)", "BRK-B": "Berkshire (BRK-B)",
    "LLY": "Eli Lilly (LLY)", "AVGO": "Broadcom (AVGO)", "WMT": "Walmart (WMT)", "JPM": "JPMorgan (JPM)",
    "V": "Visa (V)", "ORCL": "Oracle (ORCL)", "XOM": "Exxon Mobil (XOM)", "MA": "Mastercard (MA)",
    "JNJ": "Johnson & Johnson (JNJ)", "NFLX": "Netflix (NFLX)", "BAC": "Bank of America (BAC)",
    "ABBV": "AbbVie (ABBV)", "COST": "Costco (COST)", "PG": "Procter & Gamble (PG)", "HD": "Home Depot (HD)",
    "AMD": "AMD (AMD)", "ADBE": "Adobe (ADBE)", "CRM": "Salesforce (CRM)", "KO": "Coca-Cola (KO)",
    "PEP": "PepsiCo (PEP)", "TMO": "Thermo Fisher (TMO)", "DIS": "Disney (DIS)", "CSCO": "Cisco (CSCO)",
    "INTU": "Intuit (INTU)", "PFE": "Pfizer (PFE)", "LIN": "Linde (LIN)", "AMAT": "Applied Materials (AMAT)",
    "CMCSA": "Comcast (CMCSA)", "TXN": "Texas Instr (TXN)", "QCOM": "Qualcomm (QCOM)",
    "PLTR": "Palantir (PLTR)", "MU": "Micron (MU)", "GE": "General Electric (GE)", "CAT": "Caterpillar (CAT)",
    "IBM": "IBM (IBM)", "UBER": "Uber (UBER)", "BA": "Boeing (BA)", "INTC": "Intel (INTC)",
    "GS": "Goldman Sachs (GS)", "MS": "Morgan Stanley (MS)", "SBUX": "Starbucks (SBUX)"
}

CRYPTO = {
    "BTC-USD": "Bitcoin (BTC)", "ETH-USD": "Ethereum (ETH)", "SOL-USD": "Solana (SOL)", "BNB-USD": "BNB (BNB)",
    "XRP-USD": "XRP (XRP)", "DOGE-USD": "Dogecoin (DOGE)", "ADA-USD": "Cardano (ADA)", "TRX-USD": "TRON (TRX)",
    "AVAX-USD": "Avalanche (AVAX)", "DOT-USD": "Polkadot (DOT)", "LINK-USD": "Chainlink (LINK)",
    "SHIB-USD": "Shiba Inu (SHIB)", "BCH-USD": "Bitcoin Cash (BCH)", "LTC-USD": "Litecoin (LTC)",
    "NEAR-USD": "NEAR Protocol (NEAR)", "UNI-USD": "Uniswap (UNI)", "MATIC-USD": "Polygon (MATIC)",
    "ICP-USD": "Internet Computer (ICP)", "ETC-USD": "Ethereum Classic (ETC)", "FIL-USD": "Filecoin (FIL)",
    "XLM-USD": "Stellar (XLM)", "XMR-USD": "Monero (XMR)", "ATOM-USD": "Cosmos (ATOM)", "APT-USD": "Aptos (APT)",
    "HBAR-USD": "Hedera (HBAR)", "VET-USD": "VeChain (VET)", "OP-USD": "Optimism (OP)", "ARB-USD": "Arbitrum (ARB)",
    "RNDR-USD": "Render (RNDR)", "INJ-USD": "Injective (INJ)", "STX-USD": "Stacks (STX)", "KAS-USD": "Kaspa (KAS)",
    "FTM-USD": "Fantom (FTM)", "AAVE-USD": "Aave (AAVE)", "TIA-USD": "Celestia (TIA)", "THETA-USD": "Theta (THETA)",
    "EGLD-USD": "MultiversX (EGLD)", "SAND-USD": "The Sandbox (SAND)", "MANA-USD": "Decentraland (MANA)",
    "EOS-USD": "EOS (EOS)", "FLOW-USD": "Flow (FLOW)", "QNT-USD": "Quant (QNT)", "AXS-USD": "Axie Infinity (AXS)",
    "MKR-USD": "Maker (MKR)", "GRT-USD": "The Graph (GRT)", "SNX-USD": "Synthetix (SNX)", "GALA-USD": "Gala (GALA)",
    "ALGO-USD": "Algorand (ALGO)", "LDO-USD": "Lido DAO (LDO)", "KAVA-USD": "Kava (KAVA)"
}

INDICES = {
    "^BVSP": "IBOVESPA (BR)", "^GSPC": "S&P 500 (US)", "^DJI": "Dow Jones (US)", "^IXIC": "NASDAQ (US)",
    "^NDX": "NASDAQ 100 (US)", "^FTSE": "FTSE 100 (UK)", "^GDAXI": "DAX (GER)", "^FCHI": "CAC 40 (FR)",
    "^N225": "Nikkei 225 (JP)", "^HSI": "Hang Seng (HK)", "^AXJO": "ASX 200 (AU)", "^NSEI": "NIFTY 50 (IN)",
    "^GSPTSE": "S&P/TSX (CA)", "^STOXX50E": "Euro Stoxx 50 (EU)", "000001.SS": "SSE Comp (CN)",
    "399001.SZ": "SZSE Comp (CN)", "^SSMI": "SMI (CH)", "^KS11": "KOSPI (KR)", "^STI": "Straits Times (SG)",
    "^TWII": "TSEC Weighted (TW)"
}

CATEGORIES = {
    "🇧🇷 Ações Brasil": BR_STOCKS,
    "🇺🇸 Ações EUA": US_STOCKS,
    "₿ Criptomoedas": CRYPTO,
    "📊 Índices Globais": INDICES
}

def clean_for_json(obj):
    """
    Substitui NaNs, Infs e tipos Numpy por tipos Python nativos para evitar erro no jsonify
    """
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_json(i) for i in obj]
    elif isinstance(obj, (np.float64, np.float32, float)):
        if np.isnan(obj) or np.isinf(obj):
            return 0.0
        return float(obj)
    elif isinstance(obj, (np.int64, np.int32, int)):
        return int(obj)
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, pd.Series):
        return clean_for_json(obj.tolist())
    elif isinstance(obj, pd.DataFrame):
        return clean_for_json(obj.to_dict(orient='records'))
    return obj

def generate_analysis_text(metrics_in, metrics_out):
    """
    IA Explicativa (Portada do Streamlit)
    """
    total_oos = metrics_out.get('Total Return', 0)
    bh_total = metrics_out.get('BH_Total', 0)
    sharpe_is = metrics_in.get('Sharpe Ratio', 0)
    sharpe_oos = metrics_out.get('Sharpe Ratio', 0)
    max_dd = abs(metrics_out.get('Max Drawdown', 0))

    analysis = "<strong>🤖 Análise da IA (Simulada)</strong><br><br>"
    
    if total_oos > bh_total:
        analysis += f"🚀 <b>Performance Excepcional:</b> A estratégia superou o Buy & Hold no período de teste ({total_oos:.2%} vs {bh_total:.2%}).<br><br>"
    elif total_oos > 0:
        analysis += f"✅ <b>Lucratividade:</b> A estratégia foi lucrativa no teste ({total_oos:.2%}), mas não bateu o B&H ({bh_total:.2%}).<br><br>"
    else:
        analysis += f"❌ <b>Prejuízo:</b> A performance foi negativa no teste ({total_oos:.2%}).<br><br>"
    
    if sharpe_is > 0 and (sharpe_oos < 0 or sharpe_oos < sharpe_is * 0.5):
        analysis += "⚠️ <b>Alerta de Overfitting:</b> O Sharpe caiu drasticamente no teste. Cuidado com o vício de parâmetros!<br><br>"
    else:
        analysis += "💎 <b>Robustez:</b> O desempenho se manteve consistente entre treino e teste.<br><br>"
        
    if max_dd > 0.30:
        analysis += f"🚩 <b>Risco Elevado:</b> O Drawdown de {max_dd:.2%} é preocupante.<br><br>"
    
    is_warning = "Overfitting" in analysis or "Prejuízo" in analysis or bh_total > total_oos
    return analysis, is_warning

@app.route('/assets', methods=['GET'])
def get_assets():
    return jsonify(CATEGORIES)

@app.route('/run_backtest', methods=['POST'])
def run_backtest():
    try:
        data_req = request.json
        ticker = data_req.get('ticker', 'PETR4.SA')
        start_date = data_req.get('start', '2020-01-01')
        end_date = data_req.get('end', '2024-01-01')
        sma_short = int(data_req.get('sma_short', 20))
        sma_long = int(data_req.get('sma_long', 50))
        
        print(f"Executando backtest para {ticker} (SMA {sma_short}/{sma_long})")
        
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if df.empty:
            return jsonify({"error": "Nenhum dado encontrado para o ticker selecionado."}), 400
            
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        # Garante colunas necessárias
        for col in ['Open', 'High', 'Low', 'Close']:
            if col not in df.columns:
                return jsonify({"error": f"Coluna {col} ausente nos dados baixados."}), 400

        # Executa Estratégia
        res = strategy_sma_crossover(df, short_window=sma_short, long_window=sma_long)
        
        # Divisão IS/OOS
        limit = int(len(res) * 0.7)
        if limit < 20: # Evita erro em períodos muito curtos
             return jsonify({"error": "Período muito curto para análise IS/OOS (mínimo 30-50 dias)."}), 400
             
        res_is = res.iloc[:limit]
        res_oos = res.iloc[limit:]
        
        m_is = calculate_metrics(res_is['Strategy_Returns'])
        m_oos = calculate_metrics(res_oos['Strategy_Returns'])
        
        # B&H check
        asset_rets_oos = res_oos['Close'].pct_change()
        bh_metrics = calculate_metrics(asset_rets_oos)
        m_oos['BH_Total'] = bh_metrics['Total Return']

        # Marcadores
        res['trades'] = res['Signal'].diff()
        markers = []
        for index, row in res.iterrows():
            if row['trades'] == 1:
                markers.append({"time": index.strftime('%Y-%m-%d'), "position": "belowBar", "color": "#26a69a", "shape": "arrowUp", "text": "COMPRA"})
            elif row['trades'] == -1:
                markers.append({"time": index.strftime('%Y-%m-%d'), "position": "aboveBar", "color": "#ef5350", "shape": "arrowDown", "text": "VENDA"})

        # Ganho Acumulado OOS para o gráfico de performance
        res_oos = res_oos.copy()
        res_oos['Strategy_Cumulative'] = (1 + res_oos['Strategy_Returns'].fillna(0)).cumprod()
        res_oos['Asset_Cumulative'] = (1 + asset_rets_oos.fillna(0)).cumprod()
        
        perf_data = []
        for i, r in res_oos.iterrows():
            perf_data.append({
                "time": i.strftime('%Y-%m-%d'),
                "strategy": float(r['Strategy_Cumulative']),
                "asset": float(r['Asset_Cumulative'])
            })

        # IA Analysis
        ai_text, is_warning = generate_analysis_text(m_is, m_oos)

        # Candle Data
        candle_data = []
        for i, r in df.iterrows():
            candle_data.append({
                "time": i.strftime('%Y-%m-%d'), 
                "open": float(r['Open']), 
                "high": float(r['High']), 
                "low": float(r['Low']), 
                "close": float(r['Close'])
            })
        
        response_data = {
            "ticker": ticker,
            "candle_data": candle_data,
            "perf_data": perf_data, # Nova série de performance
            "markers": markers,
            "metrics_is": m_is,
            "metrics_oos": m_oos,
            "ai_analysis": ai_text,
            "is_warning": is_warning,
            "split_date": res.index[limit].strftime('%Y-%m-%d')
        }
        
        return jsonify(clean_for_json(response_data))
        
    except Exception as e:
        print("ERRO NO BACKEND:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
