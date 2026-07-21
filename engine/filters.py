"""
Candidate filtering: shrink the full course catalog down to courses that are
even eligible to recommend, before any scoring happens.

Case study capability #3 ("Sensible filtering") lives here.
"""

import pandas as pd

from taxonomy import LEVELS

SENIORITY_LEVEL_CAP = {
    "entry": "beginner",
    "mid": "intermediate",
    "senior": "advanced",
    "executive": "advanced",
}


def get_completed_course_ids(user_id: str, usage_events: pd.DataFrame) -> set[str]:
    """Fully implemented -- mechanical, not a judgment call.

    Courses this user has a 'completed' event for.
    """
    completed = usage_events[
        (usage_events["user_id"] == user_id) & (usage_events["event_type"] == "completed")
    ]
    return set(completed["course_id"])


def exclude_completed(courses: pd.DataFrame, completed_course_ids: set[str]) -> pd.DataFrame:
    """Fully implemented. Never recommend a course the user already finished."""
    return courses[~courses["course_id"].isin(completed_course_ids)]


def apply_prerequisite_filter(
    candidates: pd.DataFrame, user_id: str, usage_events: pd.DataFrame
) -> pd.DataFrame:
    """Hard filter. A course with a prerequisite is only shown once that
    prerequisite has a 'completed' event -- 'started', however far along,
    doesn't count. Courses with no prerequisite ("") always pass."""
    completed = get_completed_course_ids(user_id, usage_events)
    no_prerequisite = candidates["prerequisites"] == ""
    prerequisite_met = candidates["prerequisites"].isin(completed)
    return candidates[no_prerequisite | prerequisite_met]


def apply_level_filter(
    candidates: pd.DataFrame,
    user_row: pd.Series,
    usage_events: pd.DataFrame,
    courses: pd.DataFrame,
) -> pd.DataFrame:
    """Hard filter. Within a topic, a course at level L is only shown once
    the user has completed a course one level below L in that same topic
    (e.g. one completed 'beginner' unlocks 'intermediate'). For a topic
    where the user has zero completions, there's no behavioral signal to
    check, so fall back to a cap implied by their seniority (SENIORITY_LEVEL_CAP)
    instead of either blocking everything or letting everything through."""
    level_rank = {level: i for i, level in enumerate(LEVELS)}

    completed_ids = get_completed_course_ids(user_row["user_id"], usage_events)
    completed_courses = courses[courses["course_id"].isin(completed_ids)]
    topic_max_rank = completed_courses.groupby("topic")["level"].apply(
        lambda levels: max(level_rank[level] for level in levels)
    ).to_dict()

    seniority_cap_rank = level_rank[SENIORITY_LEVEL_CAP.get(user_row["seniority"], "beginner")]

    def is_allowed(row) -> bool:
        if row["topic"] in topic_max_rank:
            max_rank = min(topic_max_rank[row["topic"]] + 1, len(LEVELS) - 1)
        else:
            max_rank = seniority_cap_rank
        return level_rank[row["level"]] <= max_rank

    return candidates[candidates.apply(is_allowed, axis=1)]
