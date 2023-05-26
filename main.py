import logging
import asyncio
from api_operator import *
from handlers import *
from aiogram import executor
from celery import Celery
from celery.schedules import crontab


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.to_thread(executor.start_polling(dp, skip_updates=False))
