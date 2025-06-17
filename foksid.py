import telebot
from googleapiclient.discovery import build
import os
import time

# === Настройки бота и YouTube API ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = "UCGS02-NLVxwYHwqUx7IFr3g"  # ID твоего канала

# === Инициализация бота и YouTube API ===
bot = telebot.TeleBot(BOT_TOKEN)
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

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


# === Команды /start и /help === 
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Напишите ключевое слово для поиска видео на моем YouTube-канале.")


# === Обработка любого текстового сообщения === 
@bot.message_handler(content_types=['text'])
def handle_text(message):
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


# === Отправка первого сообщения в обсуждениях канала ===
WELCOME_MESSAGE = "Привет! Ознакомьтесь с правилами канала: https://t.me/yourrules" 

def get_discussion_chat_id(channel_post):
    """Получаем чат обсуждений из поста"""
    if channel_post.forward_from_chat:
        return channel_post.forward_from_chat.id
    elif channel_post.reply_to_message and hasattr(channel_post.reply_to_message, 'reply_to_story_id'):
        return channel_post.reply_to_message.reply_to_story_id
    return None

@bot.channel_post_handler(func=lambda post: True)
def handle_new_channel_post(channel_post):
    chat_id = get_discussion_chat_id(channel_post)
    if chat_id:
        try:
            bot.send_message(chat_id, WELCOME_MESSAGE, reply_to_message_id=channel_post.message_id)
            print(f"[Успех] Сообщение отправлено в обсуждение поста: {channel_post.message_id}")
        except Exception as e:
            print(f"[Ошибка] Не удалось отправить сообщение в обсуждение: {e}")


# === Перезапуск бота при ошибках ===
if __name__ == "__main__":
    print("Бот запущен...")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"[Ошибка] {e}. Перезапуск бота через 15 секунд...")
            time.sleep(15)
