"""
db/models.py

peewee models for this project's ONE new table: MarkupSession.

Why peewee: it is literally what Prodigy itself uses internally for its own
SQLite/Postgres/MySQL storage, so extending the same database with peewee is
the natural, low-friction fit rather than introducing a second ORM/toolchain.

IMPORTANT: this file does NOT redefine or touch Prodigy's own tables
(examples, datasets, links, etc). Those already exist once Prodigy is
installed and has been run at least once -- this module only adds one
sibling table, MarkupSession, used to track per-day start/end times for the
"во сколько начал/закончил" daily-breakdown feature in the analytics view
(index.html's "Разметка по дням" table). Prodigy does not track this out of
the box, so recipes/audio_markup.py writes to it explicitly.

Connection is intentionally LAZY (see get_db() / init_db() below): importing
this module never opens a real database connection. That keeps the module
safe to import in contexts with no database available yet (e.g. dashboard
startup before init_db.py has run, or this project's own py_compile / import
smoke tests) and matches peewee's own recommended pattern for deferring
database binding.
"""

import os
from datetime import datetime, date

from peewee import (
    AutoField,
    CharField,
    DateField,
    DateTimeField,
    IntegerField,
    Model,
)
from playhouse.db_url import connect as db_url_connect

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # python-dotenv is in requirements.txt, but don't hard-fail import if
    # it's missing for some reason -- .env is only a convenience.
    pass


class _LazyDatabase:
    """
    Proxy-like lazy database handle.

    peewee's own DatabaseProxy is the "correct" tool for this, but a tiny
    explicit wrapper keeps this file readable for someone skimming it who
    doesn't already know peewee's proxy idiom. Nothing here opens a socket
    or file handle until .get() is first called.
    """

    def __init__(self):
        self._db = None

    def get(self):
        if self._db is None:
            self._db = self._build()
        return self._db

    def _build(self):
        # Precedence: explicit DASHBOARD_DB_URL (if the dev team decides
        # MarkupSession should live in its own database -- see README.md's
        # "open question") > PRODIGY_DB_URL (the default recommendation:
        # live in the same database Prodigy already uses) > a local sqlite
        # file, so this module still works for a standalone demo/import
        # check with no .env configured at all.
        url = (
            os.environ.get("DASHBOARD_DB_URL")
            or os.environ.get("PRODIGY_DB_URL")
            or "sqlite:///" + os.path.join(os.path.dirname(__file__), "markup_sessions.db")
        )
        return db_url_connect(url)


_lazy_db = _LazyDatabase()


class _DeferredDatabaseProxy:
    """Makes `database = deferred_db` in Meta resolve lazily on first use."""

    def __getattr__(self, item):
        return getattr(_lazy_db.get(), item)


deferred_db = _DeferredDatabaseProxy()


class BaseModel(Model):
    class Meta:
        database = deferred_db


class MarkupSession(BaseModel):
    """
    The one new table this project adds.

    One row per (user, project, date): the annotator's markup session for
    that project on that day. started_at/ended_at back the daily-breakdown
    table in index.html's analytics view (columns: Дата / Задач размечено /
    Начало / Окончание / Время). tasks_count is the running count of
    examples answered in that session, incremented by
    recipes/audio_markup.py's update() callback.
    """

    id = AutoField()
    user = CharField(max_length=128, index=True)
    project_id = CharField(max_length=128, index=True)
    session_date = DateField(index=True, default=date.today)
    started_at = DateTimeField(null=True)
    ended_at = DateTimeField(null=True)
    tasks_count = IntegerField(default=0)

    class Meta:
        indexes = (
            # One session-per-day per user per project is the intended
            # shape; enforced at the query level in recipes/audio_markup.py
            # (get-or-create by user+project+date) rather than as a DB
            # uniqueness constraint, to keep this file simple to read.
            (("user", "project_id", "session_date"), False),
        )

    def touch_end(self, when: datetime | None = None):
        """Update ended_at to `when` (default: now) and save."""
        self.ended_at = when or datetime.utcnow()
        self.save()


def get_database():
    """Public accessor used by dashboard/app.py and init_db.py."""
    return _lazy_db.get()
