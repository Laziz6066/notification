import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os
import logging
from app.db.models import async_main
from app.handlers.user_handlers import router as user_router
from app.handlers.admin_handlers import router as admin_router
from app.services.scheduler import schedule_jobs

bot_token = os.getenv("BOT_TOKEN")
bot = Bot(token=bot_token)

async def main():
    await async_main()
    load_dotenv()
    await schedule_jobs(bot)


    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(admin_router)
    dp.include_router(user_router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')