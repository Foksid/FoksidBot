# handlers/user.py

from aiogram import Router, F
from aiogram.types import Message
from googleapiclient.discovery import build
import os
from config import YOUTUBE_API_KEY, YOUTUBE_CHANNEL_ID

router = Router()

# Инициализируем YouTube API
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# === Функция поиска видео на YouTube ===
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
                url = f"https://youtube.com/watch?v={video_id}"
                result.append({'title': title, 'url': url})

        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

    return result

# === Обработчики команд === 
@router.message(Command("start", "help"))
async def cmd_start(message: Message):
    await message.answer("Привет! Напишите ключевое слово для поиска видео на моём YouTube-канале.")

@router.message(F.chat.type == "private")
async def handle_user_text(message: Message):
    text = message.text.strip().lower()
    
    if len(text) < 3:
        await message.reply("Введите минимум 3 символа для поиска.")
        return

    await message.answer(f"Ищу видео по запросу: «{text}»...")

    videos = search_videos(text)

    if videos:
        for video in videos:
            await message.answer(f"{video['title']}\n{video['url']}")
    else:
        await message.answer(f"Видео по запросу «{text}» не найдены.")
