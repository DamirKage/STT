"""
dashboard/wer_cer.py

WER/CER computation using the `jiwer` library.

# TODO(integration): SELF-CONTAINED FALLBACK, NOT THE REAL INTEGRATION.
# Per the assessors, WER/CER per annotator is apparently already computed
# somewhere in Kaspi's existing pipeline (assessors already see it per
# person) -- this module recomputes it independently from raw
# hypothesis/reference transcription pairs so that the dashboard demo works
# standalone, without depending on internal Kaspi systems this environment
# has no access to. The real integration should almost certainly READ the
# already-computed metrics from wherever that existing pipeline stores them
# (a table, an internal API, ...) instead of recomputing them here -- ask
# the dev team where that lives. See also README.md, "Открытый вопрос:
# WER/CER уже считается в проде".
"""

from dataclasses import dataclass

import jiwer


@dataclass
class WerCerResult:
    wer: float  # word error rate, as a percentage (0-100)
    cer: float  # character error rate, as a percentage (0-100)


def compute_wer_cer(hypothesis: str, reference: str) -> WerCerResult:
    """
    Compute WER/CER for a single hypothesis/reference transcription pair.

    Both are expected to be plain strings in the same language/script.
    Returns percentages (0-100), matching how index.html's analytics view
    displays them (e.g. "5.4%").
    """
    if not reference.strip():
        # jiwer raises on an empty reference; treat as undefined rather
        # than crash the dashboard on bad/missing data.
        return WerCerResult(wer=0.0, cer=0.0)

    wer = jiwer.wer(reference, hypothesis) * 100
    cer = jiwer.cer(reference, hypothesis) * 100
    return WerCerResult(wer=round(wer, 2), cer=round(cer, 2))


def compute_wer_cer_batch(
    hypotheses: list[str], references: list[str]
) -> WerCerResult:
    """
    Aggregate WER/CER across many hypothesis/reference pairs at once
    (jiwer computes this as a single edit-distance ratio over the whole
    batch, not an average of per-example percentages -- this matches how
    WER/CER is conventionally reported for a project/day rather than
    averaging already-averaged numbers).
    """
    if not hypotheses or not references:
        return WerCerResult(wer=0.0, cer=0.0)
    if len(hypotheses) != len(references):
        raise ValueError("hypotheses and references must be the same length")

    wer = jiwer.wer(references, hypotheses) * 100
    cer = jiwer.cer(references, hypotheses) * 100
    return WerCerResult(wer=round(wer, 2), cer=round(cer, 2))
