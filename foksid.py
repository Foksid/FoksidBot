import telebot
from googleapiclient.discovery import build
import os
import time

# === Настройки бота и YouTube API ===
BOT_TOKEN = os.getenv("BOT_TOKEN")  # или '1234567890:ABCdefGHIjklmnoPQRStuv'
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")  # или 'AIza...'
CHANNEL_ID = "UCGS02-NLVxwYHwqUx7IFr3g"  # ID твоего YouTube-канала

# === ID канала и группы обсуждений ===
CHANNEL_CHAT_ID = "-1002672416624"  # username или -100... ID твоего канала
DISCUSSION_CHAT_ID = "-1002859600907"  # ID группы обсуждений

# === Приветственное сообщение под постом канала ===
WELCOME_MESSAGE = "Привет! Ознакомьтесь с правилами канала: https://t.me/yourrules" 

# === Инициализация бота и YouTube API ===
bot = telebot.TeleBot(BOT_TOKEN)
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)


# === Получаем последний пост из канала ===
def get_latest_post():
    try:
        # Получаем информацию о канале
        chat_info = bot.get_chat(CHANNEL_CHAT_ID)
        print(f"[DEBUG] Инфо о канале: {chat_info}")

        # Получаем самый свежий пост
        message = bot.get_message(chat_id=CHANNEL_CHAT_ID, message_id=chat_info.last_message_id)
        print(f"[DEBUG] Последнее сообщение: {message.message_id}")
        return message.message_id
    except Exception as e:
        print(f"[Ошибка] Не удалось получить последние посты: {e}")
        return None


# === Функция отправки сообщения в обсуждение поста ===
def send_welcome_to_discussion(post_id):
    try:
        bot.send_message(
            chat_id=DISCUSSION_CHAT_ID,
            text=WELCOME_MESSAGE,
            reply_to_message_id=post_id,
            disable_web_page_preview=True
        )
        print(f"[Успех] Сообщение отправлено как комментарий к посту {post_id}")

    except Exception as e:
        print(f"[Ошибка] Не удалось обработать пост: {e}")


# === Поиск видео по ключевому слову на канале ===
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
    if message.chat.type == 'private':
        bot.reply_to(message, "Привет! Напишите ключевое слово для поиска видео на моем YouTube-канале.")


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


# === Основной цикл работы бота ===
if __name__ == "__main__":
    print("Бот запущен...")

    last_post_id = None

    while True:
        try:
            latest_post_id = get_latest_post()
            if latest_post_id and latest_post_id != last_post_id:
                print(f"[Инфо] Обнаружен новый пост с ID: {latest_post_id}")
                send_welcome_to_discussion(latest_post_id)
                last_post_id = latest_post_id

            bot.polling(none_stop=True, timeout=60)
            time.sleep(10)  # раз в 10 секунд проверяем новые посты

        except Exception as e:
            print(f"[Ошибка] {e}. Перезапуск через 15 секунд...")
            time.sleep(15)
