# config.py
# === Бот ===
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")  # Токен бота
ADMIN_ID: int = int(os.getenv("ADMIN_ID", "1003278206"))  # Числовой ID администратора

# === YouTube ===
YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")
YOUTUBE_CHANNEL_ID: str = "UCGS02-NLVxwYHwqUx7IFr3g"  # ID твоего YouTube-канала

# === Telegram каналы ===
TELEGRAM_CHANNEL_USERNAME: str = "@foksid322"         # Основной канал
DISCUSSION_CHAT_USERNAME: str = "@foksid322test"       # Группа обсуждений

# === База данных (заглушка) ===
DATABASE_URL = None
