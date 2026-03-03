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

    def enviar_mensagem(self, texto, target_chat_id=None, inline_keyboard=None):
        chat = target_chat_id or self.chat_id
        if not self.token or not chat:
            print("❌ Erro: Token ou Chat ID do Telegram não configurados.")
            return False

        reply_markup = {
            "keyboard": [
                [{"text": "📊 Status"}, {"text": "📊 Resumo Diário"}],
                [{"text": "🟢 Ligar Robô"}, {"text": "🔴 Desligar Robô"}],
                [{"text": "💼 Minha Carteira"}, {"text": "📜 Histórico Hoje"}]
            ],
            "resize_keyboard": True
        }

        if inline_keyboard:
            reply_markup = {
                "inline_keyboard": inline_keyboard
            }

        payload = {
            "chat_id": chat,
            "text": texto,
            "parse_mode": "Markdown",
            "reply_markup": reply_markup
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

    def editar_mensagem(self, chat_id, message_id, texto, inline_keyboard=None):
        url = f"https://api.telegram.org/bot{self.token}/editMessageText"
        
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": texto,
            "parse_mode": "Markdown"
        }
        
        if inline_keyboard:
            payload["reply_markup"] = {"inline_keyboard": inline_keyboard}
            
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                return True
            else:
                print(f"⚠️ Falha ao editar mensagem: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Erro de conexão com Telegram ao editar: {e}")
            return False

    def start_listener(self, status_callback=None, toggle_callback=None, summary_callback=None, carteira_callback=None, callback_query_handler=None, teste_callback=None, historico_callback=None):
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
                                
                                if 'callback_query' in update:
                                    cq = update['callback_query']
                                    data_cb = cq.get('data')
                                    cb_msg = cq.get('message', {})
                                    cb_chat_id = cb_msg.get('chat', {}).get('id')
                                    cb_msg_id = cb_msg.get('message_id')
                                    
                                    if callback_query_handler:
                                        callback_query_handler(data_cb, cb_chat_id, cb_msg_id)
                                    
                                    # Answer callback query to stop loading state on the button
                                    cb_id = cq.get('id')
                                    requests.post(f"https://api.telegram.org/bot{self.token}/answerCallbackQuery", json={"callback_query_id": cb_id})
                                    continue
                                
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
                                elif text in ('/status', '📊 Status') and chat_id:
                                    if status_callback:
                                        status_text = status_callback()
                                    else:
                                        status_text = "Estado do sistema não configurado."
                                    self.enviar_mensagem(status_text, target_chat_id=chat_id)
                                    
                                elif text in ('/resumo', '📊 Resumo Diário') and chat_id:
                                    if summary_callback:
                                        summary_text = summary_callback()
                                    else:
                                        summary_text = "Resumo indisponível."
                                    self.enviar_mensagem(summary_text, target_chat_id=chat_id)
                                    
                                elif text == '🟢 Ligar Robô' and chat_id:
                                    if toggle_callback:
                                        res_text = toggle_callback(True)
                                        self.enviar_mensagem(res_text, target_chat_id=chat_id)
                                        
                                elif text == '🔴 Desligar Robô' and chat_id:
                                    if toggle_callback:
                                        res_text = toggle_callback(False)
                                        self.enviar_mensagem(res_text, target_chat_id=chat_id)
                                        
                                elif text in ('/carteira', '💼 Minha Carteira') and chat_id:
                                    if carteira_callback:
                                        cart_text, inline_kb = carteira_callback()
                                    else:
                                        cart_text, inline_kb = "Módulo de carteira indisponível.", None
                                    self.enviar_mensagem(cart_text, target_chat_id=chat_id, inline_keyboard=inline_kb)
                                    
                                elif text == '/teste_compra' and chat_id:
                                    if teste_callback:
                                        teste_callback(chat_id)
                                    else:
                                        self.enviar_mensagem("Comando de teste não configurado.", target_chat_id=chat_id)
                                        
                                elif text in ('/historico', '📜 Histórico Hoje') and chat_id:
                                    if historico_callback:
                                        hist_text = historico_callback()
                                    else:
                                        hist_text = "Módulo de histórico indisponível."
                                    self.enviar_mensagem(hist_text, target_chat_id=chat_id)
                                        
                except requests.exceptions.Timeout:
                    pass  # Timeout esperado do long polling
                except Exception as e:
                    print(f"Erro no listener do Telegram: {e}")
                    time.sleep(5)

        t = threading.Thread(target=poll, daemon=True)
        t.start()
        print("🎧 [Telegram] Listener iniciado para responder a comandos (/start)...")
