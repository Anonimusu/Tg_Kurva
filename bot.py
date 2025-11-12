# bot.py
import os
import threading
import asyncio
import logging
from flask import Flask
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

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
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return

    message_text = update.message.text or update.message.caption or "Сообщение без текста"
    user_id = update.message.from_user.id

    logger.info(f"Получено сообщение от {user_id}: {message_text}")

    # Пересылка в группу модерации
    if GROUP_CHAT_ID:
        try:
            if update.message.photo:
                photo = update.message.photo[-1]
                await context.bot.send_photo(
                    chat_id=GROUP_CHAT_ID,
                    photo=photo.file_id,
                    caption=f"Фото от пользователя {user_id}: {message_text}"
                )
            else:
                await context.bot.send_message(
                    chat_id=GROUP_CHAT_ID,
                    text=f"Сообщение от пользователя {user_id}: {message_text}"
                )
        except Exception as e:
            logger.error(f"Ошибка при пересылке: {e}")

    # Ответ пользователю
    try:
        await update.message.reply_text("✅ Сообщение получено! Админ проверит и опубликует.")
    except Exception as e:
        logger.error(f"Ошибка при ответе: {e}")

# Функция для запуска polling с правильным event loop
def start_polling():
    """Запускает Telegram polling в отдельном потоке с собственным event loop"""
    try:
        # Создаем новое приложение для этого потока
        application = Application.builder().token(TOKEN).build()
        application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
        
        logger.info("🔄 Запуск Telegram polling...")
        
        # Создаем новый event loop для этого потока
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Запускаем polling
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Ошибка polling: {e}")

# Запуск при импорте
def create_app():
    """Функция для запуска бота"""
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=start_polling)
    bot_thread.daemon = True
    bot_thread.start()
    
    logger.info("🚀 Бот запущен!")
    return flask_app

# Для запуска на Render
if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
