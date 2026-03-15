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
        self.user_states = {}  # {chat_id: {'state': '...', 'sl': ..., 'tp': ...}}
        self.session = requests.Session() # Reuse connection for performance

    def enviar_mensagem(self, texto, target_chat_id=None, inline_keyboard=None):
        chat = target_chat_id or self.chat_id
        if not self.token or not chat:
            print("❌ Erro: Token ou Chat ID do Telegram não configurados.")
            return False

        reply_markup = {
            "keyboard": [
                [{"text": "📊 Status"}, {"text": "📊 Resumo Diário"}],
                [{"text": "🟢 Ligar Robô"}, {"text": "🔴 Desligar Robô"}],
                [{"text": "💼 Minha Carteira"}, {"text": "📜 Histórico Hoje"}],
                [{"text": "🤖 Ligar/Desligar Scalper"}, {"text": "📊 Stats Scalper"}]
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
            response = self.session.post(self.base_url, json=payload, timeout=10)
            if response.status_code == 200:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Notificação enviada com sucesso!")
                return True
            else:
                print(f"⚠️ Falha ao enviar notificação: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Erro de conexão com Telegram: {e}")
            return False

    def enviar_foto(self, photo_stream, caption, target_chat_id=None, inline_keyboard=None):
        import json
        chat = target_chat_id or self.chat_id
        if not self.token or not chat:
            print("❌ Erro: Token ou Chat ID configurados.")
            return False

        url = f"https://api.telegram.org/bot{self.token}/sendPhoto"
        
        reply_markup = {
            "keyboard": [
                [{"text": "📊 Status"}, {"text": "📊 Resumo Diário"}],
                [{"text": "🟢 Ligar Robô"}, {"text": "🔴 Desligar Robô"}],
                [{"text": "💼 Minha Carteira"}, {"text": "📜 Histórico Hoje"}],
                [{"text": "🤖 Ligar/Desligar Scalper"}, {"text": "📊 Stats Scalper"}]
            ],
            "resize_keyboard": True
        }

        if inline_keyboard:
            reply_markup = {
                "inline_keyboard": inline_keyboard
            }

        data = {
            "chat_id": chat,
            "caption": caption,
            "parse_mode": "Markdown",
            "reply_markup": json.dumps(reply_markup)
        }
        
        photo_stream.seek(0)
        files = {
            "photo": ("grafico.png", photo_stream, "image/png")
        }

        try:
            response = self.session.post(url, data=data, files=files, timeout=15)
            if response.status_code == 200:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Foto enviada com sucesso!")
                return True
            else:
                print(f"⚠️ Falha ao enviar foto: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Erro de conexão com Telegram ao enviar foto: {e}")
            return False

    def editar_mensagem(self, chat_id, message_id, texto, inline_keyboard=None):
        url_text = f"https://api.telegram.org/bot{self.token}/editMessageText"
        url_caption = f"https://api.telegram.org/bot{self.token}/editMessageCaption"
        
        payload_text = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": texto,
            "parse_mode": "Markdown"
        }
        
        payload_caption = {
            "chat_id": chat_id,
            "message_id": message_id,
            "caption": texto,
            "parse_mode": "Markdown"
        }
        
        if inline_keyboard:
            payload_text["reply_markup"] = {"inline_keyboard": inline_keyboard}
            payload_caption["reply_markup"] = {"inline_keyboard": inline_keyboard}
            
        try:
            # Tenta editar como texto primeiro
            response = self.session.post(url_text, json=payload_text, timeout=10)
            if response.status_code == 200:
                return True
            else:
                resp_json = response.json()
                # Se o erro for de que não há texto para editar, significa que é uma foto/mídia com caption
                description = resp_json.get("description", "")
                if description == "Bad Request: there is no text in the message to edit":
                    response_caption = self.session.post(url_caption, json=payload_caption, timeout=10)
                    if response_caption.status_code == 200:
                        return True
                    else:
                        print(f"⚠️ Falha ao editar caption: {response_caption.text}")
                        return False
                elif "message is not modified" in description:
                    # Se a mensagem já é igual à que queremos colocar, ignoramos o erro (comum em botões clicados rápido ou instâncias duplas)
                    return True
                else:
                    print(f"⚠️ Falha ao editar mensagem: {response.text}")
                    return False
        except Exception as e:
            print(f"❌ Erro de conexão com Telegram ao editar: {e}")
            return False

    def start_listener(self, **callbacks):
        """Inicia uma thread para ouvir comandos do Telegram (como /start)"""
        if not self.token:
            print("❌ Listener do Telegram cancelado: TOKEN não encontrado.")
            return

        def handle_update(update):
            """Processa um único update em uma thread separada"""
            try:
                if 'callback_query' in update:
                    cq = update['callback_query']
                    data_cb = cq.get('data')
                    cb_msg = cq.get('message', {})
                    cb_chat_id = cb_msg.get('chat', {}).get('id')
                    cb_msg_id = cb_msg.get('message_id')
                    
                    # Answer callback query IMEDATAMENTE para remover o loading do botão
                    cb_id = cq.get('id')
                    self.session.post(f"https://api.telegram.org/bot{self.token}/answerCallbackQuery", json={"callback_query_id": cb_id})

                    if callbacks.get('callback_query_handler'):
                        callbacks['callback_query_handler'](data_cb, cb_chat_id, cb_msg_id)
                    return

                msg = update.get('message', {})
                text = msg.get('text', '')
                chat_id = msg.get('chat', {}).get('id')
                if not chat_id: return

                if text == '/start':
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
                elif text in ('/status', '📊 Status'):
                    status_cb = callbacks.get('status_callback')
                    self.enviar_mensagem(status_cb() if status_cb else "Estado do sistema não configurado.", target_chat_id=chat_id)
                    
                elif text in ('/resumo', '📊 Resumo Diário'):
                    sum_cb = callbacks.get('summary_callback')
                    self.enviar_mensagem(sum_cb() if sum_cb else "Resumo indisponível.", target_chat_id=chat_id)
                    
                elif text == '🟢 Ligar Robô':
                    tog_cb = callbacks.get('toggle_callback')
                    if tog_cb: self.enviar_mensagem(tog_cb(True), target_chat_id=chat_id)
                        
                elif text == '🔴 Desligar Robô':
                    tog_cb = callbacks.get('toggle_callback')
                    if tog_cb: self.enviar_mensagem(tog_cb(False), target_chat_id=chat_id)
                        
                elif text in ('/carteira', '💼 Minha Carteira'):
                    cart_cb = callbacks.get('carteira_callback')
                    if cart_cb:
                        cart_text, inline_kb = cart_cb()
                        self.enviar_mensagem(cart_text, target_chat_id=chat_id, inline_keyboard=inline_kb)
                    
                elif text == '/teste_compra':
                    tst_cb = callbacks.get('teste_callback')
                    if tst_cb: tst_cb(chat_id)
                        
                elif text in ('/historico', '📜 Histórico Hoje'):
                    hist_cb = callbacks.get('historico_callback')
                    if hist_cb: self.enviar_mensagem(hist_cb(), target_chat_id=chat_id)
                        
                elif text == '🤖 Ligar/Desligar Scalper':
                    ts_cb = callbacks.get('toggle_scalper_cb')
                    gs_cb = callbacks.get('get_scalper_state_cb')
                    if ts_cb and gs_cb:
                        state = gs_cb()
                        if state.get("status") == "ON":
                            self.enviar_mensagem(ts_cb(turn_on=False), target_chat_id=chat_id)
                        else:
                            self.user_states[chat_id] = {'state': 'WAITING_TIMEFRAME'}
                            inline_kb = [[{"text": "M1", "callback_data": "tf_M1"}, {"text": "M5", "callback_data": "tf_M5"}], [{"text": "❌ Cancelar", "callback_data": "cancel"}]]
                            self.enviar_mensagem("⏱️ *Qual o Timeframe da operação?*", target_chat_id=chat_id, inline_keyboard=inline_kb)
                    
                elif text == '📊 Stats Scalper':
                    sts_cb = callbacks.get('stats_scalper_cb')
                    if sts_cb: self.enviar_mensagem(sts_cb(), target_chat_id=chat_id)
                        
                # Lógica da Máquina de Estados
                elif chat_id in self.user_states:
                    u_state = self.user_states[chat_id]
                    if u_state['state'] == 'WAITING_SL':
                        try:
                            sl_val = float(text.replace(',', '.'))
                            u_state.update({'sl': sl_val, 'state': 'WAITING_TP'})
                            self.enviar_mensagem("✅ SL definido. Agora, qual o *Take Profit* (em pontos)?", target_chat_id=chat_id)
                        except ValueError:
                            self.enviar_mensagem("⚠️ Valor inválido. Digite apenas números.", target_chat_id=chat_id)
                    elif u_state['state'] == 'WAITING_TP':
                        try:
                            tp_val = float(text.replace(',', '.'))
                            ts_cb = callbacks.get('toggle_scalper_cb')
                            if ts_cb:
                                self.enviar_mensagem(ts_cb(turn_on=True, sl=u_state['sl'], tp=tp_val, timeframe=u_state.get('timeframe', 'M5')), target_chat_id=chat_id)
                            del self.user_states[chat_id]
                        except ValueError:
                            self.enviar_mensagem("⚠️ Valor inválido. Digite apenas números.", target_chat_id=chat_id)
            except Exception as e:
                print(f"❌ Erro ao processar update: {e}")

        def poll():
            offset = None
            url = f"https://api.telegram.org/bot{self.token}/getUpdates"
            while True:
                try:
                    # Long Polling: timeout de 20s para resposta quase instantânea sem queimar CPU
                    params = {"timeout": 20, "offset": offset}
                    resp = self.session.get(url, params=params, timeout=25)
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get('ok'):
                            for update in data['result']:
                                offset = update['update_id'] + 1
                                # Despachar cada update para uma thread separada
                                threading.Thread(target=handle_update, args=(update,), daemon=True).start()
                except Exception as e:
                    print(f"⚠️ Erro no polling: {e}")
                    time.sleep(2)
                time.sleep(0.1) # Respiro mínimo

        threading.Thread(target=poll, daemon=True).start()
        print("🎧 [Telegram] Listener otimizado iniciado (Multi-threading + Long Polling)...")
