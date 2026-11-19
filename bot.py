
import os
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = "@Black_Rose_Music1"

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not configured")

bot = Bot(
    TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

db = sqlite3.connect("music.db")
db.execute("""
CREATE TABLE IF NOT EXISTS songs (
    message_id INTEGER PRIMARY KEY,
    title TEXT
)
""")
db.commit()


async def is_member(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False


def join_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🌹 عضویت در BLACK ROSE MUSIC",
            url="https://t.me/Black_Rose_Music1"
        )],
        [InlineKeyboardButton(
            text="✅ بررسی عضویت",
            callback_data="check"
        )]
    ])


@dp.message(CommandStart())
async def start(message: Message):
    if not await is_member(message.from_user.id):
        await message.answer(
            "🌹 برای استفاده از ربات ابتدا عضو کانال شو:",
            reply_markup=join_keyboard()
        )
        return

    await message.answer(
        "🖤 به BLACK ROSE MUSIC خوش اومدی!\n\n"
        "🎵 اسم آهنگ یا خواننده رو بفرست تا پیداش کنم."
    )


@dp.channel_post()
async def save_music(message: Message):
    title = message.caption or ""

    if message.audio:
        title = message.audio.title or title
        if message.audio.performer:
            title += " " + message.audio.performer
        title += " " + (message.audio.file_name or "")

    elif message.document:
        title += " " + (message.document.file_name or "")

    elif message.video:
        title += " ویدیو"

    else:
        return

    db.execute(
        "INSERT OR REPLACE INTO songs VALUES (?, ?)",
        (message.message_id, title.strip())
    )
    db.commit()


@dp.message(F.text)
async def search_music(message: Message):
    if not await is_member(message.from_user.id):
        await message.answer(
            "🔒 برای دریافت آهنگ ابتدا عضو کانال شو.",
            reply_markup=join_keyboard()
        )
        return

    query = message.text.strip()

    if query.startswith("/"):
        return

    results = db.execute(
        "SELECT message_id, title FROM songs "
        "WHERE title LIKE ? LIMIT 10",
        (f"%{query}%",)
    ).fetchall()

    if not results:
        await message.answer(
            "😔 آهنگی پیدا نشد.\n"
            "اسم دیگری امتحان کن."
        )
        return

    buttons = []
    for message_id, title in results:
        buttons.append([
            InlineKeyboardButton(
                text="🎵 " + (title[:50] or "دریافت آهنگ"),
                callback_data=f"song:{message_id}"
            )
        ])

    await message.answer(
        "🎧 آهنگ‌های پیدا شده:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        )
    )


@dp.callback_query(F.data == "check")
async def check_membership(callback: CallbackQuery):
    if await is_member(callback.from_user.id):
        await callback.message.edit_text(
            "🌹 عضویتت تأیید شد!\n"
            "حالا اسم آهنگ رو بفرست."
        )
    else:
        await callback.answer(
            "هنوز عضو کانال نشدی!",
            show_alert=True
        )


@dp.callback_query(F.data.startswith("song:"))
async def send_song(callback: CallbackQuery):
    if not await is_member(callback.from_user.id):
        await callback.message.answer(
            "🔒 ابتدا عضو کانال شو.",
            reply_markup=join_keyboard()
        )
        await callback.answer()
        return

    message_id = int(callback.data.split(":")[1])

    try:
        await bot.copy_message(
            chat_id=callback.from_user.id,
            from_chat_id=CHANNEL,
            message_id=message_id
        )
        await callback.answer("آهنگ ارسال شد 🎵")
    except Exception:
        await callback.answer(
            "ارسال آهنگ ناموفق بود.",
            show_alert=True
        )


async def main():
    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types()
    )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
