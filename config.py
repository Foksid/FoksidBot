# config.py
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_CHANNEL_ID = "UCGS02-NLVxwYHwqUx7IFr3g"
ADMIN_ID: int = int(os.getenv("ADMIN_ID", "1003278206"))  # Числовой ID админа
TELEGRAM_CHANNEL_USERNAME = "@foksid322"
DISCUSSION_CHAT_USERNAME = "@foksid322test"

# Настройки БД (заглушка, можно заменить на реальную реализацию)
DATABASE_URL = None
