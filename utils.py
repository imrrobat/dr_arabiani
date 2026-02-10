from datetime import datetime, timedelta
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def parse_schedule(inp: str) -> dict:
    schedule = {}
    current_day = None

    for line in inp.strip().splitlines():
        line = line.strip()

        if not line:
            continue

        if "-" not in line:
            current_day = line
            schedule[current_day] = []
        else:
            schedule[current_day].append(line)

    def split_to_45min(time_range: str):
        start_str, end_str = time_range.split("-")

        start_time = datetime.strptime(start_str, "%H:%M")
        end_time = datetime.strptime(end_str, "%H:%M")

        result = []
        current = start_time

        while current + timedelta(minutes=45) <= end_time:
            start_slot = current.strftime("%H:%M")
            end_slot = (current + timedelta(minutes=45)).strftime("%H:%M")

            result.append(f"{start_slot}-{end_slot}")
            current += timedelta(hours=1)

        return result

    final_schedule = {}

    for day, ranges in schedule.items():
        final_schedule[day] = []

        for r in ranges:
            final_schedule[day].extend(split_to_45min(r))

    return final_schedule


def build_time_keyboard(day, nobats):
    keyboard = []
    row = []

    for i, (nobat_id, time_slot) in enumerate(nobats):
        start_time, end_time = time_slot.split("-")

        row.append(
            InlineKeyboardButton(
                text=f"{start_time} - {end_time}",
                callback_data=f"reserve:{nobat_id}"
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