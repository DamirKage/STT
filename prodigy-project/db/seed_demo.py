"""
db/seed_demo.py

Optional: populate MarkupSession with the SAME demo numbers already shown in
../../index.html's "Разметка по дням" table (PROJECT_ANALYTICS in that
file), so that running the dashboard locally (see PYCHARM_SETUP.md) shows
matching, non-empty data instead of an empty daily table -- init_db.py alone
only creates the table, it doesn't put anything in it.

This is purely a demo convenience. It is NOT how real rows get here in
production -- in production, recipes/audio_markup.py's update() callback
writes real rows as annotators actually work. Safe to re-run: it clears any
existing MarkupSession rows for these two demo project ids first, so running
it twice doesn't duplicate rows.

Run once, after init_db.py:

    python db/init_db.py
    python db/seed_demo.py
"""

import os
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.models import MarkupSession, get_database

DEMO_USER = "demo_user"

# date, tasks, start "HH:MM", end "HH:MM" -- copied from index.html's
# PROJECT_ANALYTICS.ASTER_KZ_310826.days / .AI_ABC_CHAT.days.
_DAYS = {
    "ASTER_KZ_310826": [
        ("2026-08-22", 452, "09:04", "18:12"),
        ("2026-08-23", 480, "08:58", "18:20"),
        ("2026-08-24", 465, "09:10", "18:05"),
        ("2026-08-25", 510, "08:55", "18:41"),
        ("2026-08-26", 495, "09:02", "18:25"),
        ("2026-08-27", 300, "09:20", "15:47"),
        ("2026-08-28", 280, "09:35", "15:10"),
        ("2026-08-29", 470, "09:05", "18:02"),
        ("2026-08-30", 505, "08:50", "18:38"),
        ("2026-08-31", 488, "09:00", "18:15"),
    ],
    "AI_ABC_CHAT": [
        ("2026-08-22", 210, "09:10", "14:52"),
        ("2026-08-23", 225, "09:05", "15:10"),
        ("2026-08-24", 198, "09:20", "14:35"),
        ("2026-08-25", 240, "09:00", "15:40"),
        ("2026-08-26", 232, "09:08", "15:22"),
        ("2026-08-27", 140, "09:30", "12:50"),
        ("2026-08-28", 130, "09:40", "12:15"),
        ("2026-08-29", 220, "09:12", "15:00"),
        ("2026-08-30", 238, "09:02", "15:35"),
        ("2026-08-31", 229, "09:06", "15:18"),
    ],
}


def _dt(day_iso: str, hm: str) -> datetime:
    d = date.fromisoformat(day_iso)
    h, m = (int(x) for x in hm.split(":"))
    return datetime(d.year, d.month, d.day, h, m)


def main():
    db = get_database()
    db.connect(reuse_if_open=True)
    try:
        db.create_tables([MarkupSession])  # no-op if init_db.py already ran

        for project_id in _DAYS:
            deleted = (
                MarkupSession.delete()
                .where(MarkupSession.project_id == project_id)
                .execute()
            )
            if deleted:
                print(f"{project_id}: cleared {deleted} existing row(s)")

        total = 0
        for project_id, rows in _DAYS.items():
            for day_iso, tasks, start_hm, end_hm in rows:
                MarkupSession.create(
                    user=DEMO_USER,
                    project_id=project_id,
                    session_date=date.fromisoformat(day_iso),
                    started_at=_dt(day_iso, start_hm),
                    ended_at=_dt(day_iso, end_hm),
                    tasks_count=tasks,
                )
                total += 1
        print(f"Seeded {total} MarkupSession rows across {len(_DAYS)} project(s) in: {db.database}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
