"""
Candidate filtering: shrink the full course catalog down to courses that are
even eligible to recommend, before any scoring happens.

Case study capability #3 ("Sensible filtering") lives here.
"""

import pandas as pd


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
    """TODO (you implement).

    `candidates["prerequisites"]` holds a course_id string, or "" if there's
    no prerequisite. Decide:
      - Hard-block a course if its prerequisite hasn't been completed? Or
        allow it through with a lower score / caveat in the reason?
      - What counts as "satisfied" -- only 'completed', or does 'started'
        with high progress_pct count too?

    There's no single right answer -- pick one, and be ready to defend it.
    `get_completed_course_ids()` above is probably useful here.
    """
    raise NotImplementedError("apply_prerequisite_filter: implement your prerequisite policy")


def apply_level_filter(
    candidates: pd.DataFrame, user_row: pd.Series, usage_events: pd.DataFrame
) -> pd.DataFrame:
    """TODO (you implement).

    This is directly the bug scenario the AMI interview asks about:
    "A program manager says entry-level users are getting advanced courses.
    How would you debug and fix that?"

    Decide: hard filter (never show 'advanced' to a user with no completed
    intermediate courses in that topic) vs. soft penalty (let it through but
    score it lower)? A hard filter is easier to defend and debug; a soft
    penalty is more flexible but can still let bad recommendations slip to
    the top if other signals are strong enough. State your choice in
    WRITEUP.md -- the interview will probe exactly this tradeoff.
    """
    raise NotImplementedError("apply_level_filter: implement your level-appropriateness policy")
