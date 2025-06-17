import telebot
from googleapiclient.discovery import build
import os
import time
import json

# === Настройки бота и YouTube API ===
BOT_TOKEN = os.getenv("BOT_TOKEN")  # или '1234567890:ABCdefGHIjklmnoPQRStuv'
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")  # или 'AIza...'
CHANNEL_ID = "UCGS02-NLVxwYHwqUx7IFr3g"  # Заменить на ID своего канала
DISCUSSION_CHAT_ID = "-1002859600907"  # Числовой ID группы обсуждений (публичной!)
POSTS_FILE = "processed_posts.json"  # Файл для сохранения обработанных постов

# === Инициализация бота и YouTube API ===
bot = telebot.TeleBot(BOT_TOKEN)
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

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

# === Приветственное сообщение под постом ===
WELCOME_MESSAGE = "Привет! Ознакомьтесь с правилами канала: https://t.me/yourrules" 

# === Хранилище уже обработанных постов с загрузкой из файла ===
try:
    with open(POSTS_FILE, "r") as f:
        processed_posts = set(json.load(f))
except FileNotFoundError:
    processed_posts = set()

def save_processed_posts():
    with open(POSTS_FILE, "w") as f:
        json.dump(list(processed_posts), f)

# === Обработчик новых постов в канале ===
@bot.channel_post_handler(func=lambda post: True)
def handle_new_channel_post(channel_post):
    print("[DEBUG] Получено событие:", channel_post)  # Диагностический вывод
    try:
        # Проверяем, что это пост из канала, а не из другой группы или ЛС
        if channel_post.chat.type != 'channel':
            print("[DEBUG] Это не канал")
            return

        # Получаем ID поста
        post_id = channel_post.message_id

        # Проверяем, обрабатывали ли мы его уже
        if post_id in processed_posts:
            print(f"[Инфо] Пост {post_id} уже обработан, пропускаю.")
            return

        print(f"[Инфо] Новый пост в канале, ID: {post_id}")

        # === Отправляем сообщение в группу обсуждений как ответ на пост ===
        bot.send_message(
            chat_id=DISCUSSION_CHAT_ID,
            text=WELCOME_MESSAGE,
            reply_to_message_id=post_id
        )

        # Добавляем в список обработанных и сохраняем
        processed_posts.add(post_id)
        save_processed_posts()

        print(f"[Успех] Сообщение отправлено как комментарий к посту {post_id}")

    except Exception as e:
        print(f"[Ошибка] Не удалось обработать пост: {e}")

# === Перезапуск бота при ошибках ===
if __name__ == "__main__":
    print("Бот запущен...")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"[Ошибка] {e}. Перезапуск бота через 15 секунд...")
            time.sleep(15)
