"""
recipes/audio_markup.py

Custom Prodigy recipe for the audio transcription markup workflow described
in ../../index.html: waveform + play/volume/speed/repeat player, word
buffer (Ctrl+Shift+1-9), transcription textarea, kk/ru language choice,
accept/reject/skip.

CANNOT BE IMPORTED OR RUN IN THIS ENVIRONMENT: `prodigy` is a paid,
license-gated package not available on public PyPI, and neither this
environment nor the author has a license key here (see ../PYCHARM_SETUP.md).
This file is written to be structurally and technically correct against
Prodigy's publicly documented conventions, syntax-checked with
`python3 -m py_compile`, and read over for logical mistakes -- but it has
NOT been run against a real Prodigy instance. Several specific API details
are flagged inline with "CONFIRM WITH YOUR PRODIGY VERSION" where the exact
current name/shape is uncertain (Prodigy's decorator/CLI API changed in the
1.11+ rewrite onto their `radicli` library) -- check those against
`python -m prodigy --help` / https://prodi.gy/docs on the actual installed
version before relying on them.
"""

import os
from datetime import datetime, date

import prodigy

# CONFIRM WITH YOUR PRODIGY VERSION: this is the classic (pre-1.11) import
# path for the stream-loading helper. Prodigy 1.11+ reorganized its CLI
# around the `radicli` library and some loader/helper import paths moved;
# run `python -c "import prodigy.components.loaders as m; print(dir(m))"`
# against the installed version to confirm this still resolves, and check
# https://prodi.gy/docs/api-loaders for the current recommended way to
# stream a folder of audio files (or a JSONL manifest with "audio"/"path"
# keys) into a recipe.
from prodigy.components.loaders import get_stream

from db.models import MarkupSession, get_database

_STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")


def _read_static(*filenames: str) -> str:
    """Concatenate one or more files from static/ into a single string."""
    parts = []
    for name in filenames:
        with open(os.path.join(_STATIC_DIR, name), encoding="utf-8") as f:
            parts.append(f.read())
    return "\n".join(parts)


# CONFIRM WITH YOUR PRODIGY VERSION: this decorator + tuple-based argument
# spec (`(help_text, arg_type, cli_flag, converter)`) is the classic Prodigy
# `@prodigy.recipe(...)` signature used across most published examples and
# plugin recipes as of Prodigy 1.10.x. Prodigy 1.11 introduced a CLI
# rewrite on top of `radicli`, which prefers plain type-hinted function
# signatures with `Arg(...)` markers instead of these tuples in some
# examples. BOTH styles may be accepted depending on exact version/compat
# shims -- confirm which your installed version expects by checking
# `python -m prodigy audio-markup --help` after installing (it should
# print an auto-generated CLI help derived from this signature either way;
# if it errors on the tuple-annotation style, switch to the radicli
# `Arg()` style per https://prodi.gy/docs/custom-recipes).
@prodigy.recipe(
    "audio-markup",
    dataset=("The dataset to save annotations to", "positional", None, str),
    source=("Path to a directory of audio files, or a JSONL manifest", "positional", None, str),
    label=("Comma-separated language labels", "option", "l", str),
)
def audio_markup(dataset: str, source: str, label: str = "kk,ru"):
    """
    Kaspi audio transcription markup recipe.

    Combines an audio block, a free-text transcription block, and a
    language-choice block into one "blocks" view, matching the single-screen
    layout in index.html (player card + transcription card + language
    picker + accept/reject/skip, all in one view). See DEV_HANDOFF.md points
    1-2 and 7 for why the fine-grained player controls, word buffer, and
    custom hotkeys are implemented as a "javascript" hook (static/*.js)
    rather than as changes to Prodigy's own recipe/block internals.
    """
    languages = [code.strip() for code in label.split(",") if code.strip()]

    # CONFIRM WITH YOUR PRODIGY VERSION: `get_stream` with a bare directory
    # path and no explicit `loader=` kwarg is documented to auto-detect the
    # loader from file extensions for common media types, but audio
    # support specifically may require passing `loader="audio"` explicitly,
    # and/or the separate `prodigy-audio` plugin rather than core Prodigy --
    # this is exactly the kind of detail that has moved between versions.
    # Check https://prodi.gy/docs/api-loaders and, if installed, whether
    # `prodigy-audio` is a separate `pip install prodigy-audio` plugin your
    # license includes.
    stream = get_stream(source, loader="audio")

    def add_language_field(example):
        example.setdefault("languages", languages)
        return example

    stream = (add_language_field(eg) for eg in stream)

    def update(examples):
        """
        Prodigy calls `update(examples)` with a batch of newly-answered
        examples (accept/reject/ignore already applied) after every save.
        This is exactly where the "во сколько начал/закончил"
        (start/end-of-day) tracking from index.html's analytics view is
        implemented -- Prodigy does NOT track annotator start/end times or
        a per-day task count out of the box, so this recipe does it
        explicitly by writing to MarkupSession (db/models.py), the one new
        table this project adds. See README.md's "три базы данных" section.

        CONFIRM WITH YOUR PRODIGY VERSION: the `update` callback's exact
        signature (a plain list of example dicts) has been stable across
        recent Prodigy versions and is one of the more confidently-documented
        recipe hooks, but double check against
        https://prodi.gy/docs/custom-recipes#update for the version in use.
        """
        db = get_database()
        db.connect(reuse_if_open=True)
        try:
            for eg in examples:
                # CONFIRM WITH YOUR PRODIGY VERSION: how to identify "who"
                # answered an example is not something core Prodigy exposes
                # uniformly out of the box in single-user local mode -- in
                # Prodigy Teams / multi-annotator setups examples typically
                # carry a `_session_id` or `_annotator_id` field; in plain
                # single-user Prodigy there may be no such field at all.
                # Check what's actually present on `eg` for your setup
                # (`print(eg.keys())`) and adjust this lookup accordingly.
                # os.environ["USER"] is used as a last-resort fallback so
                # this at least does something sensible in the common case
                # of one annotator per machine.
                user = eg.get("_session_id") or eg.get("_annotator_id") or os.environ.get("USER", "unknown")

                today = date.today()
                session, _created = MarkupSession.get_or_create(
                    user=user,
                    project_id=dataset,
                    session_date=today,
                    defaults={"started_at": datetime.utcnow()},
                )
                if session.started_at is None:
                    session.started_at = datetime.utcnow()
                session.ended_at = datetime.utcnow()
                session.tasks_count += 1
                session.save()
        finally:
            db.close()

    blocks = [
        # CONFIRM WITH YOUR PRODIGY VERSION: exact view_id strings are a
        # best guess pending confirmation. "audio" is the block name used
        # in Prodigy's own published audio-annotation examples as of recent
        # versions, but whether it ships in core Prodigy or requires the
        # separate `prodigy-audio` plugin, and whether the field name is
        # "audio" vs something else, needs checking against your version --
        # see https://prodi.gy/docs/api-interfaces#audio (or your plugin's
        # own docs if it's `prodigy-audio`).
        {"view_id": "audio"},
        # CONFIRM WITH YOUR PRODIGY VERSION: "text_input" is a documented
        # core block type; the exact set of supported keys (field_id,
        # field_rows, field_placeholder, field_autofocus) has been fairly
        # stable but confirm against your version's docs at
        # https://prodi.gy/docs/api-interfaces#text_input.
        {
            "view_id": "text_input",
            "field_id": "transcript",
            "field_placeholder": "Начните вводить транскрипцию...",
            "field_rows": 4,
        },
        # CONFIRM WITH YOUR PRODIGY VERSION: "choice" is a documented core
        # block type for single/multi-select options; confirm the exact
        # option-list shape (id/text keys) at
        # https://prodi.gy/docs/api-interfaces#choice.
        {
            "view_id": "choice",
            "text": "Укажите язык",
            "options": [{"id": code, "text": code.upper()} for code in languages],
        },
    ]

    return {
        "dataset": dataset,
        "view_id": "blocks",
        "stream": stream,
        "update": update,
        "config": {
            "blocks": blocks,
            # CONFIRM WITH YOUR PRODIGY VERSION: "global_css" and
            # "javascript" accepting raw string content (as opposed to a
            # file path Prodigy reads itself) is the commonly documented
            # and demonstrated pattern in Prodigy's own custom-interface
            # examples -- this recipe reads static/style.css and
            # concatenates static/*.js into strings and passes those
            # strings, on that assumption. If your installed version
            # instead expects a file PATH for one or both of these keys,
            # swap `_read_static(...)` for the plain path string. Check
            # https://prodi.gy/docs/install#config (global_css/javascript).
            "global_css": _read_static("style.css"),
            "javascript": _read_static("i18n.js", "theme.js", "buffer.js", "player.js"),
            # CONFIRM WITH YOUR PRODIGY VERSION: "keymap" (overriding
            # default accept/reject/ignore keys and adding custom ones) is
            # a documented config key in recent Prodigy versions, but the
            # exact action-name strings it expects (e.g. "accept" vs
            # "accept_button") differ by version/recipe type -- confirm at
            # https://prodi.gy/docs/install#keyboard-shortcuts. Mapped here
            # to mirror index.html's hotkeys modal: F=accept, J=reject,
            # Enter=skip. The Ctrl+Shift+1-9 snippet insertion and D=theme
            # hotkeys are NOT handled here -- those are bound directly in
            # static/buffer.js and static/theme.js instead, since they
            # don't correspond to a core Prodigy action Prodigy's own
            # keymap system would recognize.
            "keymap": {
                "accept": ["f"],
                "reject": ["j"],
                "ignore": ["enter"],
            },
        },
    }
