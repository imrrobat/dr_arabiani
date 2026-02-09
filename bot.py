import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from pars_date import parse_schedule
from config import API_TOKEN, ADMIN_USERS


async def start_handler(pm: Message):
    await pm.answer("سلام به بات دکتر عربیانی خوش اومدید")


async def add_handler(pm: Message):
    if pm.from_user.id in ADMIN_USERS:
        try:
            result = parse_schedule(pm.text[1:])
            await pm.answer(result)
        except:
            await pm.answer("Error")
    else:
        await pm.answer("برای اضافه کردن باید ادمین باشین")


async def main():
    bot = Bot(API_TOKEN)
    dp = Dispatcher()

    dp.message.register(start_handler, CommandStart())
    dp.message.register(add_handler, Command("add"))

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
