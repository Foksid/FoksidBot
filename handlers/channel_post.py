# handlers/channel_post.py

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import ChatTypeFilter
from services.discussion_service import store_pending_first_comment
from bot_settings import FIRST_COMMENT_TEXT, RULES_URL
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()
router.message.filter(ChatTypeFilter("channel"))

@router.channel_message()
async def handle_new_channel_post(message: Message):
    print(f"[DEBUG] Получен пост из чата: {message.chat.id}")

    if message.chat.username != "foksid322":
        return

    post_id = message.message_id
    print(f"[INFO] Новый пост в канале, ID: {post_id}")

    rules_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Правила", url=RULES_URL)]
        ]
    )

    store_pending_first_comment(
        channel_id=message.chat.id,
        channel_message_id=post_id,
        comment_text=FIRST_COMMENT_TEXT,
        comment_markup=rules_kb
    )
