import telebot
from googleapiclient.discovery import build
import os
import time
import threading

# === Настройки бота и API ===
BOT_TOKEN = os.getenv("BOT_TOKEN") #or "ВАШ_ТОКЕН"  # Например: '1234567890:ABCdefGHIjklmnoPQRStuv'
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY") or "ВАШ_YOUTUBE_API_KEY"
YOUTUBE_CHANNEL_ID = "UCGS02-NLVxwYHwqUx7IFr3g"  # ID YouTube-канала
TELEGRAM_CHANNEL_ID = -1002847993909              # ID основного Telegram-канала
DISCUSSION_CHAT_ID = -1002880107017               # ID группы обсуждений

# === Сообщение под каждым постом канала ===
WELCOME_MESSAGE = "Привет! Ознакомьтесь с правилами канала: https://t.me/yourrules" 

# === Инициализация бота и YouTube API ===
bot = telebot.TeleBot(BOT_TOKEN)
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# === Хранилище отложенных комментариев ===
pending_comments = {}

def store_pending_first_comment(channel_id, channel_message_id, comment_text, comment_markup=None):
    """Сохраняет задачу на отправку первого комментария"""
    pending_comments[(channel_id, channel_message_id)] = {
        "text": comment_text,
        "markup": comment_markup
    }

# === Фоновый поток для отправки комментариев в группу ===
def comment_sender():
    while True:
        for ((channel_id, message_id), data) in list(pending_comments.items()):
            try:
                bot.send_message(
                    chat_id=DISCUSSION_CHAT_ID,
                    text=data["text"],
                    reply_to_message_id=message_id,
                    reply_markup=data.get("markup")
                )
                del pending_comments[(channel_id, message_id)]
            except Exception as e:
                print(f"[Ошибка] Не удалось отправить комментарий к {message_id}: {e}")
        time.sleep(5)

# Запуск фонового потока
threading.Thread(target=comment_sender, daemon=True).start()

# === Обработчик новых постов в Telegram-канале ===
@bot.channel_post_handler(func=lambda post: True)
def handle_new_channel_post(channel_post):
    print(f"[DEBUG] Получен пост из чата: {channel_post.chat.id}")

    if channel_post.chat.id != TELEGRAM_CHANNEL_ID:
        print(f"[INFO] Не мой канал. Ожидал: {TELEGRAM_CHANNEL_ID}, получил: {channel_post.chat.id}")
        return

    # Пропускаем репосты
    if channel_post.forward_from or channel_post.forward_from_chat:
        print("[DEBUG] Это репост — пропускаю")
        return

    try:
        post_id = channel_post.message_id
        print(f"[Инфо] Новый пост в канале, ID: {post_id}")

        # Сохраняем задачу на комментарий
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("Правила", url="https://t.me/yourrules")) 

        store_pending_first_comment(
            channel_id=channel_post.chat.id,
            channel_message_id=post_id,
            comment_text=WELCOME_MESSAGE,
            comment_markup=markup
        )

    except Exception as e:
        print(f"[Ошибка] Не удалось обработать пост: {e}")

# === Команда /start и /help ===
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if message.chat.type == 'private':
        bot.reply_to(message, "Привет! Напишите ключевое слово для поиска видео на моём YouTube-канале.")

# === Проверка доступности видео ===
def get_valid_video(video_id):
    try:
        request = youtube.videos().list(
            part='status',
            id=video_id
        )
        response = request.execute()
        if response['items']:
            status = response['items'][0]['status']['privacyStatus']
            if status == 'public':
                return True
    except Exception as e:
        print(f"[Ошибка] Не удалось проверить видео {video_id}: {e}")
    return False

# === Поиск видео на YouTube по ключевому слову ===
def search_videos(keyword):
    result = []
    next_page_token = None

    while len(result) < 10:  # максимум 10 результатов
        request = youtube.search().list(
            part='snippet',
            channelId=YOUTUBE_CHANNEL_ID,
            q=keyword,
            type='video',
            maxResults=10,
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response.get('items', []):
            title = item['snippet']['title']
            video_id = item['id']['videoId']
            if keyword.lower() in title.lower():
                if get_valid_video(video_id):  # Проверяем, доступно ли видео
                    url = f"https://youtube.com/watch?v={video_id}"
                    result.append({'title': title, 'url': url})
                else:
                    print(f"[Инфо] Пропущено недоступное видео: {video_id}")

        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

    return result

# === Обработка текстовых сообщений ТОЛЬКО в ЛС === 
@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.chat.type == 'private':
        text = message.text.strip().lower()

        if len(text) < 3:
            bot.reply_to(message, "Введите минимум 3 символа для поиска.")
            return

        bot.send_message(message.chat.id, f"Ищу видео по запросу: \"{text}\"...")

        videos = search_videos(text)

        if videos:
            for video in videos:
                bot.send_message(message.chat.id, f"{video['title']}\n{video['url']}")
        else:
            bot.send_message(message.chat.id, f"Видео по запросу \"{text}\" не найдены.")

# === Перезапуск бота при ошибках ===
if __name__ == "__main__":
    print("Бот запущен...")
    time.sleep(5)  # Ждём 5 секунд перед началом работы
    while True:
        try:
            bot.polling(none_stop=True, skip_pending=True)
        except Exception as e:
            print(f"[Ошибка] {e}. Перезапуск бота через 15 секунд...")
            time.sleep(15)
