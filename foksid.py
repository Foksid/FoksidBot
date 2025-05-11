import telebot
from googleapiclient.discovery import build

# === Настройки ===
BOT_TOKEN = 'ВСТАВЬ_ТОКЕН_БОТА'  # Получить можно у @BotFather
YOUTUBE_API_KEY = 'ВСТАВЬ_ТВОЙ_YOUTUBE_API_КЛЮЧ'
CHANNEL_ID = 'UCGS02-NLVxwYHwqUx7IFr3g'  # ID твоего канала

# === Инициализация бота и YouTube API ===
bot = telebot.TeleBot(BOT_TOKEN)
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# === Функция поиска видео на канале по ключевому слову ===
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
            if keyword.lower() in title.lower():
                video_id = item['id']['videoId']
                url = f"https://youtu.be/ {video_id}"
                result.append({'title': title, 'url': url})

        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

    return result

# === Обработка сообщений ===
@bot.message_handler(func=lambda m: '@FoksidBot' in m.text)
def handle_mention(message):
    text = message.text

    # Убираем "@FoksidBot" из текста и обрезаем лишние пробелы
    query = text.replace('@FoksidBot', '').strip()

    if not query:
        bot.reply_to(message, "Напиши после @FoksidBot, о чём тебе нужно видео. Например:\n\"@FoksidBot как делать рестрикторы\"")
        return

    bot.send_message(message.chat.id, f"Ищу видео по запросу: \"{query}\"...")

    videos = search_videos(query)

    if videos:
        for video in videos:
            bot.send_message(message.chat.id, f"🎥 {video['title']}\n{video['url']}")
    else:
        bot.send_message(message.chat.id, f"Видео по запросу \"{query}\" не найдены.")

# === Запуск бота ===
print("Бот запущен...")
bot.polling(none_stop=True)