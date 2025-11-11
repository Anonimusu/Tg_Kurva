# bot.py
import os
import threading
from flask import Flask
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Логирование (полезно для Render -> Logs)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем токен и ID чата из переменных окружения
TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROUP_CHAT_ID = os.environ.get("GROUP_CHAT_ID")  # можно задать в Render, если хочешь

if not TOKEN:
    logger.error("TELEGRAM_TOKEN не задан. Установите переменную окружения TELEGRAM_TOKEN в Render.")
    raise RuntimeError("TELEGRAM_TOKEN не задан")

if not GROUP_CHAT_ID:
    logger.warning("GROUP_CHAT_ID не задан. Сообщения в модерацию будут отправляться в None (проверьте).")

# Функция обработки сообщений (текст, фото и т.д.)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Иногда update.message может быть None (например, callback_query), но у тебя обычные сообщения
    if update.message is None:
        return

    message_text = update.message.text or update.message.caption or "Сообщение без текста (возможно, фото)"
    user_id = update.message.from_user.id

    # Пересылка в группу модерации (если задан)
    if GROUP_CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text=f"Новое сообщение от пользователя {user_id}: {message_text}"
            )
            # Если есть фото, пересылаем его в группу
            if update.message.photo:
                photo = update.message.photo[-1]  # Берём фото в максимальном разрешении
                await context.bot.send_photo(
                    chat_id=GROUP_CHAT_ID,
                    photo=photo.file_id,
                    caption=f"Фото от пользователя {user_id}: {message_text}"
                )
        except Exception as e:
            logger.exception("Ошибка при пересылке в модерацию: %s", e)

    # Ответ пользователю
    try:
        await update.message.reply_text("Сообщение получено! Админ проверит и опубликует анонимно. 🚫 Без личных данных!")
    except Exception as e:
        logger.exception("Ошибка при ответе пользователю: %s", e)

# Функция, которая запускает polling (в отдельном потоке)
def start_polling(app):
    """Запускает application.run_polling() — в отдельном потоке, чтобы главный поток мог запустить web-сервер."""
    logger.info("Запуск Telegram polling...")
    try:
        app.run_polling()
    except Exception as e:
        logger.exception("Polling завершился с ошибкой: %s", e)

# Создаём Flask сервер для ping (cron-job будет заходить сюда)
flask_app = Flask(__name__)

@flask_app.route("/")
def index():
    return "Bot is alive!", 200

if __name__ == "__main__":
    # Создаём приложение бота
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    # Запускаем polling в отдельном потоке
    t = threading.Thread(target=start_polling, args=(application,))
    t.daemon = True
    t.start()

    # Запускаем Flask — Render использует переменную PORT
    port = int(os.environ.get("PORT", 5000))
    logger.info("Запуск web-сервера на порту %s", port)
    flask_app.run(host="0.0.0.0", port=port)
