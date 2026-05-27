import os
import sys
import time
import psutil
import subprocess
import telebot
from dotenv import load_dotenv

# Reconfigura o encoding da saída no Windows para evitar erros com emojis
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass


# Carrega as variáveis de ambiente (como o WATCHDOG_TOKEN)
load_dotenv()

# Lê o token do bot de emergência
WATCHDOG_TOKEN = os.getenv('WATCHDOG_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

if not WATCHDOG_TOKEN:
    print("Erro: A variável de ambiente WATCHDOG_TOKEN não foi definida.")
    print("Por favor, adicione WATCHDOG_TOKEN no seu arquivo .env")
    exit(1)

# Inicializa o bot do watchdog
bot = telebot.TeleBot(WATCHDOG_TOKEN)

from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def kill_processes():
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
    return killed_any

def check_is_running():
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            name = proc.info.get('name')
            cmdline = proc.info.get('cmdline')
            if name and name.lower() in ('python.exe', 'pythonw.exe') and cmdline:
                if any('app.py' in cmd for cmd in cmdline) or any('scalper_win.py' in cmd for cmd in cmdline):
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False

@bot.message_handler(commands=['ligar'])
def handle_ligar(message):
    execute_ligar(message.chat.id)

def execute_ligar(chat_id):
    try:
        if check_is_running():
            bot.send_message(chat_id, "⚠️ O sistema já está rodando. Use /reiniciar se quiser reiniciar.")
            return
            
        bot.send_message(chat_id, "🟢 Ligando o sistema principal...")
        
        import sys
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Tenta localizar o python do .venv no diretório pai para garantir execução correta
        parent_dir = os.path.dirname(script_dir)
        venv_python = os.path.join(parent_dir, '.venv', 'Scripts', 'python.exe')
        python_exe = venv_python if os.path.exists(venv_python) else sys.executable
        # Força o uso do python.exe correspondente para garantir que rode em nova janela no Windows
        subprocess.Popen([python_exe, 'app.py'], cwd=script_dir, creationflags=subprocess.CREATE_NEW_CONSOLE)
        bot.send_message(chat_id, "✅ Sistema ligado e operando!")
    except Exception as e:
        error_msg = f"❌ Erro ao ligar o sistema: {e}"
        print(error_msg)
        bot.send_message(chat_id, error_msg)

@bot.message_handler(commands=['desligar'])
def handle_desligar(message):
    chat_id = message.chat.id
    execute_desligar(chat_id)

def execute_desligar(chat_id):
    try:
        bot.send_message(chat_id, "🛑 Desligando o sistema principal...")
        killed = kill_processes()
        
        if killed:
            bot.send_message(chat_id, "✅ Sistema principal desligado com sucesso. O robô está inativo.")
        else:
            bot.send_message(chat_id, "⚠️ Nenhum processo do robô foi encontrado rodando.")
    except Exception as e:
        error_msg = f"❌ Erro ao desligar o sistema: {e}"
        print(error_msg)
        bot.send_message(chat_id, error_msg)

@bot.message_handler(commands=['reiniciar'])
def handle_reiniciar(message):
    chat_id = message.chat.id
    execute_reiniciar(chat_id)

def execute_reiniciar(chat_id):
    try:
        bot.send_message(chat_id, "🔄 Reiniciando o sistema...")
        kill_processes()
        
        time.sleep(3)
        import sys
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Tenta localizar o python do .venv no diretório pai para garantir execução correta
        parent_dir = os.path.dirname(script_dir)
        venv_python = os.path.join(parent_dir, '.venv', 'Scripts', 'python.exe')
        python_exe = venv_python if os.path.exists(venv_python) else sys.executable
        subprocess.Popen([python_exe, 'app.py'], cwd=script_dir, creationflags=subprocess.CREATE_NEW_CONSOLE)
        bot.send_message(chat_id, "✅ Sistema reiniciado e operando!")
    except Exception as e:
        error_msg = f"❌ Erro ao reiniciar o sistema: {e}"
        print(error_msg)
        bot.send_message(chat_id, error_msg)

# --- NOVO MENU INTERATIVO ---

def create_panel_markup():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🔄 Reiniciar Robô", callback_data='btn_reiniciar'))
    markup.row(InlineKeyboardButton("🛑 Desligar Robô", callback_data='btn_desligar'))
    markup.row(InlineKeyboardButton("💻 Desligar PC Físico", callback_data='btn_desligar_pc'))
    return markup

@bot.message_handler(commands=['painel'])
def handle_painel(message):
    bot.send_message(
        message.chat.id, 
        "🎛️ **Painel de Emergência do Scalper**", 
        parse_mode="Markdown", 
        reply_markup=create_panel_markup()
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "btn_reiniciar":
        bot.answer_callback_query(call.id, "Reiniciando robô...")
        execute_reiniciar(call.message.chat.id)
    elif call.data == "btn_desligar":
        bot.answer_callback_query(call.id, "Desligando robô...")
        execute_desligar(call.message.chat.id)
    elif call.data == "btn_desligar_pc":
        bot.answer_callback_query(call.id, "Desligando PC...")
        bot.send_message(call.message.chat.id, "⚠️ ALERTA: Desligando o Windows em 10 segundos...")
        os.system("shutdown /s /t 10")

@bot.message_handler(commands=['start', 'menu'])
def handle_start(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton("🟢 Ligar"), KeyboardButton("🔄 Reiniciar"))
    markup.row(KeyboardButton("🛑 Desligar"), KeyboardButton("💻 Desligar PC"))
    bot.send_message(message.chat.id, "🛡️ Painel do Watchdog.\n\nEscolha uma das opções no teclado abaixo:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in ["🟢 Ligar", "🔄 Reiniciar", "🛑 Desligar", "💻 Desligar PC"])
def handle_teclado(message):
    chat_id = message.chat.id
    if message.text == "🟢 Ligar":
        execute_ligar(chat_id)
    elif message.text == "🔄 Reiniciar":
        execute_reiniciar(chat_id)
    elif message.text == "🛑 Desligar":
        execute_desligar(chat_id)
    elif message.text == "💻 Desligar PC":
        bot.send_message(chat_id, "⚠️ **ALERTA: Desligando o Windows em 10 segundos...**", parse_mode="Markdown")
        os.system("shutdown /s /t 10")

if __name__ == '__main__':
    print("🛡️ Watchdog está ON e vigiando! Envie /start no Telegram para acessar as opções.")
    
    # Enviar mensagem inicial pro Admin
    if TELEGRAM_CHAT_ID:
        try:
            markup = ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row(KeyboardButton("🟢 Ligar"), KeyboardButton("🔄 Reiniciar"))
            markup.row(KeyboardButton("🛑 Desligar"), KeyboardButton("💻 Desligar PC"))
            bot.send_message(TELEGRAM_CHAT_ID, "🛡️ **Watchdog Iniciado e Online!**\n\nUse o teclado abaixo fixado no seu chat para controlar o robô de forma rápida e segura.", reply_markup=markup, parse_mode="Markdown")
        except Exception as e:
            print(f"Erro ao enviar mensagem inicial: {e}")
    
    # 4. Blindagem: Loop eterno para o bot ser imortal contra quedas de internet
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"⚠️ Erro de rede ou queda de conexão no Watchdog: {e}. Reconectando em 5 segundos...")
            time.sleep(5)
