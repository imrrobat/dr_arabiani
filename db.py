import sqlite3

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


def clear_all_nobats():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("DELETE FROM nobat")

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
