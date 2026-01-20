import pandas as pd
import os
import re

def load_clean_assets(csv_path='data/lista_ativos.csv'):
    """
    Carrega e filtra a lista de ativos do arquivo CSV exportado do MT5.
    Retorna uma lista contendo primeiros os Futuros (WIN/WDO atuais) e depois ações.
    """
    fallback_std = ["PETR4", "VALE3", "WING26"]
    
    # Resolve path relative to the application root if needed
    if not os.path.exists(csv_path):
        # Try finding it relative to current working directory or script location
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        csv_path_abs = os.path.join(base_dir, csv_path)
        if not os.path.exists(csv_path_abs):
            print(f"⚠️  Arquivo {csv_path} não encontrado. Usando fallback.")
            return fallback_std
        csv_path = csv_path_abs

    try:
        # Tenta ler detectando separador (MT5 as vezes usa Tab ou Ponto-e-virgula)
        # encoding 'utf-16' é comum em exports do MT5, mas 'utf-8' ou 'cp1252' também possiveis.
        # Vamos tentar engine python que é mais permissiva
        try:
             df = pd.read_csv(csv_path, sep=None, engine='python', encoding='utf-8')
        except:
             df = pd.read_csv(csv_path, sep='\t', encoding='utf-16')
             
    except Exception as e:
        print(f"⚠️  Erro ao ler CSV: {e}. Usando fallback.")
        return fallback_std

    # Normalizar colunas
    df.columns = [c.strip() for c in df.columns]
    
    required_cols = ['Symbol', 'Path']
    if not all(col in df.columns for col in required_cols):
        print(f"⚠️  Colunas faltando no CSV (Esperado: {required_cols}). Usando fallback.")
        return fallback_std

    # ==========================
    # 1. FILTRAR AÇÕES (STOCKS)
    # ==========================
    # Contém "Equities" no Path
    try:
        mask_equities = df['Path'].str.contains('Equities', case=False, na=False)
        df_stocks = df[mask_equities].copy()

        # Remover Fracionários (terminam com dígito + F, ex: 4F)
        # Regex: \dF$ -> Encontra numero seguido de F no final da string
        mask_frac = df_stocks['Symbol'].str.contains(r'\dF$', regex=True, na=False)
        df_stocks = df_stocks[~mask_frac]

        # Remover Opções (Lenght > 6)
        # Ações padrão: XXXX3 (5), XXXX11 (6). Opções costumam ser maiores ou ter letras no meio.
        df_stocks = df_stocks[df_stocks['Symbol'].str.len() <= 6]
        
        stocks_list = df_stocks['Symbol'].unique().tolist()
        stocks_list.sort() # Ordem alfabética
    except Exception as e:
        print(f"Erro ao filtrar ações: {e}")
        stocks_list = []

    # ============================
    # 2. FILTRAR FUTUROS (FUTURES)
    # ============================
    # Path tem BMF ou Derivatives
    try:
        mask_futures_path = df['Path'].str.contains(r'BMF|Derivatives', case=False, regex=True, na=False)
        df_futures = df[mask_futures_path].copy()

        # Apenas WIN e WDO
        mask_win_wdo = df_futures['Symbol'].str.match(r'^(WIN|WDO)')
        df_futures = df_futures[mask_win_wdo]

        # Vigentes (tem "26" ou o ano atual, mas vamos focar no pedido "26")
        # Para ser mais robusto, poderiamos pegar current year.
        # Mas o user pediu explicitamente para limpar coisas velhas.
        
        # Vamos assumir contratos vigentes contendo "26" (ano 2026)
        mask_current = df_futures['Symbol'].str.contains('26')
        df_futures = df_futures[mask_current]

        futures_list = df_futures['Symbol'].unique().tolist()
        futures_list.sort()
    except Exception as e:
        print(f"Erro ao filtrar futuros: {e}")
        futures_list = []

    # ==========================
    # 3. MERGE & OUTPUT
    # ==========================
    final_list = futures_list + stocks_list
    
    # Deduplicate preserving order
    clean = []
    seen = set()
    for item in final_list:
        if item not in seen:
            clean.append(item)
            seen.add(item)
            
    if not clean:
        return fallback_std

    return clean
