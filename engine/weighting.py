"""
Combine the three signals from engine/signals.py into one score + one reason.

This is where case study capabilities #1 (blend all three, make the
weighting legible) and #2 (cold-start handling) actually get decided. It's
the single most important function in this codebase for the interview --
expect to be asked to justify every number in DEFAULT_WEIGHTS and the
renormalization strategy below.
"""

from __future__ import annotations

from typing import Optional

Signal = tuple[float, Optional[str]]  # (score in [0,1], reason fragment or None)

# Starting point, not a conclusion -- these are unweighted guesses. Your
# WRITEUP.md should say what you'd actually tune these against (e.g. an
# offline eval against held-out completions, or an online experiment -- see
# the "Measuring success" section of WRITEUP.md).
DEFAULT_WEIGHTS = {
    "survey": 0.4,
    "usage": 0.4,
    "work_info": 0.2,
}


def combine_signals(
    signals: dict[str, Signal],
    weights: dict[str, float] = DEFAULT_WEIGHTS,
) -> tuple[float, str]:
    """Weighted blend of the three signals, with renormalization for
    cold-start. A signal with reason=None didn't fire -- by construction in
    engine/signals.py that covers both "no data" and "data but no overlap,"
    so its weight is dropped and redistributed across whichever signals did
    fire, rather than counted as a real zero that would double-punish
    users for missing data. The final reason is built from the 1-2
    highest-scoring signals that fired, not a concatenation of all three.
    """
    priority = list(weights)  # tie-break order when scores are equal
    active = {
        name: signals[name]
        for name in priority
        if name in signals and signals[name][1] is not None
    }

    if not active:
        return (0.0, "We don't have enough information about you yet, so this is a general starting point.")

    active_weight_total = sum(weights[name] for name in active)
    blended_score = sum(
        score * weights[name] for name, (score, _reason) in active.items()
    ) / active_weight_total

    ranked = sorted(active, key=lambda name: (-active[name][0], priority.index(name)))
    top_reasons = [active[name][1] for name in ranked[:2]]

    if len(top_reasons) == 1:
        reason = f"Because {top_reasons[0]}, we suggest this course."
    else:
        reason = f"Because {top_reasons[0]}, and {top_reasons[1]}, we suggest this course."

    return (round(blended_score, 2), reason)
