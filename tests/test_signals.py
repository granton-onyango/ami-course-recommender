"""Unit tests for engine/signals.py -- the three independent scoring functions."""

import pandas as pd

from engine import signals

COURSE_COLUMNS = ["course_id", "title", "topic", "level", "skills_taught", "duration_mins", "prerequisites"]
USAGE_COLUMNS = ["user_id", "course_id", "event_type", "progress_pct", "quiz_score", "timestamp"]


def make_course(course_id="C1", title="Intro to Sales", topic="sales", level="beginner"):
    return pd.Series({
        "course_id": course_id, "title": title, "topic": topic, "level": level,
        "skills_taught": "pitch", "duration_mins": 30, "prerequisites": "",
    })


def make_courses_table(rows):
    return pd.DataFrame(rows, columns=COURSE_COLUMNS)


def make_usage_events(rows):
    return pd.DataFrame(rows, columns=USAGE_COLUMNS)


# --- survey_signal ---

def test_survey_signal_returns_zero_none_when_no_survey():
    course = make_course()
    assert signals.survey_signal(course, None) == (0.0, None)


def test_survey_signal_scores_skill_gap_higher_than_preferred_topic_only():
    course = make_course(topic="sales")
    skill_gap_row = pd.Series({
        "skill_gaps": "sales", "goals": "marketing", "preferred_topics": "marketing",
        "confidence_by_topic": "",
    })
    preferred_only_row = pd.Series({
        "skill_gaps": "marketing", "goals": "marketing", "preferred_topics": "sales",
        "confidence_by_topic": "",
    })
    gap_score, _ = signals.survey_signal(course, skill_gap_row)
    pref_score, _ = signals.survey_signal(course, preferred_only_row)
    assert gap_score > pref_score


def test_survey_signal_no_overlap_returns_zero_none():
    course = make_course(topic="sales")
    survey_row = pd.Series({
        "skill_gaps": "marketing", "goals": "marketing", "preferred_topics": "marketing",
        "confidence_by_topic": "",
    })
    assert signals.survey_signal(course, survey_row) == (0.0, None)


# --- usage_signal ---

def test_usage_signal_empty_usage_events_returns_zero_none():
    course = make_course()
    courses_table = make_courses_table([list(course)])
    usage = make_usage_events([])
    assert signals.usage_signal(course, "U1", usage, courses_table) == (0.0, None)


def test_usage_signal_rewards_completed_courses_in_same_topic():
    course = make_course(course_id="C2", topic="sales", level="intermediate")
    courses_table = make_courses_table([
        ["C1", "Intro to Sales", "sales", "beginner", "pitch", 30, ""],
        ["C2", "Applied Sales", "sales", "intermediate", "closing", 40, "C1"],
    ])
    usage = make_usage_events([
        ["U1", "C1", "completed", 100, "95", "2026-01-01T00:00:00"],
    ])
    score, reason = signals.usage_signal(course, "U1", usage, courses_table)
    assert score > 0.0
    assert reason is not None


def test_usage_signal_high_quiz_score_beats_low_quiz_score():
    course = make_course(course_id="C2", topic="sales", level="intermediate")
    courses_table = make_courses_table([
        ["C1", "Intro to Sales", "sales", "beginner", "pitch", 30, ""],
        ["C2", "Applied Sales", "sales", "intermediate", "closing", 40, "C1"],
    ])
    high_quiz_usage = make_usage_events([
        ["U1", "C1", "completed", 100, "95", "2026-01-01T00:00:00"],
    ])
    low_quiz_usage = make_usage_events([
        ["U1", "C1", "completed", 100, "40", "2026-01-01T00:00:00"],
    ])
    high_score, _ = signals.usage_signal(course, "U1", high_quiz_usage, courses_table)
    low_score, _ = signals.usage_signal(course, "U1", low_quiz_usage, courses_table)
    assert high_score > low_score


def test_usage_signal_ignores_completions_in_other_topics():
    course = make_course(course_id="C2", topic="sales", level="intermediate")
    courses_table = make_courses_table([
        ["C1", "Intro to Marketing", "marketing", "beginner", "branding", 30, ""],
        ["C2", "Applied Sales", "sales", "intermediate", "closing", 40, ""],
    ])
    usage = make_usage_events([
        ["U1", "C1", "completed", 100, "95", "2026-01-01T00:00:00"],
    ])
    assert signals.usage_signal(course, "U1", usage, courses_table) == (0.0, None)


# --- work_info_signal ---

def test_work_info_signal_matches_stated_goal():
    course = make_course(topic="sales", level="beginner")
    user_row = pd.Series({
        "role": "Sales Associate", "industry": "Retail", "company_size": "1-10",
        "seniority": "entry", "stated_goal": "sales",
    })
    score, reason = signals.work_info_signal(course, user_row)
    assert score > 0.0
    assert reason is not None


def test_work_info_signal_no_match_returns_zero_none():
    course = make_course(topic="sales", level="advanced")
    user_row = pd.Series({
        "role": "Analyst", "industry": "Retail", "company_size": "1-10",
        "seniority": "entry", "stated_goal": "marketing",
    })
    assert signals.work_info_signal(course, user_row) == (0.0, None)
