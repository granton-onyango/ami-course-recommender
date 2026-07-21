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
    """TODO (you implement).

    `signals` is e.g. {"survey": (0.8, "..."), "usage": (0.0, None),
    "work_info": (0.3, "...")}.

    Two decisions to make explicitly (don't let them happen by accident):

    1. Cold start / missing data: if a signal's reason is None (the signal
       didn't fire -- e.g. no usage_events, no survey_response), does its
       weight silently vanish (mass moves to the other signals via
       renormalization), or does it count as a real 0 (penalizing the
       user for missing data)? These give very different results for a
       brand-new user. The case study explicitly asks how you handle the
       cold-start -> behavior-driven transition -- this is where you answer
       that, in code, not just in prose.

    2. Reason string: build ONE human-readable sentence from whichever
       signal(s) contributed most, e.g. "Because you told us you want to
       improve at financial planning and finished Intro to Bookkeeping, we
       suggest...". Don't just concatenate all three reason fragments --
       pick the strongest 1-2 and make it read like a sentence, per the
       case study's own example in section 1.
    """
    raise NotImplementedError("combine_signals: implement weighting + cold-start renormalization")
