import telebot
from googleapiclient.discovery import build
import os
import time
from fuzzywuzzy import fuzz

# === Настройки бота и API ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_CHANNEL_ID = "UCGS02-NLVxwYHwqUx7IFr3g"  # ID твоего YouTube-канала

# === Инициализация бота и YouTube API ===
bot = telebot.TeleBot(BOT_TOKEN)
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# === Команда /start и /help ===
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if message.chat.type == 'private':
        bot.reply_to(message, "Привет! Напишите ключевое слово или целый запрос для поиска видео на моем YouTube-канале.")

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

# === Поиск видео на YouTube по ключевому слову с fuzzy-сравнением ===
def search_videos(keyword):
    result = []
    next_page_token = None
    keyword_lower = keyword.strip().lower()

    while len(result) < 50:  # максимум 20 результатов
        request = youtube.search().list(
            part='snippet',
            channelId=YOUTUBE_CHANNEL_ID,
            q=keyword,
            type='video',
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response.get('items', []):
            title = item['snippet']['title']
            video_id = item['id']['videoId']

            if not get_valid_video(video_id):
                print(f"[Инфо] Пропущено недоступное видео: {video_id}")
                continue

            title_lower = title.lower()
            match_score = fuzz.partial_ratio(keyword_lower, title_lower)

            if match_score > 45:  # можно менять порог от 0 до 100
                url = f"https://youtube.com/watch?v={video_id}"
                result.append({'title': title, 'url': url, 'score': match_score})

        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

    # Сортируем по релевантности 
    result.sort(key=lambda x: x['score'], reverse=True)
    # Возвращаем только нужные поля
    return [{'title': item['title'], 'url': item['url']} for item in result[:20]]

# === Обработка текстовых сообщений ТОЛЬКО в ЛС ===  
@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.chat.type == 'private':
        text = message.text.strip().lower()

        if len(text) < 2:
            bot.reply_to(message, "Введите минимум 2 символа для поиска.")
            return

        bot.send_message(message.chat.id, f"Ищу видео по запросу: \"{text}\"...")

        videos = search_videos(text)

        if videos:
            for video in videos:
                bot.send_message(message.chat.id, f"{video['title']}\n{video['url']}")
        else:
            bot.send_message(message.chat.id, f"Видео по запросу \"{text}\" не найдены, попробуйте перефразировать запрос.")

# === Перезапуск бота при ошибках ===
if __name__ == "__main__":
    print("Бот запущен...")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"[Ошибка] {e}. Перезапуск бота через 15 секунд...")
            time.sleep(15)
