import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from config import API_TOKEN


async def start_handler(pm: Message):
    await pm.answer("سلام به بات دکتر عربیانی خوش اومدید")


async def add_handler(pm: Message):
    await pm.answer("برای اضافه کردن باید ادمین باشین")


async def main():
    bot = Bot(API_TOKEN)
    dp = Dispatcher()

    dp.message.register(start_handler, CommandStart)
    dp.message.register(add_handler, Command("add"))

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
