# bot.py
import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получаем токен и ID чата из переменных окружения
TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROUP_CHAT_ID = os.environ.get("GROUP_CHAT_ID")
RENDER_URL = "tg-kurva.onrender.com"  # Твой URL на Render

if not TOKEN:
    logger.error("TELEGRAM_TOKEN не задан!")
    raise RuntimeError("TELEGRAM_TOKEN не задан")

# Создаём приложение Telegram
application = Application.builder().token(TOKEN).build()

# Функция обработки сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    message_text = update.message.text or update.message.caption or "Сообщение без текста"
    user_id = update.message.from_user.id

    logger.info(f"💬 Сообщение от {user_id}: {message_text}")

    # Ответ пользователю
    await update.message.reply_text("✅ Сообщение получено! Модератор проверит и опубликует.")

    # Пересылка в группу модерации
    if GROUP_CHAT_ID:
        try:
            if update.message.photo:
                photo = update.message.photo[-1]
                await context.bot.send_photo(
                    chat_id=GROUP_CHAT_ID,
                    photo=photo.file_id,
                    caption=f"📸 От {user_id}: {message_text}"
                )
            else:
                await context.bot.send_message(
                    chat_id=GROUP_CHAT_ID,
                    text=f"📝 От {user_id}: {message_text}"
                )
        except Exception as e:
            logger.error(f"❌ Ошибка пересылки: {e}")

# Добавляем обработчик
application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

# Создаём Flask приложение
app = Flask(__name__)

@app.route("/")
def home():
    return "🤖 Бот работает на вебхуках!", 200

@app.route("/webhook", methods=["POST"])
async def webhook():
    """Основной обработчик вебхуков"""
    try:
        # Получаем обновление от Telegram
        update = Update.de_json(request.get_json(), application.bot)
        
        # Обрабатываем сообщение
        await application.process_update(update)
        
        return "ok"
    except Exception as e:
        logger.error(f"❌ Ошибка в webhook: {e}")
        return "error", 500

async def set_webhook():
    """Установка вебхука при запуске"""
    webhook_url = f"https://{RENDER_URL}/webhook"
    
    try:
        await application.bot.set_webhook(webhook_url)
        logger.info(f"🌐 Webhook установлен: {webhook_url}")
    except Exception as e:
        logger.error(f"❌ Ошибка установки webhook: {e}")

# При запуске устанавливаем вебхук
if __name__ == '__main__':
    import asyncio
    
    # Устанавливаем вебхук
    asyncio.run(set_webhook())
    
    # Запускаем Flask
    logger.info("🚀 Бот запущен на вебхуках!")
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
