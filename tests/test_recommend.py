"""Integration tests for engine/recommend.py -- filter -> score -> rank ->
top N, end to end, on a small hand-built dataset rather than the full
generated CSVs."""

import pandas as pd
import pytest

from engine.recommend import get_recommendations


def make_small_dataset():
    courses = pd.DataFrame([
        ["C1", "Intro to Sales", "sales", "beginner", "pitch", 30, ""],
        ["C2", "Intro to Marketing", "marketing", "beginner", "branding", 30, ""],
    ], columns=["course_id", "title", "topic", "level", "skills_taught", "duration_mins", "prerequisites"])

    users = pd.DataFrame([
        ["U1", "Sales Associate", "Retail", "1-10", "entry", "sales"],
    ], columns=["user_id", "role", "industry", "company_size", "seniority", "stated_goal"])

    usage_events = pd.DataFrame(
        columns=["user_id", "course_id", "event_type", "progress_pct", "quiz_score", "timestamp"]
    )
    survey_responses = pd.DataFrame(
        columns=["user_id", "skill_gaps", "goals", "preferred_topics", "confidence_by_topic"]
    )

    return courses, users, usage_events, survey_responses


def test_get_recommendations_raises_keyerror_for_unknown_user():
    courses, users, usage_events, survey_responses = make_small_dataset()
    with pytest.raises(KeyError):
        get_recommendations("NOPE", 5, courses, users, usage_events, survey_responses)


def test_get_recommendations_ranks_matching_topic_first():
    """U1's stated_goal is 'sales' and they have no usage/survey history --
    a true cold-start case, so only work_info can fire. C1 should still
    rank above C2 because it matches the stated goal."""
    courses, users, usage_events, survey_responses = make_small_dataset()
    recs = get_recommendations("U1", 5, courses, users, usage_events, survey_responses)
    assert recs[0]["course_id"] == "C1"
    assert recs[0]["rank"] == 1
    assert recs[0]["score"] > 0.0


def test_get_recommendations_respects_n():
    courses, users, usage_events, survey_responses = make_small_dataset()
    recs = get_recommendations("U1", 1, courses, users, usage_events, survey_responses)
    assert len(recs) == 1
