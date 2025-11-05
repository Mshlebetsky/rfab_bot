import  asyncio, os
from  aiogram import Bot, Dispatcher, types, F
from  aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv
import logging

from menu.menu import menu_router
from scripts.logging_config import setup_logging


setup_logging()
logger = logging.getLogger(__name__)


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


def setup_routers(dp: Dispatcher) -> None:
    """Регистрация всех роутеров."""
    routers = [
        menu_router
    ]
    for router in routers:
        dp.include_router(router)


    # ================= MAIN =================
async def main():
    """Главная точка входа."""
    while True:
        try:
            # dp.update.middleware(DataBaseSession(session_pool=Session))

            await bot.delete_webhook(drop_pending_updates=True)

            setup_routers(dp)

            logger.info("▶️ Запуск long polling")
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        except Exception as e:
            logger.error(f"Ошибка в polling: {e}", exc_info=True)
        else:
            break
        await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен вручную (KeyboardInterrupt)")