"""Unit tests for engine/filters.py -- the hard eligibility gates.

Each test builds a tiny, hand-crafted table instead of loading the full
generated data/*.csv, so it's obvious from the test itself exactly what
data goes in and why a given result is expected.
"""

import pandas as pd

from engine import filters

COURSE_COLUMNS = ["course_id", "title", "topic", "level", "skills_taught", "duration_mins", "prerequisites"]
USAGE_COLUMNS = ["user_id", "course_id", "event_type", "progress_pct", "quiz_score", "timestamp"]


def make_courses(rows):
    return pd.DataFrame(rows, columns=COURSE_COLUMNS)


def make_usage_events(rows):
    return pd.DataFrame(rows, columns=USAGE_COLUMNS)


def test_get_completed_course_ids_only_counts_completed_events():
    usage = make_usage_events([
        ["U1", "C1", "completed", 100, "90", "2026-01-01T00:00:00"],
        ["U1", "C2", "started", 40, "", "2026-01-02T00:00:00"],
        ["U1", "C3", "dropped", 20, "", "2026-01-03T00:00:00"],
        ["U2", "C1", "completed", 100, "80", "2026-01-01T00:00:00"],  # different user
    ])
    assert filters.get_completed_course_ids("U1", usage) == {"C1"}


def test_exclude_completed_removes_only_completed_courses():
    courses = make_courses([
        ["C1", "Intro to Sales", "sales", "beginner", "pitch", 30, ""],
        ["C2", "Intro to Marketing", "marketing", "beginner", "branding", 30, ""],
    ])
    result = filters.exclude_completed(courses, {"C1"})
    assert list(result["course_id"]) == ["C2"]


def test_prerequisite_filter_blocks_unmet_prerequisite():
    candidates = make_courses([
        ["C2", "Applied Sales", "sales", "intermediate", "closing", 40, "C1"],
    ])
    usage = make_usage_events([])  # C1 never completed
    result = filters.apply_prerequisite_filter(candidates, "U1", usage)
    assert result.empty


def test_prerequisite_filter_allows_met_prerequisite():
    candidates = make_courses([
        ["C2", "Applied Sales", "sales", "intermediate", "closing", 40, "C1"],
    ])
    usage = make_usage_events([
        ["U1", "C1", "completed", 100, "90", "2026-01-01T00:00:00"],
    ])
    result = filters.apply_prerequisite_filter(candidates, "U1", usage)
    assert list(result["course_id"]) == ["C2"]


def test_prerequisite_filter_started_but_not_completed_still_blocks():
    """'started' at high progress does NOT satisfy a prerequisite -- only
    'completed' counts, per the hard-block policy chosen in engine/filters.py."""
    candidates = make_courses([
        ["C2", "Applied Sales", "sales", "intermediate", "closing", 40, "C1"],
    ])
    usage = make_usage_events([
        ["U1", "C1", "started", 95, "", "2026-01-01T00:00:00"],
    ])
    result = filters.apply_prerequisite_filter(candidates, "U1", usage)
    assert result.empty


def test_prerequisite_filter_allows_courses_with_no_prerequisite():
    candidates = make_courses([
        ["C1", "Intro to Sales", "sales", "beginner", "pitch", 30, ""],
    ])
    usage = make_usage_events([])
    result = filters.apply_prerequisite_filter(candidates, "U1", usage)
    assert list(result["course_id"]) == ["C1"]


def test_level_filter_caps_cold_start_entry_user_to_beginner():
    courses = make_courses([
        ["C1", "Intro to Sales", "sales", "beginner", "pitch", 30, ""],
        ["C2", "Applied Sales", "sales", "intermediate", "closing", 40, "C1"],
    ])
    usage = make_usage_events([])  # zero history anywhere -- true cold start
    user_row = pd.Series({"user_id": "U1", "seniority": "entry"})
    result = filters.apply_level_filter(courses, user_row, usage, courses)
    assert list(result["course_id"]) == ["C1"]


def test_level_filter_unlocks_next_level_after_completion():
    courses = make_courses([
        ["C1", "Intro to Sales", "sales", "beginner", "pitch", 30, ""],
        ["C2", "Applied Sales", "sales", "intermediate", "closing", 40, "C1"],
        ["C3", "Advanced Sales", "sales", "advanced", "negotiation", 50, "C2"],
    ])
    candidates = courses[courses["course_id"] != "C1"]  # already completed, filtered out upstream
    usage = make_usage_events([
        ["U1", "C1", "completed", 100, "90", "2026-01-01T00:00:00"],
    ])
    user_row = pd.Series({"user_id": "U1", "seniority": "entry"})
    result = filters.apply_level_filter(candidates, user_row, usage, courses)
    # completed a beginner course in this topic -> intermediate unlocked, advanced still isn't
    assert list(result["course_id"]) == ["C2"]


def test_level_filter_senior_seniority_gets_full_range_with_no_history():
    courses = make_courses([
        ["C1", "Intro to Sales", "sales", "beginner", "pitch", 30, ""],
        ["C2", "Applied Sales", "sales", "intermediate", "closing", 40, ""],
        ["C3", "Advanced Sales", "sales", "advanced", "negotiation", 50, ""],
    ])
    usage = make_usage_events([])
    user_row = pd.Series({"user_id": "U1", "seniority": "senior"})
    result = filters.apply_level_filter(courses, user_row, usage, courses)
    assert set(result["course_id"]) == {"C1", "C2", "C3"}
