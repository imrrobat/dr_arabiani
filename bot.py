import sqlite3
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.types import CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from utils import parse_schedule, build_time_keyboard, build_days_keyboard
from db import (
    get_available_days,
    get_free_nobats_by_day,
    get_all_nobats,
    clear_all_nobats,
    reserve_nobat,
    save_schedule_to_db,
    get_user_nobats,
)
from config import API_TOKEN, ADMIN_USERS
from menu import START_MENU


class ReserveState(StatesGroup):
    waiting_for_info = State()


conn = sqlite3.connect("database.db")
cur = conn.cursor()

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS nobat (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        day TEXT NOT NULL,
        time_slot TEXT NOT NULL,
        is_reserved INTEGER DEFAULT 0,
        reserved_name TEXT,
        reserved_phone TEXT,
        reserved_user_id INTEGER
    )
    """
)

conn.commit()
conn.close()


async def start_handler(pm: Message):
    await pm.answer(START_MENU)


async def add_handler(pm: Message):
    if pm.from_user.id in ADMIN_USERS:
        try:
            lines = pm.text.splitlines()
            inp = "\n".join(lines[1:])

            result = parse_schedule(inp)
            save_schedule_to_db(result)
            await pm.answer("نوبت‌ها با موفقیت ثبت شدند")

        except Exception as e:
            await pm.answer("فرمت اشتباه")
            print(e)
    else:
        await pm.answer("برای اضافه کردن باید ادمین باشین")


async def show_handler(pm: Message):
    if pm.from_user.id not in ADMIN_USERS:
        await pm.answer("شما دسترسی به این بخش ندارین")
        return

    rows = get_all_nobats()

    if not rows:
        await pm.answer("هیچ نوبتی ثبت نشده")
        return

    lines = []

    for day, time_slot, is_reserved, name, phone in rows:
        if is_reserved:
            lines.append(f"{day} - {time_slot} - رزرو شده توسط {name} - {phone}")
        else:
            lines.append(f"{day} - {time_slot} - آزاد")

    text = "\n".join(lines)
    await pm.answer(text)


async def nobat_handler(pm: Message):
    days = get_available_days()

    if not days:
        await pm.answer("نوبت آزادی وجود نداره")
        return

    keyboard = build_days_keyboard(days)

    await pm.answer("لطفا روز مورد نظر رو انتخاب کن:", reply_markup=keyboard)


async def day_selected_handler(cb: CallbackQuery):
    day = cb.data.split(":", 1)[1]

    nobats = get_free_nobats_by_day(day)

    if not nobats:
        await cb.message.edit_text("برای این روز نوبت آزادی وجود نداره")
        return

    keyboard = build_time_keyboard(day, nobats)

    await cb.message.edit_text(f"نوبت‌های آزاد {day}:", reply_markup=keyboard)

    await cb.answer()


async def reserve_nobat_handler(cb: CallbackQuery, state: FSMContext):
    nobat_id = int(cb.data.split(":")[1])

    await state.update_data(nobat_id=nobat_id)
    await state.set_state(ReserveState.waiting_for_info)

    await cb.message.edit_text(
        "لطفا اسم و فامیل رو در یک خط بنویس\n"
        "و در خط بعدی شماره تماس رو وارد کن\n\n"
        "مثال:\n"
        "نیکولو پاگانینی\n"
        "123456789"
    )

    await cb.answer()


async def receive_user_info(pm: Message, state: FSMContext):
    data = pm.text.strip().splitlines()

    if len(data) != 2:
        await pm.answer(
            "فرمت اشتباهه ❌\n" "لطفا اسم و فامیل و شماره تماس رو دقیقا در دو خط بفرست"
        )
        return

    name = data[0].strip()
    phone = data[1].strip()
    user_id = pm.from_user.id

    state_data = await state.get_data()
    nobat_id = state_data["nobat_id"]

    reserve_nobat(nobat_id, user_id, name, phone)

    await pm.answer("نوبت با موفقیت ثبت شد ✅")

    await state.clear()


async def clear_handler(pm: Message):
    if pm.from_user.id not in ADMIN_USERS:
        await pm.answer("شما اجازه انجام این کار رو ندارین ❌")
        return

    clear_all_nobats()
    await pm.answer("تمام نوبت‌ها با موفقیت پاک شدند ✅")


async def my_nobat_handler(pm: Message):
    user_id = pm.from_user.id
    rows = get_user_nobats(user_id)

    if not rows:
        await pm.answer("شما هیچ نوبتی رزرو نکردین")
        return

    lines = []
    for day, time_slot, name, phone in rows:
        lines.append(f"{day} - {time_slot}")

    await pm.answer("نوبت‌های شما:\n" + "\n".join(lines))


async def main():
    bot = Bot(API_TOKEN)
    dp = Dispatcher()

    dp.message.register(start_handler, CommandStart())
    dp.message.register(add_handler, Command("add"))
    dp.message.register(show_handler, Command("show"))
    dp.message.register(nobat_handler, Command("nobat"))
    dp.message.register(clear_handler, Command("clear"))
    dp.message.register(my_nobat_handler, Command("mine"))

    dp.callback_query.register(
        day_selected_handler, lambda c: c.data.startswith("day:")
    )

    dp.callback_query.register(
        reserve_nobat_handler, lambda c: c.data.startswith("reserve:")
    )
    dp.message.register(receive_user_info, ReserveState.waiting_for_info)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
