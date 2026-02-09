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
            lines = pm.text.splitlines()
            inp = "\n".join(lines[1:])  # حذف /add

            result = parse_schedule(inp)

            text = ""
            for day, times in result.items():
                text += f"{day}\n"
                for t in times:
                    text += f"  {t}\n"

            await pm.answer(text)

        except Exception as e:
            await pm.answer("Error in input format")
            print(e)
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
