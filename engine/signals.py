"""
The three signal sources the case study requires you to blend (capability #1):
survey, usage (behavior), and work info. Each function scores ONE course for
ONE user against ONE signal, on a 0.0-1.0 scale, and returns a short
human-readable reason fragment explaining that score (or None if the signal
didn't fire for this course/user pair).

Keeping these three functions separate and pure (no shared mutable state,
no side effects) is what makes engine/weighting.py able to blend them --
and what makes each one independently testable and explainable, which is
capability #4. Don't collapse them into one big function.
"""

from __future__ import annotations

import pandas as pd

from engine.filters import SENIORITY_LEVEL_CAP
from taxonomy import TOPIC_DISPLAY


def survey_signal(course: pd.Series, survey_row: pd.Series | None) -> tuple[float, str | None]:
    """Topic-overlap scoring against the onboarding survey. skill_gaps /
    goals / preferred_topics are all topic-level tags in this data (not
    individual skills), so the overlap check is topic vs topic, weighted by
    how strong a signal each field is: an explicit skill gap counts for
    more than a general preference. Low confidence_by_topic nudges toward
    the beginner course in that topic, it doesn't rule the topic out."""
    if survey_row is None:
        return (0.0, None)

    topic = course["topic"]
    skill_gaps = set(survey_row["skill_gaps"].split(";"))
    goals = set(survey_row["goals"].split(";"))
    preferred_topics = set(survey_row["preferred_topics"].split(";"))

    confidence_by_topic = {}
    if survey_row["confidence_by_topic"]:
        for pair in survey_row["confidence_by_topic"].split(";"):
            conf_topic, conf_score = pair.split(":")
            confidence_by_topic[conf_topic] = int(conf_score)

    score = 0.0
    matched_fields = []  # in priority order: strongest signal first

    if topic in skill_gaps:
        score += 0.45
        matched_fields.append("skill_gaps")
    if topic in goals:
        score += 0.30
        matched_fields.append("goals")
    if topic in preferred_topics:
        score += 0.15
        matched_fields.append("preferred_topics")

    low_confidence_beginner = (
        topic in confidence_by_topic
        and confidence_by_topic[topic] <= 2
        and course["level"] == "beginner"
    )
    if low_confidence_beginner:
        score += 0.10

    if not matched_fields and not low_confidence_beginner:
        return (0.0, None)

    display = TOPIC_DISPLAY[topic]
    if matched_fields:
        strongest = matched_fields[0]
        reason = {
            "skill_gaps": f"you told us {display} is a skill gap",
            "goals": f"improving at {display} is one of your stated goals",
            "preferred_topics": f"you marked {display} as a topic you're interested in",
        }[strongest]
    else:
        reason = f"you rated your confidence in {display} low, so we're starting you at the beginner level"

    return (min(score, 1.0), reason)


def usage_signal(
    course: pd.Series, user_id: str, usage_events: pd.DataFrame, courses: pd.DataFrame
) -> tuple[float, str | None]:
    """Behavior-driven scoring. Rewards having completed other courses in
    this same topic, more so if quiz scores were good. usage_events has no
    topic column, so `courses` is needed here to look up which topic each
    past course_id belongs to. Dropped courses are deliberately ignored --
    a drop might mean "wrong level," which is apply_level_filter's call to
    make, not this function's. No usage_events at all (cold-start) or no
    history in this specific topic both return (0.0, None), same as any
    other signal that didn't fire."""
    user_events = usage_events[usage_events["user_id"] == user_id]
    if user_events.empty:
        return (0.0, None)

    topic = course["topic"]
    topic_by_course_id = courses.set_index("course_id")["topic"]
    same_topic = user_events[user_events["course_id"].map(topic_by_course_id) == topic]
    if same_topic.empty:
        return (0.0, None)

    completed = same_topic[same_topic["event_type"] == "completed"]
    if completed.empty:
        return (0.0, None)

    display = TOPIC_DISPLAY[topic]
    quiz_scores = completed.loc[completed["quiz_score"] != "", "quiz_score"].astype(int)
    if not quiz_scores.empty and quiz_scores.mean() >= 70:
        return (0.8, f"you did well in other {display} courses")
    return (0.5, f"you've completed other {display} courses")


def work_info_signal(course: pd.Series, user_row: pd.Series) -> tuple[float, str | None]:
    """Tie-breaker signal from the 5 categorical work-info fields.
    stated_goal is literally a topic, so it overlap-scores like a mini
    survey signal. seniority implies an expected level band -- reusing
    SENIORITY_LEVEL_CAP from filters.py rather than redeclaring the same
    mapping a second time (see taxonomy.py for why that matters)."""
    topic = course["topic"]
    score = 0.0
    reason = None

    if user_row["stated_goal"] == topic:
        score += 0.6
        reason = f"this matches your stated goal of {TOPIC_DISPLAY[topic]}"

    expected_level = SENIORITY_LEVEL_CAP.get(user_row["seniority"])
    if expected_level == course["level"]:
        score += 0.4
        if reason is None:
            reason = "this level fits where someone at your seniority typically starts"

    if score == 0.0:
        return (0.0, None)
    return (min(score, 1.0), reason)
