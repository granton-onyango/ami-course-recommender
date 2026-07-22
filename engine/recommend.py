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
            "usage": signals.usage_signal(course, user_id, usage_events, courses),
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


def get_recommendation_breakdown(
    user_id: str,
    n: int,
    courses: pd.DataFrame,
    users: pd.DataFrame,
    usage_events: pd.DataFrame,
    survey_responses: pd.DataFrame,
) -> dict:
    """Same pipeline as get_recommendations, but keeps every intermediate
    value instead of discarding it, for the UI's debug/breakdown view:
    the user's raw survey answers, how many courses survived each filter
    stage, and each candidate's per-signal scores next to the final
    blended score. A separate function rather than a refactor of
    get_recommendations, so that already-verified path stays untouched."""
    user_matches = users[users["user_id"] == user_id]
    if user_matches.empty:
        raise KeyError(f"unknown user_id: {user_id}")
    user_row = user_matches.iloc[0]

    survey_matches = survey_responses[survey_responses["user_id"] == user_id]
    survey_row = survey_matches.iloc[0] if not survey_matches.empty else None

    survey_answers = None
    if survey_row is not None:
        survey_answers = {
            "skill_gaps": survey_row["skill_gaps"],
            "goals": survey_row["goals"],
            "preferred_topics": survey_row["preferred_topics"],
            "confidence_by_topic": survey_row["confidence_by_topic"],
        }

    completed_ids = filters.get_completed_course_ids(user_id, usage_events)
    after_completed = filters.exclude_completed(courses, completed_ids)
    after_prerequisite = filters.apply_prerequisite_filter(after_completed, user_id, usage_events)
    after_level = filters.apply_level_filter(after_prerequisite, user_row, usage_events, courses)

    filter_funnel = [
        {"stage": "total_catalog", "count": len(courses)},
        {"stage": "exclude_completed", "count": len(after_completed)},
        {"stage": "apply_prerequisite_filter", "count": len(after_prerequisite)},
        {"stage": "apply_level_filter", "count": len(after_level)},
    ]

    scored = []
    for _, course in after_level.iterrows():
        survey_score = signals.survey_signal(course, survey_row)
        usage_score = signals.usage_signal(course, user_id, usage_events, courses)
        work_info_score = signals.work_info_signal(course, user_row)
        final_score, final_reason = weighting.combine_signals(
            {"survey": survey_score, "usage": usage_score, "work_info": work_info_score}
        )

        scored.append({
            "course_id": course["course_id"],
            "title": course["title"],
            "signals": {
                "survey": {"score": survey_score[0], "reason": survey_score[1]},
                "usage": {"score": usage_score[0], "reason": usage_score[1]},
                "work_info": {"score": work_info_score[0], "reason": work_info_score[1]},
            },
            "final_score": final_score,
            "final_reason": final_reason,
        })

    scored.sort(key=lambda c: c["final_score"], reverse=True)
    top_n = scored[:n]
    for rank, item in enumerate(top_n, start=1):
        item["rank"] = rank

    return {
        "user_id": user_id,
        "survey": survey_answers,
        "filter_funnel": filter_funnel,
        "weights": dict(weighting.DEFAULT_WEIGHTS),
        "courses": top_n,
    }
