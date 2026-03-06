import os
import pandas as pd

def load_clean_assets():
    """
    Retorna lista dos ativos filtrados no Screener Técnico.
    Sempre garante a presença do mini índice (WIN) e mini dólar (WDO).
    """
    
    # Ativos filtrados via screener_tecnico.py mais recente
    ativos = [
        'ABEV3', 'ALPA4', 'ASAI3', 'B3SA3', 'BBAS3', 'BEEF3', 'BRAP4', 'BRKM5', 
        'COGN3', 'CSNA3', 'CYRE3', 'DXCO3', 'FLRY3', 'GGBR4', 'GOAU4', 'HAPV3', 
        'IRBR3', 'ITSA4', 'ITUB4', 'JHSF3', 'KLBN11', 'MRVE3', 'MULT3', 'PCAR3', 
        'PETR3', 'PETR4', 'PRIO3', 'QUAL3', 'RAIZ4', 'RECV3', 'RENT3', 'SBSP3', 
        'SLCE3', 'SMTO3', 'SUZB3', 'TIMS3', 'TOTS3', 'UGPA3', 'VALE3', 'VBBR3', 
        'VIVT3', 'WEGE3', 'ALOS3', 'ARML3', 'BOVA11', 'BRSR6', 'CURY3', 'FESA4', 
        'GRND3', 'INTB3', 'KEPL3', 'MOVI3', 'ODPV3'
    ]
    
    # Adicionando WIN e WDO
    if "WINJ26" not in ativos: ativos.insert(0, "WINJ26")
    if "WDOG26" not in ativos: ativos.insert(0, "WDOG26")
    
    return ativos

