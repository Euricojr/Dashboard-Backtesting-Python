import MetaTrader5 as mt5
import pandas as pd
import os

# Conecta
if not mt5.initialize():
    print("Erro ao conectar no MT5")
    quit()

print("🔍 Varrendo todos os ativos da corretora... aguarde...")

# Pega TODOS os símbolos disponíveis no servidor do BTG
# (Isso pode demorar uns segundos pois são milhares)
symbols = mt5.symbols_get()

# Transforma em lista de dicionários para facilitar
data = []
for s in symbols:
    data.append({
        "Symbol": s.name,
        "Path": s.path,        # O caminho da pasta (Ex: Bovespa\A vista\Petrobras)
        "Description": s.description
    })

# Cria DataFrame
df = pd.DataFrame(data)

mt5.shutdown()

print(f"\n✅ Encontrados {len(df)} ativos totais!\n")

# --- RESUMO POR CATEGORIA ---

# --- RESUMO POR CATEGORIA ---
summary_lines = []
summary_lines.append("--- O QUE TEM DENTRO DO SEU MT5 ---")

if not df.empty:
    # Agrupa pelo caminho (Path)
    counts = df['Path'].apply(lambda x: x.split('\\')[0] if isinstance(x, str) else str(x)).value_counts().to_string()
    summary_lines.append(counts)

    # --- EXEMPLOS ---
    summary_lines.append("\n--- EXEMPLOS DE AÇÕES (Top 5) ---")
    acoes = df[df['Path'].str.contains('Vista|Cash|Bovespa', case=False, na=False)]
    if not acoes.empty:
        summary_lines.append(acoes[['Symbol', 'Description']].head().to_string())
    else:
        summary_lines.append("Nenhuma ação encontrada com filtro padrão.")

    summary_lines.append("\n--- EXEMPLOS DE FUTUROS (Top 5) ---")
    futuros = df[df['Path'].str.contains('Futur|BMF', case=False, na=False)]
    if not futuros.empty:
        summary_lines.append(futuros[['Symbol', 'Description']].head().to_string())
    else:
        summary_lines.append("Nenhum futuro encontrado com filtro padrão.")

    # Salvar Excel/CSV
    output_file = "lista_completa_ativos_btg.xlsx"
    try:
        df.to_excel(output_file, index=False)
        summary_lines.append(f"\n📁 Lista completa salva em '{os.path.abspath(output_file)}'")
    except ImportError:
        csv_file = "lista_completa_ativos_btg.csv"
        df.to_csv(csv_file, index=False)
        summary_lines.append(f"\n⚠️ openpyxl não instalado. Salvo em CSV: '{os.path.abspath(csv_file)}'")
    except Exception as e:
        summary_lines.append(f"\n❌ Erro ao salvar arquivo: {e}")

else:
    summary_lines.append("Nenhum ativo encontrado.")

# Imprimir e Salvar Resumo
summary_text = "\n".join(summary_lines)
print(summary_text)

with open("resumo_ativos.txt", "w", encoding="utf-8") as f:
    f.write(summary_text)

print(f"\n📄 Resumo salvo em 'resumo_ativos.txt'")
