# bot.py
import os
import logging
from flask import Flask, request
import requests
import json

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получаем токен из переменных окружения
TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROUP_CHAT_ID = os.environ.get("GROUP_CHAT_ID", "-1003006892296")

if not TOKEN:
    raise RuntimeError("❌ TELEGRAM_TOKEN не задан!")

# Создаем Flask приложение
app = Flask(__name__)

@app.route("/")
def home():
    return "🤖 Бот работает! Отправь сообщение в Telegram.", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    """Простой обработчик вебхуков"""
    try:
        # Получаем данные от Telegram
        data = request.get_json()
        logger.info(f"📨 Получен вебхук")
        
        # Проверяем что это сообщение
        if 'message' in data:
            message = data['message']
            chat_id = message['chat']['id']
            user_id = message['from']['id']
            text = message.get('text', '') or message.get('caption', '')
            
            logger.info(f"💬 Сообщение от {user_id}: {text}")
            
            # 1. Отвечаем пользователю
            send_telegram_message(chat_id, "✅ Сообщение получено! Модератор проверит.")
            
            # 2. Пересылаем в группу модерации
            if GROUP_CHAT_ID:
                if 'photo' in message:
                    # Если есть фото - пересылаем фото
                    photo_id = message['photo'][-1]['file_id']
                    send_telegram_photo(GROUP_CHAT_ID, photo_id, f"📸 От {user_id}: {text}")
                else:
                    # Если текст - пересылаем текст
                    send_telegram_message(GROUP_CHAT_ID, f"📝 От {user_id}: {text}")
        
        return 'ok'
        
    except Exception as e:
        logger.error(f"❌ Ошибка в webhook: {e}")
        return 'error', 500

def send_telegram_message(chat_id, text):
    """Отправка текстового сообщения"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        logger.info(f"✅ Сообщение отправлено в {chat_id}")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки сообщения: {e}")

def send_telegram_photo(chat_id, photo_id, caption):
    """Отправка фото"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    payload = {
        'chat_id': chat_id,
        'photo': photo_id,
        'caption': caption
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        logger.info(f"✅ Фото отправлено в {chat_id}")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки фото: {e}")

if __name__ == '__main__':
    logger.info("🚀 Запускаю бота...")
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)