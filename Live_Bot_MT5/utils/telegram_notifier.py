import requests
import os
from datetime import datetime

class TelegramNotifier:
    def __init__(self, token=None, chat_id=None):
        self.token = token or os.getenv("TELEGRAM_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.base_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    def enviar_mensagem(self, texto):
        if not self.token or not self.chat_id:
            print("❌ Erro: Token ou Chat ID do Telegram não configurados.")
            return False

        payload = {
            "chat_id": self.chat_id,
            "text": texto,
            "parse_mode": "Markdown"
        }

        try:
            response = requests.post(self.base_url, json=payload, timeout=10)
            if response.status_code == 200:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Notificação enviada com sucesso!")
                return True
            else:
                print(f"⚠️ Falha ao enviar notificação: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Erro de conexão com Telegram: {e}")
            return False
