# main.py

import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import channel_post, admin_create_post, user  # <-- добавили user
from services.discussion_service import pending_comments
# Логирование
logging.basicConfig(level=logging.INFO)

async def comment_sender(bot: Bot):
    from aiogram import Bot
    while True:
        for ((channel_id, message_id), data) in list(pending_comments.items()):
            attempt = 0
            max_attempts = 5
            delay = 3

            while attempt < max_attempts:
                try:
                    await bot.send_message(
                        chat_id=channel_id,
                        text=data["text"],
                        reply_to_message_id=message_id,
                        reply_markup=data.get("markup")
                    )
                    del pending_comments[(channel_id, message_id)]
                    print(f"[Успех] Комментарий к {message_id} отправлен")
                    break
                except Exception as e:
                    print(f"[Ошибка] Попытка {attempt + 1} — Не удалось отправить комментарий к {message_id}: {e}")
                    attempt += 1
                    await asyncio.sleep(delay)
            else:
                print(f"[Критично] Не удалось отправить комментарий к {message_id} за {max_attempts} попыток.")
                del pending_comments[(channel_id, message_id)]

        await asyncio.sleep(2)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Подключаем роутеры
    dp.include_router(user.router)
    dp.include_router(channel_post.router)
    dp.include_router(admin_create_post.router)

    # Запуск фоновой задачи
    asyncio.create_task(comment_sender(bot))

    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
