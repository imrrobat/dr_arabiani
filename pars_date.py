from datetime import datetime, timedelta


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
