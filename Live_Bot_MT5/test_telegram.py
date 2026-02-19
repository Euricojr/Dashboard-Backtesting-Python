from utils.telegram_notifier import TelegramNotifier

import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def testar_envio():
    print(f"📡 Tentando enviar mensagem...")
    print(f"🔑 Token (Masked): {TOKEN[:5]}...{TOKEN[-5:] if TOKEN else 'None'}")
    print(f"🆔 Chat ID: {CHAT_ID}")
    
    notifier = TelegramNotifier(token=TOKEN, chat_id=CHAT_ID)
    sucesso = notifier.enviar_mensagem(
        "🔔 **Teste de Notificação FinSense** 🔔\n"
        "Se você recebeu esta mensagem, sua configuração está correta! 🚀"
    )

    if sucesso:
        print("✅ Sucesso! O bot está funcionando.")
    else:
        print("❌ Falha no envio.")

if __name__ == "__main__":
    testar_envio()
