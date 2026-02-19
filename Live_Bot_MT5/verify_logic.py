import pandas as pd
import sys
import os

# Adiciona o diretório atual ao path para importar monitor_example
sys.path.append(os.getcwd())

# Mockando a lógica aqui para teste rápido sem depender de imports complexos
LAST_SIGNAL_STATE = 0

def check_crossover(df):
    global LAST_SIGNAL_STATE
    
    if len(df) < 2:
        return None

    current = df.iloc[-1]
    prev = df.iloc[-2]
    
    c_short = current['SMA_Short']
    c_long = current['SMA_Long']
    p_short = prev['SMA_Short']
    p_long = prev['SMA_Long']
    
    signal_text = None
    new_state = LAST_SIGNAL_STATE
    
    # Golden Cross: Curta cruza Longa para CIMA
    # Antes: Curta <= Longa
    # Agora: Curta > Longa
    if p_short <= p_long and c_short > c_long:
        if LAST_SIGNAL_STATE != 1:
            signal_text = "COMPRA (Golden Cross)"
            new_state = 1
            
    # Death Cross: Curta cruza Longa para BAIXO
    # Antes: Curta >= Longa
    # Agora: Curta < Longa
    elif p_short >= p_long and c_short < c_long:
        if LAST_SIGNAL_STATE != -1:
            signal_text = "VENDA (Death Cross)"
            new_state = -1

    if signal_text:
        LAST_SIGNAL_STATE = new_state
        return {
            "sinal": signal_text,
            "preco": current['close']
        }
    
    return None

def run_test():
    global LAST_SIGNAL_STATE
    print("🧪 Iniciando Teste de Lógica de Crossover...")
    
    # Caso 1: Sem cruzamento (Curta abaixo da Longa)
    df1 = pd.DataFrame({
        'close': [10, 10],
        'SMA_Short': [50, 52],
        'SMA_Long': [60, 60]
    })
    res = check_crossover(df1)
    assert res is None, f"Erro Caso 1: Esperado None, recebeu {res}"
    print("✅ Caso 1 (Sem cruzamento) Passou")
    
    # Caso 2: Golden Cross (Curta cruza Longa para cima)
    df2 = pd.DataFrame({
        'close': [10, 11],
        'SMA_Short': [58, 62], # 58 <= 60 (Prev), 62 > 60 (Curr)
        'SMA_Long': [60, 60]
    })
    res = check_crossover(df2)
    assert res is not None and "COMPRA" in res['sinal'], f"Erro Caso 2: Esperado COMPRA, recebeu {res}"
    print("✅ Caso 2 (Golden Cross) Passou")
    
    # Caso 3: Continuação (Curta continua acima da Longa)
    # Estado deve se manter 1, não deve disparar alerta novamente
    df3 = pd.DataFrame({
        'close': [11, 12],
        'SMA_Short': [62, 65],
        'SMA_Long': [60, 60]
    })
    res = check_crossover(df3)
    assert res is None, f"Erro Caso 3: Esperado None (Estado mantido), recebeu {res}"
    print("✅ Caso 3 (Continuação Alta) Passou")
    
    # Caso 4: Death Cross (Curta cruza Longa para baixo)
    df4 = pd.DataFrame({
        'close': [12, 10],
        'SMA_Short': [65, 55], # 65 >= 60 (Prev), 55 < 60 (Curr)
        'SMA_Long': [60, 60]
    })
    res = check_crossover(df4)
    assert res is not None and "VENDA" in res['sinal'], f"Erro Caso 4: Esperado VENDA, recebeu {res}"
    print("✅ Caso 4 (Death Cross) Passou")

    print("\n🎉 Todos os testes de lógica passaram!")

if __name__ == "__main__":
    run_test()
