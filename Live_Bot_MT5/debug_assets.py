import pandas as pd
import sys
import os

# Adiciona o diretório atual ao path para importar utils
sys.path.append(os.getcwd())

from utils.asset_filter import load_clean_assets

def main():
    print("Carregando ativos filtrados...")
    assets_data = load_clean_assets()
    
    if isinstance(assets_data, list):
        print(f"Modo Whitelist (Lista) detectado.")
        indices = [x for x in assets_data if x.startswith("WI") or x.startswith("WD") or x.startswith("DOL") or x.startswith("IND")]
        acoes = [x for x in assets_data if x not in indices]
    else:
        indices = assets_data.get("Indices", [])
        acoes = assets_data.get("Acoes", [])
    
    print("\n--- ATIVOS FILTRADOS ---")
    print(f"Total Índices: {len(indices)}")
    print(f"Total Ações: {len(acoes)}")
    
    print("\nÍndices:")
    print(", ".join(indices))
    
    print("\nAções (Primeiros 50):")
    print(", ".join(acoes[:50]))
    if len(acoes) > 50:
        print(f"... e mais {len(acoes) - 50} ações.")
        
    # Salvar em CSV para análise detalhada
    all_assets = []
    for asset in indices:
        all_assets.append({"Symbol": asset, "Type": "Indice"})
    for asset in acoes:
        all_assets.append({"Symbol": asset, "Type": "Acao"})
        
    df = pd.DataFrame(all_assets)
    
    # Resolve absolute path to data directory properly
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "data")
    
    # Ensure directory exists
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        
    output_file = os.path.join(data_dir, "filtered_assets_debug.csv")
    df.to_csv(output_file, index=False)
    
    print(f"\nLista completa salva em: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    main()
