import asyncio
import os
import re
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.filters.command import CommandObject
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from database import get_user_profile,init_db,set_referrer,upsert_user

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
MINI_APP_URL = os.getenv("MINI_APP_URL")
PRODUCTION = os.getenv("APP_ENV", "development").lower() == "production"

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing in .env")
if not MINI_APP_URL:
    raise RuntimeError("MINI_APP_URL is missing in .env")
if PRODUCTION and not MINI_APP_URL.lower().startswith("https://"):
    raise RuntimeError("MINI_APP_URL must use https:// in production")

dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message,command:CommandObject):
    init_db()
    telegram_user=message.from_user
    telegram_id=str(telegram_user.id)
    is_new=get_user_profile(telegram_id) is None
    upsert_user({"id":telegram_user.id,"first_name":telegram_user.first_name,"last_name":telegram_user.last_name,"username":telegram_user.username,"language_code":telegram_user.language_code})
    referral=re.fullmatch(r"ref_(QP[A-Fa-f0-9]{6})",(command.args or "").strip())
    if is_new and referral:
        set_referrer(telegram_id,referral.group(1).upper())
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🛍 Открыть QulayPin",
            web_app=WebAppInfo(url=MINI_APP_URL)
        )]
    ])
    await message.answer(
        "Добро пожаловать в QulayPin 🎮\nПополняйте игры и сервисы прямо в Telegram.",
        reply_markup=kb
    )

async def main():
    bot = Bot(BOT_TOKEN)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
