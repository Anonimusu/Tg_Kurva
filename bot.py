# bot.py
import os
import threading
from flask import Flask
import logging
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получаем токен и ID чата из переменных окружения
TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROUP_CHAT_ID = os.environ.get("GROUP_CHAT_ID")

if not TOKEN:
    logger.error("TELEGRAM_TOKEN не задан!")
    raise RuntimeError("TELEGRAM_TOKEN не задан")

# Создаём Flask приложение
flask_app = Flask(__name__)

@flask_app.route("/")
def index():
    return "Bot is alive!", 200

@flask_app.route("/health")
def health():
    return "OK", 200

# Функция обработки сообщений
def handle_message(update: Update, context: CallbackContext):
    if update.message is None:
        return

    message_text = update.message.text or update.message.caption or "Сообщение без текста"
    user_id = update.message.from_user.id

    # Пересылка в группу модерации
    if GROUP_CHAT_ID:
        try:
            if update.message.photo:
                photo = update.message.photo[-1]
                context.bot.send_photo(
                    chat_id=GROUP_CHAT_ID,
                    photo=photo.file_id,
                    caption=f"Фото от пользователя {user_id}: {message_text}"
                )
            else:
                context.bot.send_message(
                    chat_id=GROUP_CHAT_ID,
                    text=f"Сообщение от пользователя {user_id}: {message_text}"
                )
        except Exception as e:
            logger.error(f"Ошибка при пересылке: {e}")

    # Ответ пользователю
    try:
        update.message.reply_text("Сообщение получено! Админ проверит и опубликует.")
    except Exception as e:
        logger.error(f"Ошибка при ответе: {e}")

# Функция для запуска бота
def start_bot():
    """Запускает Telegram бота в отдельном потоке"""
    try:
        updater = Updater(TOKEN)
        dispatcher = updater.dispatcher
        
        # Добавляем обработчик сообщений
        dispatcher.add_handler(MessageHandler(Filters.all & ~Filters.command, handle_message))
        
        logger.info("Запуск Telegram бота...")
        updater.start_polling()
        updater.idle()
    except Exception as e:
        logger.error(f"Ошибка бота: {e}")

# Запуск при импорте
def create_app():
    """Функция для запуска бота (нужна для Render)"""
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    return flask_app

# Для локального тестирования
if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)