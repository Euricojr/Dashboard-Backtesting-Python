from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()
import pandas as pd
import numpy as np
import yfinance as yf
import traceback
from datetime import datetime
from groq import Groq  # Import Groq

import backtest  # Agora no mesmo diretório

app = Flask(__name__, static_folder='../frontend', static_url_path='')

@app.route('/')
def home():
    return app.send_static_file('index.html')
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

# Configuração Groq
import os
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
groq_client = None

try:
    groq_client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    print(f"Erro ao inicializar Groq: {e}")

def generate_analysis_text(metrics, trade_stats):
    """
    Gera análise textual usando Groq AI (Llama 3 70B).
    """
    try:
        if not groq_client:
            return "<strong>Erro:</strong> Cliente Groq não inicializado.", False
            
        # Preparar dados para o prompt
        data_str = f"""
        [DADOS DO BACKTEST - PERÍODO TOTAL]
        - Retorno Total: {metrics.get('Total Return', 0):.2%}
        - Sharpe Ratio: {metrics.get('Sharpe Ratio', 0):.2f}
        - Drawdown Máximo: {metrics.get('Max Drawdown', 0):.2%}
        - Volatilidade Anual: {metrics.get('Vol Anual', 0):.2%}
        - Win Rate: {trade_stats.get('win_rate', 0):.2%} (Total Trades: {trade_stats.get('total_trades', 0)})
        - Profit Factor: {trade_stats.get('profit_factor', 0):.2f}
        
        BENCHMARK (BUY & HOLD):
        - Retorno: {metrics.get('BH_Total', 0):.2%}
        """
        
        prompt = f"""
        Você é um analista quantitativo sênior da FinSense. Analise os resultados deste backtest total (estratégia vs buy & hold).
        
        {data_str}
        
        Gere um relatório HTML curto (apenas tags <p>, <b>, <br>) com 3 parágrafos concisos:
        1. **Veredito**: A estratégia superou o Buy & Hold? É lucrativa e estável?
        2. **Pontos Fortes**: Analise o Profit Factor, Sharpe e Win Rate.
        3. **Riscos/Alertas**: Comente sobre o Drawdown e volatilidade.
        
        Se houver prejuízo ou drawdown excessivo (>30%), termine com um alerta claro em vermelho (usando style='color: #FF4560').
        Não use markdown, apenas HTML básico (<b>, <br>). Seja direto e profissional.
        """
        
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Você é um especialista em trading quantitativo da FinSense.",
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=600,
        )
        
        analysis = chat_completion.choices[0].message.content
        
        # Detectar warning simples
        is_warning = False
        if metrics.get('Total Return', 0) < 0 or metrics.get('Max Drawdown', 0) < -0.30:
            is_warning = True
            
        return analysis, is_warning

    except Exception as e:
        print(f"Erro na geração IA: {e}")
        return f"<strong>Erro na análise IA:</strong> {str(e)}", False

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
        strategy_name = data_req.get('strategy', 'SMA') 
        
        print(f"Executando backtest total para {ticker}. Estratégia: {strategy_name}")
        
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
        if strategy_name == "RSI":
            res = backtest.strategy_rsi_weekly(df, lower=35, upper=70)
        else:
            res = backtest.strategy_sma_crossover(df, short_window=sma_short, long_window=sma_long)
        
        # Cálculo de Métricas (PERÍODO INTEGRAL)
        m_raw = backtest.calculate_metrics(res['Strategy_Returns'])
        bh_metrics = backtest.calculate_metrics(res['Close'].pct_change())
        m_raw['BH_Total'] = bh_metrics['Total Return']
        
        # Trade Stats
        trade_stats = backtest.calculate_trade_stats(res)
        
        # IA Analysis
        ai_text, is_warning = generate_analysis_text(m_raw, trade_stats)
        
        # Formatação para o Frontend
        metrics_formatted = {
            "total_return": f"{m_raw.get('Total Return', 0):.2%}",
            "cagr": f"{m_raw.get('CAGR', 0):.2%}",
            "volatilidade_anual": f"{m_raw.get('Vol Anual', 0):.2%}",
            "sharpe_ratio": f"{m_raw.get('Sharpe Ratio', 0):.2f}",
            "max_drawdown": f"{m_raw.get('Max Drawdown', 0):.2%}"
        }

        # Dados para Gráficos
        res['Strategy_Cumulative'] = (1 + res['Strategy_Returns'].fillna(0)).cumprod()
        asset_rets = res['Close'].pct_change()
        res['Asset_Cumulative'] = (1 + asset_rets.fillna(0)).cumprod()
        
        equity_data = []
        for i, r in res.iterrows():
            equity_data.append({
                "time": i.strftime('%Y-%m-%d'),
                "strategy": float(r['Strategy_Cumulative']),
                "asset": float(r['Asset_Cumulative'])
            })

        candle_data = []
        for i, r in df.iterrows():
            candle_data.append({
                "time": i.strftime('%Y-%m-%d'), 
                "open": float(r['Open']), 
                "high": float(r['High']), 
                "low": float(r['Low']), 
                "close": float(r['Close'])
            })
            
        # Marcadores (Trades)
        res['trades'] = res['Signal'].diff()
        markers = []
        for index, row in res.iterrows():
            if row['trades'] == 1:
                markers.append({"time": index.strftime('%Y-%m-%d'), "position": "belowBar", "color": "#00E396", "shape": "arrowUp", "text": "COMPRA"})
            elif row['trades'] == -1:
                markers.append({"time": index.strftime('%Y-%m-%d'), "position": "aboveBar", "color": "#FF4560", "shape": "arrowDown", "text": "VENDA"})

        # SMA Data
        sma_short_data = []
        sma_long_data = []
        if 'SMA_Short' in res.columns:
            for i, r in res.iterrows():
                if not pd.isna(r['SMA_Short']):
                    sma_short_data.append({"time": i.strftime('%Y-%m-%d'), "value": float(r['SMA_Short'])})
        
        if 'SMA_Long' in res.columns:
             for i, r in res.iterrows():
                if not pd.isna(r['SMA_Long']):
                    sma_long_data.append({"time": i.strftime('%Y-%m-%d'), "value": float(r['SMA_Long'])})

        # Montagem do JSON Final (Sem Split)
        response_data = {
            "metrics": metrics_formatted,
            "trade_stats": trade_stats,
            "candle_data": candle_data,
            "equity_data": equity_data,
            "sma_short_data": sma_short_data,
            "sma_long_data": sma_long_data,
            "markers": markers,
            "ai_analysis": ai_text,
            "is_warning": is_warning,
            "ticker": ticker
        }
        
        return jsonify(clean_for_json(response_data))

        # SMA Data (if available)
        sma_short_data = []
        sma_long_data = []
        if 'SMA_Short' in res.columns:
            for i, r in res.iterrows():
                if not pd.isna(r['SMA_Short']):
                    sma_short_data.append({"time": i.strftime('%Y-%m-%d'), "value": float(r['SMA_Short'])})
        
        if 'SMA_Long' in res.columns:
             for i, r in res.iterrows():
                if not pd.isna(r['SMA_Long']):
                    sma_long_data.append({"time": i.strftime('%Y-%m-%d'), "value": float(r['SMA_Long'])})

        # Montagem do JSON Final
        response_data = {
            "metrics_in": metrics_in,
            "metrics_out": metrics_out,
            "trade_stats_in": trade_stats_in,
            "trade_stats_out": trade_stats_out,
            "candle_data": candle_data,
            "equity_data": equity_data,
            "sma_short_data": sma_short_data,
            "sma_long_data": sma_long_data,
            "split_date": split_date,
            "markers": markers,
            "ai_analysis": ai_text,
            "is_warning": is_warning,
            "ticker": ticker
        }
        
        return jsonify(clean_for_json(response_data))
        
    except Exception as e:
        print("ERRO NO BACKEND:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/batch_backtest', methods=['POST'])
def run_batch_backtest():
    try:
        data_req = request.json
        category_key = data_req.get('category', 'BR_STOCKS') # Key from CATEGORIES
        start_date = data_req.get('start', '2023-01-01')
        end_date = data_req.get('end', '2024-01-01')
        sma_short = int(data_req.get('sma_short', 20))
        sma_long = int(data_req.get('sma_long', 50))
        strategy_name = data_req.get('strategy', 'SMA')
        
        tickers_map = {}
        if category_key == 'ALL':
             for cat in CATEGORIES.values():
                 tickers_map.update(cat)
        else:
            # Encontra a categoria pelo nome (ex: "🇧🇷 Ações Brasil") ou chave direta se fosse o caso
            # O frontend vai mandar o label da chave provavelmente.
            # Vamos simplificar: O frontend manda a Key do dicionário CATEGORIES? 
            # O dicionário CATEGORIES tem chaves com emojis. O frontend manda isso?
            # Vamos assumir que o frontend manda a chave exata de CATEGORIES
             tickers_map = CATEGORIES.get(category_key, {})

        results = []
        
        print(f"Iniciando Batch para {len(tickers_map)} ativos. Categoria: {category_key}")
        
        for ticker, name in tickers_map.items():
            try:
                # 1. Download (Otimizado: apenas colunas essenciais)
                df = yf.download(ticker, start=start_date, end=end_date, progress=False)
                
                if df.empty: continue
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                
                # Check min length
                if len(df) < 50: continue

                # 2. Strategy
                if strategy_name == "RSI":
                    res = backtest.strategy_rsi_weekly(df, lower=35, upper=70)
                else:
                    res = backtest.strategy_sma_crossover(df, short_window=sma_short, long_window=sma_long)
                
                # 3. Split (50/50)
                limit = int(len(res) * 0.5)
                res_oos = res.iloc[limit:].copy()
                
                # 4. Metrics OOS
                m_oos = backtest.calculate_metrics(res_oos['Strategy_Returns'])
                
                results.append({
                    "ticker": ticker,
                    "name": name,
                    "return_out": m_oos.get('Total Return', 0),
                    "sharpe_out": m_oos.get('Sharpe Ratio', 0),
                    "drawdown_out": m_oos.get('Max Drawdown', 0)
                })
                
            except Exception as e:
                print(f"Erro ao processar {ticker}: {e}")
                continue
        
        # Sort by Return OOS Descending
        results.sort(key=lambda x: x['return_out'], reverse=True)
        
        return jsonify(clean_for_json(results))

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
