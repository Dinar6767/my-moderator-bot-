import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.handlers import start, admin, moderation, moderation_commands, support, premium
from bot.middlewares.antiflood import AntiFloodMiddleware
from core.config import BOT_TOKEN
from core.logger import setup_logger
from database.session import init_db, close_db

log = setup_logger()


async def main() -> None:
    log.info("Инициализация БД...")
    await init_db()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.middleware(AntiFloodMiddleware(max_messages=5, window=10))

    dp.include_router(start.router)
    dp.include_router(admin.router)
    dp.include_router(moderation_commands.router)
    dp.include_router(moderation.router)
    dp.include_router(support.router)
    dp.include_router(premium.router)

    log.info("Бот запущен. Polling...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await close_db()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.warning("Остановка.")
