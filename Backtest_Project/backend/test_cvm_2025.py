import pandas as pd
import requests
import zipfile
import io
import os

def check_2025():
    ano = 2025
    url = f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_{ano}.zip"
    print(f"Tentando baixar: {url}")
    
    try:
        r = requests.get(url)
        if r.status_code != 200:
            print(f"❌ Erro HTTP {r.status_code}: Arquivo de {ano} ainda não disponível na CVM.")
            return

        print("✅ Download realizado. Verificando conteúdo...")
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            print("Arquivos no ZIP:")
            for f in z.namelist():
                print(f" - {f}")
            
            # Tenta ler o BPA (Ativo)
            target_file = f"dfp_cia_aberta_BPA_con_{ano}.csv"
            if target_file in z.namelist():
                print(f"\nLendo {target_file}...")
                df = pd.read_csv(z.open(target_file), sep=';', encoding='ISO-8859-1')
                print(f"Total de linhas encontradas: {len(df)}")
                
                if len(df) > 0:
                    print("\n=== EMPRESAS COM DADOS DE 2025 DISPONÍVEIS ===\n")
                    empresas = sorted(df['DENOM_CIA'].unique())
                    for emp in empresas:
                        print(f" -> {emp}")
                    print(f"\nTotal: {len(empresas)} empresas encontradas.")
                    petro = df[df['DENOM_CIA'].str.contains('PETROLEO', na=False)]
                    if not petro.empty:
                        print(f"\n✅ PETROBRAS ENCONTRADA EM {ano}!")
                        print(petro[['DENOM_CIA', 'DT_REFER', 'VL_CONTA']].head())
                    else:
                        print("\n❌ PETROBRAS NÃO encontrada nos dados de 2025.")
                else:
                    print("⚠️ O arquivo CSV existe mas está vazio (apenas cabeçalho).")
            else:
                print(f"⚠️ Arquivo {target_file} não encontrado dentro do ZIP.")

    except Exception as e:
        print(f"Erro Crítico: {e}")

if __name__ == "__main__":
    check_2025()
