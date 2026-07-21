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


def survey_signal(course: pd.Series, survey_row: pd.Series | None) -> tuple[float, str | None]:
    """TODO (you implement).

    survey_row has skill_gaps / goals / preferred_topics (semicolon-separated
    tag strings) and confidence_by_topic ("topic:score;topic:score"). course
    has topic and skills_taught (semicolon-separated).

    survey_row is None if this user never filled in the survey -- handle
    that explicitly (return what?), don't let it throw.

    Guidance: reward overlap between the course's topic/skills and the
    user's goals/skill_gaps/preferred_topics. Consider: should a topic in
    skill_gaps count for more than one in preferred_topics? Low
    confidence_by_topic on a topic probably means "recommend the beginner
    course in that topic," not "avoid this topic."
    """
    raise NotImplementedError("survey_signal: implement tag-overlap scoring against survey data")


def usage_signal(
    course: pd.Series, user_id: str, usage_events: pd.DataFrame
) -> tuple[float, str | None]:
    """TODO (you implement).

    usage_events for this user_id (may be empty -- that's the cold-start
    case, capability #2). Columns: course_id, event_type, progress_pct,
    quiz_score, timestamp.

    Guidance: what should count as a positive behavioral signal toward a
    candidate course? E.g. the user completed other courses in the same
    topic with a high quiz_score -> boost the next course in that topic's
    progression. The user dropped courses in a topic -> maybe dampen, or
    maybe that just means the level was wrong (that's apply_level_filter's
    job, not this function's -- keep the concerns separate).

    Empty usage_events should return (0.0, None) or similar -- NOT crash,
    and NOT silently look identical to "actively low interest." The caller
    (engine/weighting.py) is what decides how to treat "no usage data"
    differently from "usage data that scored 0."
    """
    raise NotImplementedError("usage_signal: implement behavior-driven scoring from usage_events")


def work_info_signal(course: pd.Series, user_row: pd.Series) -> tuple[float, str | None]:
    """TODO (you implement).

    user_row has role, industry, company_size, seniority, stated_goal.

    Guidance: this is your weakest signal in terms of data richness (5
    categorical fields vs. rich tag data elsewhere) -- that's fine, it's
    supposed to be a tie-breaker / cold-start floor, not the star. Simple
    ideas: seniority implies an expected level band; stated_goal is
    literally a topic and should overlap-score like a mini survey signal.
    Don't over-engineer this one.
    """
    raise NotImplementedError("work_info_signal: implement role/seniority/goal-based scoring")
