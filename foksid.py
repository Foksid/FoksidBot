import telebot
from googleapiclient.discovery import build
import os
import time

# === Настройки бота и YouTube API ===
BOT_TOKEN = os.getenv("BOT_TOKEN")  # или '1234567890:ABCdefGHIjklmnoPQRStuv'
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")  # или 'AIza...'
CHANNEL_ID = "UCGS02-NLVxwYHwqUx7IFr3g"  # Заменить на ID своего канала
DISCUSSION_CHAT_ID = "-1002859600907"  # Числовой ID группы обсуждений (публичной!)

# === Инициализация бота и YouTube API ===
bot = telebot.TeleBot(BOT_TOKEN)
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# === Приветственное сообщение под постом канала ===
WELCOME_MESSAGE = "Привет! Ознакомьтесь с правилами канала: https://t.me/yourrules" 

# === Обработчик новых постов в канале ===
@bot.message_handler(commands=['test'])
def test_send_in_discussion(message):
    try:
        bot.send_message(
            chat_id=DISCUSSION_CHAT_ID,
            text="🤖 Это тестовое сообщение от бота!"
        )
        print("[Успех] Тестовое сообщение отправлено!")
        bot.reply_to(message, "✅ Тестовое сообщение отправлено в группу обсуждений.")
    except Exception as e:
        error_msg = f"[Ошибка при тесте]: {e}"
        print(error_msg)
        bot.reply_to(message, error_msg)

@bot.message_handler(func=lambda m: m.chat.type == 'channel', content_types=['text', 'photo', 'video'])
def handle_new_channel_post(message):
    try:
        chat_id = message.chat.id
        post_id = message.message_id

        print(f"[Инфо] Новый пост в канале {chat_id}, ID: {post_id}")

        # === Отправляем сообщение в группу обсуждений как ответ на пост ===
        bot.send_message(
            chat_id=DISCUSSION_CHAT_ID,
            text=WELCOME_MESSAGE,
            reply_to_message_id=post_id,
            disable_web_page_preview=True
        )

        print(f"[Успех] Сообщение отправлено как комментарий к посту {post_id}")

    except Exception as e:
        print(f"[Ошибка] Не удалось обработать пост: {e}")

# === Команда /start и /help ===
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if message.chat.type == 'private':
        bot.reply_to(message, "Привет! Напишите ключевое слово для поиска видео на моем YouTube-канале.")

# === Проверка, доступно ли видео ===
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

# === Поиск видео по ключевому слову на канале ===
def search_videos(keyword):
    result = []
    next_page_token = None

    while len(result) < 10:  # максимум 10 результатов
        request = youtube.search().list(
            part='snippet',
            channelId=CHANNEL_ID,
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
    # Обрабатываем только личные сообщения
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
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"[Ошибка] {e}. Перезапуск бота через 15 секунд...")
            time.sleep(15)
