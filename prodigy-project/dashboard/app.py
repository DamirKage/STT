"""
dashboard/app.py

Small, read-only FastAPI service. This is the one genuinely new piece of
backend infrastructure in this project (see README.md) -- everything else
(recipes/, static/, prodigy.json) is config + hooks on top of Prodigy that
already exists once Prodigy is installed.

PRODUCTION NOTE: in production this would sit BEHIND Kaspi's existing auth
(login/QR/roles, see index.html and DEV_HANDOFF.md point 5) -- it does not
implement its own authentication or authorization here. Every route below
assumes the request already arrived authenticated/authorized by whatever
sits in front of it (a gateway, Kaspi's existing session middleware, etc).
That is out of scope for this scaffold.

Endpoints intentionally mirror the shapes already used by ../../index.html's
mock analytics data (PROJECT_ANALYTICS / renderDayTable in that file), so
dashboard/static/index.html can be a near-drop-in real version of the same
UI, just fetching from here instead of reading hardcoded JS objects.

DB access note: this module does NOT open a database connection at import
time (see db/models.py's lazy connection design) -- connections only happen
inside request handlers, the first time a query actually runs. That's what
lets `import dashboard.app` succeed even before db/init_db.py has been run
(see the verification section of the project's build notes / README.md).
"""

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from db.models import MarkupSession
from dashboard.wer_cer import compute_wer_cer_batch

app = FastAPI(title="Kaspi Markup Dashboard (read-only)")

# CORS enabled for local dev (dashboard/static/index.html and any other
# local frontend hitting this from a different port). Tighten this to a
# real allowlist before this ever runs anywhere near production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ── TODO(integration): demo WER/CER reference data ──────────────────────
# This scaffold has no access to Kaspi's real per-example transcriptions
# (those live inside Prodigy's own examples/answers, which this project
# does not reimplement -- see README.md). To make /api/projects and
# /api/projects/{id}/summary return *something* real-looking end-to-end
# rather than hardcoded numbers, this uses jiwer (dashboard/wer_cer.py)
# against a tiny built-in demo hypothesis/reference set per project.
#
# The real integration should replace this whole block with a read from
# wherever Kaspi's existing WER/CER pipeline already stores its
# per-annotator numbers (see dashboard/wer_cer.py's own TODO for the same
# point) -- this is a placeholder specifically so the demo is self-contained
# and doesn't silently show fabricated-looking round numbers.
_DEMO_TRANSCRIPTIONS: dict[str, dict[str, list[str]]] = {
    "ASTER_KZ_310826": {
        "hypotheses": ["сәлеметсіз бе қалайсыз", "каспи голд картасы"],
        "references": ["сәлеметсіз бе қалайсыз ба", "каспи голд картасы"],
    },
    "AI_ABC_CHAT": {
        "hypotheses": ["добрый день чем могу помочь", "спасибо за звонок"],
        "references": ["добрый день чем я могу вам помочь", "спасибо за звонок"],
    },
}


def _known_project_ids() -> list[str]:
    # Project ids come from whichever projects have at least one
    # MarkupSession row recorded, plus the demo set above (so the endpoint
    # still returns something before any real annotation has happened).
    from_sessions = {
        row.project_id for row in MarkupSession.select(MarkupSession.project_id).distinct()
    }
    return sorted(from_sessions | set(_DEMO_TRANSCRIPTIONS.keys()))


def _project_wer_cer(project_id: str):
    demo = _DEMO_TRANSCRIPTIONS.get(project_id)
    if not demo:
        return None
    return compute_wer_cer_batch(demo["hypotheses"], demo["references"])


class ProjectSummary(BaseModel):
    project_id: str
    tasks_count: int
    wer: float | None
    cer: float | None


class DailyRow(BaseModel):
    date: str
    tasks: int
    started_at: str | None
    ended_at: str | None


@app.get("/api/projects", response_model=list[ProjectSummary])
def list_projects():
    """
    Project list with avg WER/CER -- matches the project-list summary
    column in index.html's project table (the "WER/CER" column).
    """
    out = []
    for pid in _known_project_ids():
        tasks = (
            MarkupSession.select()
            .where(MarkupSession.project_id == pid)
        )
        total_tasks = sum(row.tasks_count for row in tasks)
        wc = _project_wer_cer(pid)
        out.append(
            ProjectSummary(
                project_id=pid,
                tasks_count=total_tasks,
                wer=wc.wer if wc else None,
                cer=wc.cer if wc else None,
            )
        )
    return out


@app.get("/api/projects/{project_id}/summary", response_model=ProjectSummary)
def project_summary(project_id: str):
    if project_id not in _known_project_ids():
        raise HTTPException(status_code=404, detail="Unknown project_id")

    tasks = MarkupSession.select().where(MarkupSession.project_id == project_id)
    total_tasks = sum(row.tasks_count for row in tasks)
    wc = _project_wer_cer(project_id)
    return ProjectSummary(
        project_id=project_id,
        tasks_count=total_tasks,
        wer=wc.wer if wc else None,
        cer=wc.cer if wc else None,
    )


@app.get("/api/projects/{project_id}/daily", response_model=list[DailyRow])
def project_daily(project_id: str):
    """
    date, tasks, started_at, ended_at from MarkupSession -- matches the
    exact daily-breakdown table shape in index.html's analytics view
    ("Разметка по дням": Дата / Задач размечено / Начало / Окончание /
    Время; "Время" is derived client-side from started_at/ended_at, same
    as this API returning the two timestamps and letting the caller
    format the duration).
    """
    if project_id not in _known_project_ids():
        raise HTTPException(status_code=404, detail="Unknown project_id")

    rows = (
        MarkupSession.select()
        .where(MarkupSession.project_id == project_id)
        .order_by(MarkupSession.session_date)
    )

    by_date: dict[str, DailyRow] = {}
    for row in rows:
        date_str = row.session_date.isoformat()
        by_date[date_str] = DailyRow(
            date=date_str,
            tasks=row.tasks_count,
            started_at=row.started_at.isoformat() if row.started_at else None,
            ended_at=row.ended_at.isoformat() if row.ended_at else None,
        )
    return list(by_date.values())


@app.get("/api/health")
def health():
    return {"status": "ok"}


# Serves dashboard/static/index.html (and any assets alongside it) at "/",
# so the demo page and its /api/* calls are same-origin by default. Mounted
# last so it doesn't shadow the /api/* routes above.
_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="static")
