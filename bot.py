# bot.py
import os
import logging
import time
from flask import Flask, request
import requests
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROUP_CHAT_ID = os.environ.get("GROUP_CHAT_ID", "-1003006892296")

# Словарь для отслеживания пользователей
user_sessions = {}

app = Flask(__name__)

@app.route("/")
def home():
    return "🤖 Бот работает! Отправь /start в Telegram.", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    """Обработчик вебхуков с умным меню"""
    try:
        data = request.get_json()
        
        if 'message' in data:
            message = data['message']
            chat_id = message['chat']['id']
            text = message.get('text', '')
            user_name = message['from'].get('first_name', 'Пользователь')
            
            logger.info(f"💬 {user_name}: {text}")
            
            # Обработка команд и меню
            if text.startswith('/'):
                handle_command(chat_id, text, user_name)
            else:
                handle_user_input(chat_id, message, user_name, text)
        
        return 'ok'
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return 'error', 500

def handle_command(chat_id, command, user_name):
    """Обработка команд"""
    if command == '/start':
        send_welcome_message(chat_id, user_name)
    elif command == '/menu':
        send_welcome_message(chat_id, user_name)
    else:
        send_unknown_command(chat_id)

def handle_user_input(chat_id, message, user_name, text):
    """Обработка ввода пользователя"""
    # Если это текст из меню - обрабатываем как выбор пункта
    menu_options = ["📖 Отправить историю", "🔍 Запрос на пробив", "📋 Правила"]
    
    if text in menu_options:
        handle_menu_selection(chat_id, text, user_name)
    else:
        # Если это обычный текст/контент - обрабатываем как контент
        handle_user_content(chat_id, message, user_name, text)

def handle_menu_selection(chat_id, text, user_name):
    """Обработка выбора в меню"""
    if text == "📖 Отправить историю":
        send_story_prompt(chat_id)
    elif text == "🔍 Запрос на пробив":
        send_probe_prompt(chat_id)
    elif text == "📋 Правила":
        send_rules_message(chat_id)

def handle_user_content(chat_id, message, user_name, text):
    """Обработка контента от пользователя (истории/запросы)"""
    
    # Определяем тип контента
    if 'photo' in message:
        content_type = "запрос" if "пробив" in text.lower() else "история"
    else:
        content_type = "запрос" if "пробив" in text.lower() else "история"
    
    # Ответ пользователю
    response_text = f"""
✅ Принято! Ваш {content_type} передан модераторам.

Обычно проверка занимает 5-30 минут.
    """
    
    send_telegram_message(chat_id, response_text)
    
    # Пересылка в группу модерации
    if GROUP_CHAT_ID:
        user_info = f"👤 От: {user_name} (ID: {message['from']['id']})"
        
        if 'photo' in message:
            # Фото
            photo_id = message['photo'][-1]['file_id']
            caption = f"{user_info}\n\n📸 {text}" if text else f"{user_info}\n📸 Прислал фото"
            send_telegram_photo(GROUP_CHAT_ID, photo_id, caption)
        else:
            # Текст
            content_text = f"{user_info}\n\n💬 Сообщение:\n{text}"
            send_telegram_message(GROUP_CHAT_ID, content_text)
    
    # Автоматически возвращаем в меню через 2 секунды
    time.sleep(2)
    send_welcome_message(chat_id, user_name)

def send_welcome_message(chat_id, user_name):
    """Умное приветствие - полный текст только первый раз"""
    user_id = chat_id
    
    if user_id not in user_sessions:
        # Первый раз - показываем полное приветствие
        user_sessions[user_id] = {"first_time": False}
        text = f"""
👋 Добро пожаловать в наше сообщество KURVA_UA, {user_name}!

Здесь ты можешь поделиться своим опытом или узнать больше о интересующей "KURVE.

🎯 Выбери действие:
        """
    else:
        # Не первый раз - показываем только меню
        text = "🎯 Выбери действие:"
    
    keyboard = {
        "keyboard": [
            [{"text": "📖 Отправить историю"}],
            [{"text": "🔍 Запрос на пробив"}],
            [{"text": "📋 Правила"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }
    
    send_telegram_message(chat_id, text, keyboard)

def send_story_prompt(chat_id):
    """Подсказка для отправки истории"""
    story_text = """
💵 Расскажи свою историю о "KURVE"

• Обманула с деньгами?💵
• Украла вещи?😡
• Или просто отлично отработала в твоей машине?😈

Опиши ситуацию подробно - опубликуем анонимно.
    """
    send_telegram_message(chat_id, story_text)

def send_probe_prompt(chat_id):
    """Подсказка для запроса на пробив"""
    probe_text = """
😈 Узнай правду о KURVE

Пришли:
• Ссылку на соцсети
• Или фото с сайта знакомств
• Текстовый запрос - что тебя интересует!?

Наше сообщество проверит - возможно, кто-то уже имел с ней дело и знает все "внутренности".
    """
    send_telegram_message(chat_id, probe_text)

def send_rules_message(chat_id):
    """Правила сообщества"""
    rules_text = """
⚖️ Правила сообщества

Можно высказываться в любой форме, но оставайся МУЖЧИНОЙ!

⚠️ ВАЖНО: 
Клевета без доказательств недопустима. 
При опровержении информации твой аккаунт будет раскрыт пострадавшей стороне.

Имей это ввиду!
    """
    send_telegram_message(chat_id, rules_text)

def send_unknown_command(chat_id):
    """Неизвестная команда"""
    send_telegram_message(
        chat_id,
        "❌ Неизвестная команда.\n\nИспользуй /start для начала работы или /menu для возврата в меню."
    )

def send_telegram_message(chat_id, text, reply_markup=None):
    """Универсальная отправка сообщений"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info(f"✅ Сообщение отправлено в {chat_id}")
        else:
            logger.error(f"❌ Ошибка отправки: {response.text}")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки: {e}")

def send_telegram_photo(chat_id, photo_id, caption):
    """Отправка фото"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    payload = {
        'chat_id': chat_id,
        'photo': photo_id,
        'caption': caption,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info(f"✅ Фото отправлено в {chat_id}")
        else:
            logger.error(f"❌ Ошибка отправки фото: {response.text}")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки фото: {e}")

if __name__ == '__main__':
    logger.info("🚀 Бот с умным меню запущен")
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
