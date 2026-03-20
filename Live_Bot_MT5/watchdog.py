import os
import time
import psutil
import subprocess
import telebot
from dotenv import load_dotenv

# Carrega as variáveis de ambiente (como o WATCHDOG_TOKEN)
load_dotenv()

# Lê o token do bot de emergência
WATCHDOG_TOKEN = os.getenv('WATCHDOG_TOKEN')

if not WATCHDOG_TOKEN:
    print("Erro: A variável de ambiente WATCHDOG_TOKEN não foi definida.")
    print("Por favor, adicione WATCHDOG_TOKEN no seu arquivo .env")
    exit(1)

# Inicializa o bot do watchdog
bot = telebot.TeleBot(WATCHDOG_TOKEN)

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def execute_kill_switch(chat_id):
    try:
        # Avisa que iniciou o protocolo
        bot.send_message(chat_id, "🚨 Falha detectada. Iniciando protocolo de emergência (Kill Switch)...")
        
        killed_any = False
        
        # Itera sobre todos os processos abertos no Windows
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                name = proc.info.get('name')
                cmdline = proc.info.get('cmdline')
                
                # Verifica se é executável Python
                if name and name.lower() in ('python.exe', 'pythonw.exe') and cmdline:
                    # Verifica se o script alvo (app.py ou scalper_win.py) está na linha de comando
                    if any('app.py' in cmd for cmd in cmdline) or any('scalper_win.py' in cmd for cmd in cmdline):
                        print(f"Matando processo {proc.info['pid']} - Cmd: {cmdline}")
                        proc.kill() # Termina o processo à força
                        killed_any = True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
                
        if killed_any:
            # Dá o sleep de 3 segundos
            time.sleep(3)
            
            import sys
            
            # Obtém a pasta onde está este script (Live_Bot_MT5) para referenciar o app.py corretamente
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Reinicia o sistema principal (app.py) silenciosamente no mesmo terminal
            subprocess.Popen([sys.executable, 'app.py'], cwd=script_dir)
            
            # Envia a mensagem final de ressurreição
            bot.send_message(chat_id, "✅ Sistema principal e submódulos degolados com sucesso! O Scalper foi reiniciado e está de volta à vida.")
        else:
            bot.send_message(chat_id, "⚠️ Nenhum processo do robô (`app.py` ou `scalper_win.py`) foi encontrado rodando.")
            
    except Exception as e:
        error_msg = f"❌ Erro ao executar o Kill Switch: {e}"
        print(error_msg)
        bot.send_message(chat_id, error_msg)

@bot.message_handler(commands=['start', 'menu'])
def handle_start(message):
    markup = InlineKeyboardMarkup()
    btn_emergency = InlineKeyboardButton("🚨 Acionar Kill Switch", callback_data="btn_emergencia")
    markup.add(btn_emergency)
    bot.send_message(message.chat.id, "🛡️ Painel do Watchdog.\n\nUse o botão abaixo para reiniciar o sistema principal em caso de travamento:", reply_markup=markup)

@bot.message_handler(commands=['emergencia'])
def handle_emergencia(message):
    execute_kill_switch(message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == "btn_emergencia")
def callback_emergencia(call):
    bot.answer_callback_query(call.id, "Iniciando protocolo...")
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None) # remove o botão clicado
    execute_kill_switch(call.message.chat.id)

if __name__ == '__main__':
    print("🛡️ Watchdog está ON e vigiando! Aguardando o comando /emergencia no Telegram...")
    
    # 4. Blindagem: Loop eterno para o bot ser imortal contra quedas de internet
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"⚠️ Erro de rede ou queda de conexão no Watchdog: {e}. Reconectando em 5 segundos...")
            time.sleep(5)
