import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from pars_date import parse_schedule
from config import API_TOKEN, ADMIN_USERS
import sqlite3
from collections import OrderedDict
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext


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
    reserved_phone TEXT
)
"""
)

conn.commit()
conn.close()


def get_available_days(limit=5):
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute(
        """
    SELECT DISTINCT day
    FROM nobat
    WHERE is_reserved = 0
    ORDER BY day
    LIMIT ?
    """,
        (limit,),
    )

    days = [row[0] for row in cur.fetchall()]
    conn.close()
    return days


def get_free_nobats_by_day(day):
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute(
        """
    SELECT id, time_slot
    FROM nobat
    WHERE day = ? AND is_reserved = 0
    ORDER BY time_slot
    """,
        (day,),
    )

    rows = cur.fetchall()
    conn.close()
    return rows


def build_time_keyboard(day, nobats):
    keyboard = []
    row = []

    for i, (nobat_id, time_slot) in enumerate(nobats):
        start_time = time_slot.split("-")[0]

        row.append(
            InlineKeyboardButton(
                text=f"{day} | {start_time}", callback_data=f"reserve:{nobat_id}"
            )
        )

        if (i + 1) % 4 == 0:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def build_days_keyboard(days):
    keyboard = [
        [InlineKeyboardButton(text=day, callback_data=f"day:{day}")] for day in days
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_free_nobats_for_keyboard():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute(
        """
    SELECT id, day, time_slot
    FROM nobat
    WHERE is_reserved = 0
    ORDER BY day, time_slot
    """
    )

    rows = cur.fetchall()
    conn.close()

    days = OrderedDict()

    for nobat_id, day, time_slot in rows:
        if day not in days:
            if len(days) == 3:  # فقط ۳ روز
                break
            days[day] = []

        if len(days[day]) < 8:  # فقط ۸ نوبت برای هر روز
            days[day].append((nobat_id, time_slot))

    return days


def build_nobat_keyboard(days_dict):
    keyboard = []

    for day, nobats in days_dict.items():
        row = []
        for i, (nobat_id, time_slot) in enumerate(nobats):
            start_time = time_slot.split("-")[0]

            row.append(
                InlineKeyboardButton(
                    text=f"{day} | {start_time}", callback_data=f"reserve:{nobat_id}"
                )
            )

            if (i + 1) % 4 == 0:
                keyboard.append(row)
                row = []

        if row:
            keyboard.append(row)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def save_schedule_to_db(schedule: dict):
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    for day, times in schedule.items():
        for t in times:
            cur.execute(
                """
            INSERT INTO nobat (day, time_slot)
            VALUES (?, ?)
            """,
                (day, t),
            )

    conn.commit()
    conn.close()


def get_free_nobats():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute(
        """
    SELECT id, day, time_slot
    FROM nobat
    WHERE is_reserved = 0
    """
    )

    rows = cur.fetchall()
    conn.close()
    return rows


def reserve_nobat(nobat_id, name, phone):
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute(
        """
    UPDATE nobat
    SET is_reserved = 1,
        reserved_name = ?,
        reserved_phone = ?
    WHERE id = ? AND is_reserved = 0
    """,
        (name, phone, nobat_id),
    )

    conn.commit()
    conn.close()


def get_all_nobats():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute(
        """
    SELECT day, time_slot, is_reserved, reserved_name, reserved_phone
    FROM nobat
    ORDER BY day, time_slot
    """
    )

    rows = cur.fetchall()
    conn.close()
    return rows


async def start_handler(pm: Message):
    await pm.answer("سلام به بات دکتر عربیانی خوش اومدید")


async def add_handler(pm: Message):
    if pm.from_user.id in ADMIN_USERS:
        try:
            lines = pm.text.splitlines()
            inp = "\n".join(lines[1:])

            result = parse_schedule(inp)
            save_schedule_to_db(result)

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


from aiogram.fsm.context import FSMContext


async def reserve_nobat_handler(cb: CallbackQuery, state: FSMContext):
    nobat_id = int(cb.data.split(":")[1])

    # ذخیره nobat_id در state
    await state.update_data(nobat_id=nobat_id)
    await state.set_state(ReserveState.waiting_for_info)

    await cb.message.edit_text(
        "لطفا اسم و فامیل رو در یک خط بنویس\n"
        "و در خط بعدی شماره تماس رو وارد کن\n\n"
        "مثال:\n"
        "علی حیدری\n"
        "849324234"
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

    state_data = await state.get_data()
    nobat_id = state_data["nobat_id"]

    # ذخیره در دیتابیس
    reserve_nobat(nobat_id, name, phone)

    await pm.answer("نوبت با موفقیت ثبت شد ✅")

    await state.clear()


async def main():
    bot = Bot(API_TOKEN)
    dp = Dispatcher()

    dp.message.register(start_handler, CommandStart())
    dp.message.register(add_handler, Command("add"))
    dp.message.register(show_handler, Command("show"))
    dp.message.register(nobat_handler, Command("nobat"))

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
