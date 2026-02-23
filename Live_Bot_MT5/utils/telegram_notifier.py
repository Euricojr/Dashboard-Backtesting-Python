import requests
import os
import threading
import time
from datetime import datetime

class TelegramNotifier:
    def __init__(self, token=None, chat_id=None):
        self.token = token or os.getenv("TELEGRAM_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.base_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    def enviar_mensagem(self, texto, target_chat_id=None):
        chat = target_chat_id or self.chat_id
        if not self.token or not chat:
            print("❌ Erro: Token ou Chat ID do Telegram não configurados.")
            return False

        payload = {
            "chat_id": chat,
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

    def start_listener(self):
        """Inicia uma thread para ouvir comandos do Telegram (como /start)"""
        if not self.token:
            print("❌ Listener do Telegram cancelado: TOKEN não encontrado.")
            return
            
        def poll():
            offset = None
            url = f"https://api.telegram.org/bot{self.token}/getUpdates"
            while True:
                try:
                    params = {"timeout": 30, "offset": offset}
                    # O timeout do request deve ser um pouco maior que o timeout do Telegram
                    resp = requests.get(url, params=params, timeout=40)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get('ok'):
                            for update in data['result']:
                                offset = update['update_id'] + 1
                                msg = update.get('message', {})
                                text = msg.get('text', '')
                                chat_id = msg.get('chat', {}).get('id')
                                
                                if text == '/start' and chat_id:
                                    welcome_text = (
                                        "👋 *Olá! Bem-vindo ao Live Bot do Finsense!* 🚀\n\n"
                                        "Eu sou o seu robô de monitoramento de ativos do mercado financeiro.\n"
                                        "Sempre que você LIGAR o robô no painel web, estarei acompanhando os ativos e te notificarei imediatamente "
                                        "quando ocorrer um cruzamento das médias móveis (SMA).\n\n"
                                        "Sinais que você receberá:\n"
                                        "🟢 *COMPRA* (Golden Cross)\n"
                                        "🔴 *VENDA* (Death Cross)\n\n"
                                        "Para gerenciar, basta acessar o painel pelo navegador."
                                    )
                                    self.enviar_mensagem(welcome_text, target_chat_id=chat_id)
                except requests.exceptions.Timeout:
                    pass  # Timeout esperado do long polling
                except Exception as e:
                    print(f"Erro no listener do Telegram: {e}")
                    time.sleep(5)

        t = threading.Thread(target=poll, daemon=True)
        t.start()
        print("🎧 [Telegram] Listener iniciado para responder a comandos (/start)...")
