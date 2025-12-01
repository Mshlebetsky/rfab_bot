from __future__ import annotations
import asyncio
import logging
import os

from aiogram.enums import ParseMode
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from menu.admin import admin_router
from menu.menu import menu_router
from db.db import import_menu_json, init_db


# --------------------------- CONFIG ---------------------------
BOT_TOKEN = os.getenv('BOT_TOKEN', 'PUT_YOUR_TOKEN_HERE')
MENU_JSON_PATH = 'menu/menu.json'  # optional path for import


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)





# --------------------------- AIORGRAM BOT ---------------------------

load_dotenv()
token = os.getenv("TOKKEN")


if not token:
    logger.critical("❌ Не найден токен в .env (TOKEN)")
    raise RuntimeError("Отсутствует TOKEN в .env")


bot = Bot(
    token=token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    timeout=60
)
dp = Dispatcher()
dp.include_router(menu_router)
dp.include_router(admin_router)


# --------------------------- STARTUP ---------------------------

async def main():
    init_db()
    # optionally import menu.json if exists
    if os.path.exists(MENU_JSON_PATH):
        logger.info('Found menu.json: importing...')
        import_menu_json(MENU_JSON_PATH)
    print('Bot is starting...')
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
