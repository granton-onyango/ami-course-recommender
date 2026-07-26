"""Unit tests for engine/weighting.py -- blending signals and cold-start
renormalization. This is the single most important function in the engine
(see WRITEUP.md section 3), so it gets the most direct scrutiny here."""

from engine.weighting import combine_signals


def test_combine_signals_weighted_sum_when_all_three_fire():
    signal_scores = {
        "survey": (0.9, "skill gap"),
        "usage": (0.8, "did well before"),
        "work_info": (0.6, "matches goal"),
    }
    score, reason = combine_signals(signal_scores)
    assert score == round(0.9 * 0.4 + 0.8 * 0.4 + 0.6 * 0.2, 2)
    assert "skill gap" in reason


def test_combine_signals_renormalizes_when_one_signal_abstains():
    """A missing signal's weight should be redistributed, not counted as a
    real zero -- otherwise cold-start users get double-punished."""
    signal_scores = {
        "survey": (0.0, None),
        "usage": (0.8, "did well before"),
        "work_info": (0.6, "matches goal"),
    }
    score, _ = combine_signals(signal_scores)
    expected = round((0.8 * 0.4 + 0.6 * 0.2) / (0.4 + 0.2), 2)
    assert score == expected


def test_combine_signals_renormalized_score_beats_treat_as_zero_score():
    """Concrete proof the renormalization policy matters: the same raw
    signals score higher under renormalization than they would under a
    naive treat-missing-as-zero policy."""
    signal_scores = {
        "survey": (0.0, None),
        "usage": (0.8, "did well before"),
        "work_info": (0.6, "matches goal"),
    }
    renormalized_score, _ = combine_signals(signal_scores)
    treat_as_zero_score = round(0.0 * 0.4 + 0.8 * 0.4 + 0.6 * 0.2, 2)
    assert renormalized_score > treat_as_zero_score


def test_combine_signals_total_cold_start_returns_graceful_fallback():
    signal_scores = {"survey": (0.0, None), "usage": (0.0, None), "work_info": (0.0, None)}
    score, reason = combine_signals(signal_scores)
    assert score == 0.0
    assert reason  # a real fallback sentence, not a crash or an empty string


def test_combine_signals_reason_prioritizes_higher_scoring_signal():
    signal_scores = {
        "survey": (0.5, "survey reason"),
        "usage": (0.9, "usage reason"),
        "work_info": (0.0, None),
    }
    _, reason = combine_signals(signal_scores)
    assert reason.index("usage reason") < reason.index("survey reason")
