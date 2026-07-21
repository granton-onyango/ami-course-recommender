"""
Orchestration glue: filter -> score -> rank -> top N. This wiring is
mechanical and fully implemented -- your judgment goes into filters.py,
signals.py, and weighting.py, all of which this calls and none of which
work yet until you implement them.
"""

import pandas as pd

from engine import filters, signals, weighting


def get_recommendations(
    user_id: str,
    n: int,
    courses: pd.DataFrame,
    users: pd.DataFrame,
    usage_events: pd.DataFrame,
    survey_responses: pd.DataFrame,
) -> list[dict]:
    user_matches = users[users["user_id"] == user_id]
    if user_matches.empty:
        raise KeyError(f"unknown user_id: {user_id}")
    user_row = user_matches.iloc[0]

    survey_matches = survey_responses[survey_responses["user_id"] == user_id]
    survey_row = survey_matches.iloc[0] if not survey_matches.empty else None

    completed_ids = filters.get_completed_course_ids(user_id, usage_events)
    candidates = filters.exclude_completed(courses, completed_ids)
    candidates = filters.apply_prerequisite_filter(candidates, user_id, usage_events)
    candidates = filters.apply_level_filter(candidates, user_row, usage_events, courses)

    scored = []
    for _, course in candidates.iterrows():
        signal_scores = {
            "survey": signals.survey_signal(course, survey_row),
            "usage": signals.usage_signal(course, user_id, usage_events),
            "work_info": signals.work_info_signal(course, user_row),
        }
        score, reason = weighting.combine_signals(signal_scores)
        scored.append({
            "course_id": course["course_id"],
            "title": course["title"],
            "score": score,
            "reason": reason,
        })

    scored.sort(key=lambda r: r["score"], reverse=True)

    top_n = scored[:n]
    for rank, item in enumerate(top_n, start=1):
        item["rank"] = rank

    return top_n
