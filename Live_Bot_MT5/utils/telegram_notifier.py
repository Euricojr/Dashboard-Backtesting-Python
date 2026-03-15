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
            response = requests.post(url, data=data, files=files, timeout=15)
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
            response = requests.post(url_text, json=payload_text, timeout=10)
            if response.status_code == 200:
                return True
            else:
                resp_json = response.json()
                # Se o erro for de que não há texto para editar, significa que é uma foto/mídia com caption
                if resp_json.get("description") == "Bad Request: there is no text in the message to edit":
                    response_caption = requests.post(url_caption, json=payload_caption, timeout=10)
                    if response_caption.status_code == 200:
                        return True
                    else:
                        print(f"⚠️ Falha ao editar caption: {response_caption.text}")
                        return False
                else:
                    print(f"⚠️ Falha ao editar mensagem: {response.text}")
                    return False
        except Exception as e:
            print(f"❌ Erro de conexão com Telegram ao editar: {e}")
            return False

    def start_listener(self, status_callback=None, toggle_callback=None, summary_callback=None, 
                       carteira_callback=None, callback_query_handler=None, teste_callback=None, 
                       historico_callback=None, toggle_scalper_cb=None, stats_scalper_cb=None,
                       get_scalper_state_cb=None):
        """Inicia uma thread para ouvir comandos do Telegram (como /start)"""
        if not self.token:
            print("❌ Listener do Telegram cancelado: TOKEN não encontrado.")
            return
            
        def poll():
            offset = None
            url = f"https://api.telegram.org/bot{self.token}/getUpdates"
            while True:
                try:
                    # Timeout curto para nao prender o GIL e travar o terminal (Bug do Windows)
                    params = {"timeout": 5, "offset": offset}
                    resp = requests.get(url, params=params, timeout=10)
                    
                    if resp.status_code == 200:
                        try:
                            data = resp.json()
                        except Exception as json_err:
                            print(f"⚠️ [Telegram] Falha ao decodificar JSON do Telegram: {json_err}")
                            time.sleep(1)
                            continue
                            
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
                                        
                                elif text == '🤖 Ligar/Desligar Scalper' and chat_id:
                                    if toggle_scalper_cb and get_scalper_state_cb:
                                        state = get_scalper_state_cb()
                                        if state.get("status") == "ON":
                                            # Se está ligado, apenas desliga direto
                                            res_text = toggle_scalper_cb(turn_on=False)
                                            self.enviar_mensagem(res_text, target_chat_id=chat_id)
                                        else:
                                            # Se está desligado, entra na máquina de estados
                                            self.user_states[chat_id] = {'state': 'WAITING_SL'}
                                            self.enviar_mensagem("🎯 *Configuração do Scalper*\n\nQual o *Stop Loss* (em pontos)?\n(Ex: 100)", target_chat_id=chat_id)
                                    
                                elif text == '📊 Stats Scalper' and chat_id:
                                    if stats_scalper_cb:
                                        res_text = stats_scalper_cb()
                                        self.enviar_mensagem(res_text, target_chat_id=chat_id)
                                        
                                # Lógica da Máquina de Estados para mensagens de texto genéricas
                                else:
                                    if chat_id in self.user_states:
                                        u_state = self.user_states[chat_id]
                                        
                                        if u_state['state'] == 'WAITING_SL':
                                            try:
                                                sl_val = float(text.replace(',', '.'))
                                                u_state['sl'] = sl_val
                                                u_state['state'] = 'WAITING_TP'
                                                self.enviar_mensagem("✅ SL definido. Agora, qual o *Take Profit* (em pontos)?\n(Ex: 200)", target_chat_id=chat_id)
                                            except ValueError:
                                                self.enviar_mensagem("⚠️ Valor inválido. Digite apenas números para o Stop Loss.", target_chat_id=chat_id)
                                                
                                        elif u_state['state'] == 'WAITING_TP':
                                            try:
                                                tp_val = float(text.replace(',', '.'))
                                                sl_val = u_state['sl']
                                                
                                                # Finaliza e liga o robô
                                                if toggle_scalper_cb:
                                                    res_text = toggle_scalper_cb(turn_on=True, sl=sl_val, tp=tp_val)
                                                    self.enviar_mensagem(res_text, target_chat_id=chat_id)
                                                
                                                # Limpa estado
                                                del self.user_states[chat_id]
                                            except ValueError:
                                                self.enviar_mensagem("⚠️ Valor inválido. Digite apenas números para o Take Profit.", target_chat_id=chat_id)
                                        
                except requests.exceptions.Timeout:
                    pass  # Timeout esperado
                except requests.exceptions.ReadTimeout:
                    pass
                except Exception as e:
                    print(f"Erro no listener do Telegram: {e}")
                    time.sleep(2)
                
                # Respiro do loop para não torrar CPU
                time.sleep(1)

        t = threading.Thread(target=poll, daemon=True)
        t.start()
        print("🎧 [Telegram] Listener iniciado para responder a comandos (/start)...")
