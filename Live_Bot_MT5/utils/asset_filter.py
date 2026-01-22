import pandas as pd
import os
import re

def load_clean_assets(csv_path='data/lista_ativos.csv'):
    """
    Carrega e filtra a lista de ativos do arquivo CSV exportado do MT5.
    Retorna um dicionário: { "Indices": [...], "Acoes": [...] }
    """
    fallback_std = {
        "Indices": ["WING26", "WDOG26"],
        "Acoes": ["ABEV3", "PETR4", "VALE3", "BOVA11"]
    }
    
    # Resolve path
    if not os.path.exists(csv_path):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        csv_path_abs = os.path.join(base_dir, csv_path)
        if not os.path.exists(csv_path_abs):
            print(f"⚠️  Arquivo {csv_path} não encontrado. Usando fallback.")
            return fallback_std
        csv_path = csv_path_abs

    try:
        # Tenta ler CSV
        try:
            df = pd.read_csv(csv_path, sep=None, engine='python', encoding='utf-8')
        except:
            df = pd.read_csv(csv_path, sep='\t', encoding='utf-16')
    except Exception as e:
        print(f"⚠️  Erro ao ler CSV: {e}. Usando fallback.")
        return fallback_std

    # Normalizar colunas
    df.columns = [c.strip() for c in df.columns]
    if 'Symbol' not in df.columns:
        return fallback_std

    all_symbols = df['Symbol'].dropna().astype(str).unique().tolist()
    
    indices = []
    acoes = []

    # REGRAS REGEX
    
    # 1. Ações (Stocks)
    # 4 Letras Maiúsculas + Sufixo (3, 4, 5, 6, 11)
    # Exclui automaticamente: BDRs (32,33,34,35), Fracionários (F), Opções
    regex_stock = re.compile(r'^[A-Z]{4}(3|4|5|6|11)$')
    
    # 2. Futuros (Futures)
    # WIN/WDO/IND/DOL + Letra Mês + Ano (25, 26, 27)
    regex_future = re.compile(r'^(WIN|WDO|IND|DOL)[A-Z](25|26|27)$')

    for s in all_symbols:
        s = s.strip()
        
        # Check Futures
        if regex_future.match(s):
            indices.append(s)
            continue # Se é futuro, não é ação
            
        # Check Stocks
        if regex_stock.match(s):
            acoes.append(s)

    # Ordenação
    indices.sort()
    acoes.sort()
    
    # Validação Mínima
    if not indices and not acoes:
        return fallback_std

    return {
        "Indices": indices,
        "Acoes": acoes
    }
