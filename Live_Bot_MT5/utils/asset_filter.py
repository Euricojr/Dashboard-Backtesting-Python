def load_clean_assets():
    """
    Retorna lista curada dos principais ativos da B3 (Elite + Mid Caps).
    Atualizada com Sanepar, CSN e elétricas/saneamento.
    """
    whitelist = [
        # --- FUTUROS E INDICES ---
        "WING26", "WINJ26", "WDOG26", "BOVA11", "SMAL11", "IVVB11",
        
        # --- AÇÕES (LISTA COMPLETA) ---
        "ABEV3", "AESB3", "ALOS3", "ALUP11", "ARZZ3", "ASAI3", "AURE3", "AZUL4",
        "B3SA3", "BBAS3", "BBDC3", "BBDC4", "BBSE3", "BEEF3", "BHIA3", "BPAC11",
        "BRAP4", "BRAV3", "BRFS3", "BRKM5", "CAML3", "CASH3", "CCRO3", "CIEL3",
        "CMIG4", "CMIN3", "COGN3", "CPFE3", "CPLE6", "CRFB3", "CSAN3", "CSNA3",
        "CURY3", "CVCB3", "CXSE3", "CYRE3", "DIRR3", "DXCO3", "ECOR3", "EGIE3",
        "ELET3", "ELET6", "EMBR3", "ENAT3", "ENEV3", "ENGI11", "EQTL3", "EZTC3",
        "FLRY3", "GGBR4", "GGPS3", "GOAU4", "GOLL4", "HAPV3", "HYPE3", "IGTI11",
        "INTB3", "IRBR3", "ITSA4", "ITUB4", "JBSS3", "JHSF3", "KEPL3", "KLBN11",
        "LREN3", "LWSA3", "MATD3", "MGLU3", "MILS3", "MOVI3", "MRFG3", "MRVE3",
        "MULT3", "MYPK3", "NEOE3", "NTCO3", "PCAR3", "PETR3", "PETR4", "PETZ3",
        "POSI3", "PRIO3", "PSSA3", "RADL3", "RAIL3", "RAIZ4", "RANI3", "RAPT4", "RDOR3",
        "RECV3", "RENT3", "ROMI3", "RRRP3", "SANB11", "SAPR11", "SAPR4", "SBSP3",
        "SLCE3", "SMTO3", "SOMA3", "STBP3", "SUZB3", "TAEE11", "TASA4", "TIMS3", "TOTS3",
        "TRPL4", "UGPA3", "UNIP6", "USIM5", "VALE3", "VAMO3", "VBBR3", "VIVA3",
        "VIVT3", "WEGE3", "YDUQ3", "POMO4", "LEVE3"
    ]
    
    # Remove duplicatas e ordena
    return sorted(list(set(whitelist)))
