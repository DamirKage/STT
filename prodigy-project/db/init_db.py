"""
db/init_db.py

Tiny standalone script: create the MarkupSession table if it doesn't exist
yet. Run this once before first use:

    python db/init_db.py

This does NOT create or touch any of Prodigy's own tables (examples,
datasets, links, ...) -- those are created and managed by Prodigy itself the
first time it runs. This script only creates MarkupSession, the one new
sibling table this project adds (see db/models.py and README.md).

Safe to run against either the same database Prodigy already uses
(PRODIGY_DB_URL) or a separate one (DASHBOARD_DB_URL) -- see .env.example
and README.md's "открытый вопрос" about which of those two the dev team
prefers. With no .env configured at all, it falls back to a local sqlite
file (db/markup_sessions.db) so this script -- and anything that imports
db/models.py -- works standalone for a demo, which is also what makes the
dashboard importable/testable without a live Prodigy database (see
dashboard/app.py).
"""

import os
import sys

# Make sure this works whether invoked as `python db/init_db.py` (script's
# own directory ends up on sys.path, not the project root) or as
# `python -m db.init_db` from the project root (already works) -- inserting
# the project root explicitly covers both without requiring callers to
# remember the right invocation form.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.models import MarkupSession, get_database


def main():
    db = get_database()
    db.connect(reuse_if_open=True)
    try:
        db.create_tables([MarkupSession])
        print(f"MarkupSession table ready in: {db.database}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
