import logging
import asyncio
from handlers import *
from aiogram import executor

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.to_thread(executor.start_polling(dp, skip_updates=False))
