import os
import pandas as pd

def load_clean_assets():
    """
    Retorna lista dos ativos APROVADOS no Scanner Elite.
    Caso não exista ou falhe, retorna uma lista padrão.
    """
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'backtest_results.csv')
    
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path, sep=';', decimal=',')
            # Filtra apenas os aprovados
            approved = df[df['Status'] == 'APROVADO']['Ticker'].tolist()
            # Remove sufixo .SA
            clean_list = [t.replace('.SA', '') for t in approved]
            
            # Garante que os futuros continuem na lista de monitoramento e front-end
            if "WINJ26" not in clean_list: clean_list.insert(0, "WINJ26")
            if "WDOG26" not in clean_list: clean_list.insert(0, "WDOG26")
            
            # Remove duplicatas e retorna
            return sorted(list(set(clean_list)))
        except Exception as e:
            print(f"Erro ao ler os ativos filtrados: {e}")
            
    # Fallback default se o CSV não existir:
    whitelist = [
        "WINJ26", "WDOG26", "BOVA11", "SMAL11", "IVVB11",
        "PETR4", "VALE3", "ITUB4", "BBDC4", "BBAS3"
    ]
    return sorted(list(set(whitelist)))
