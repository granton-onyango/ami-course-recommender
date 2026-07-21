"""
Generate synthetic courses / users / usage_events / survey_responses CSVs.

Run from the project root:
    python -m data.generate_data
    python -m data.generate_data --num-users 2000 --seed 7

This is infrastructure, not the part of the case study being evaluated for
recommendation judgment -- but read through it anyway. You need to be able
to explain the shape of your own data (e.g. why ~30% of users have zero
usage_events -- that's your cold-start population) in the follow-up
interview.
"""

import argparse
import csv
import pathlib
import random
import sys
from datetime import datetime, timedelta

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from taxonomy import (  # noqa: E402
    COMPANY_SIZES,
    INDUSTRIES,
    LEVELS,
    ROLES,
    SENIORITY,
    TOPIC_DISPLAY,
    TOPIC_SKILLS,
    TOPICS,
)

DATA_DIR = ROOT / "data"

LEVEL_PREFIXES = {
    "beginner": ["Intro to", "Fundamentals of", "Getting Started with"],
    "intermediate": ["Applied", "Practical", "Building Skills in"],
    "advanced": ["Advanced", "Mastering", "Strategic"],
}

COURSES_PER_TOPIC = {"beginner": 6, "intermediate": 5, "advanced": 5}


def make_title(topic: str, level: str, n: int) -> str:
    prefixes = LEVEL_PREFIXES[level]
    prefix = prefixes[n % len(prefixes)]
    suffix = "" if n < len(prefixes) else f" {n // len(prefixes) + 1}"
    return f"{prefix} {TOPIC_DISPLAY[topic]}{suffix}"


def generate_courses(rng: random.Random) -> list[dict]:
    courses = []
    course_idx = 1
    # topic -> level -> [course_id, ...], so intermediate/advanced courses
    # can pick a real prerequisite from the level below in the same topic.
    by_topic_level: dict[str, dict[str, list[str]]] = {t: {lvl: [] for lvl in LEVELS} for t in TOPICS}

    for topic in TOPICS:
        for level in LEVELS:
            for n in range(COURSES_PER_TOPIC[level]):
                course_id = f"C{course_idx:04d}"
                course_idx += 1

                prerequisite = ""
                if level == "intermediate" and by_topic_level[topic]["beginner"]:
                    prerequisite = rng.choice(by_topic_level[topic]["beginner"])
                elif level == "advanced" and by_topic_level[topic]["intermediate"]:
                    prerequisite = rng.choice(by_topic_level[topic]["intermediate"])

                skills = rng.sample(TOPIC_SKILLS[topic], k=rng.randint(2, len(TOPIC_SKILLS[topic])))

                courses.append({
                    "course_id": course_id,
                    "title": make_title(topic, level, n),
                    "topic": topic,
                    "level": level,
                    "skills_taught": ";".join(skills),
                    "duration_mins": rng.choice(range(20, 181, 10)),
                    "prerequisites": prerequisite,
                })
                by_topic_level[topic][level].append(course_id)

    return courses


def generate_users(rng: random.Random, num_users: int) -> list[dict]:
    users = []
    for i in range(1, num_users + 1):
        users.append({
            "user_id": f"U{i:05d}",
            "role": rng.choice(ROLES),
            "industry": rng.choice(INDUSTRIES),
            "company_size": rng.choice(COMPANY_SIZES),
            "seniority": rng.choice(SENIORITY),
            "stated_goal": rng.choice(TOPICS),
        })
    return users


def generate_survey_responses(rng: random.Random, users: list[dict]) -> list[dict]:
    """~90% of users filled in the onboarding survey; ~10% didn't. Your
    engine has to degrade gracefully for that missing 10%, same as it does
    for users with zero usage_events."""
    responses = []
    for user in users:
        if rng.random() > 0.90:
            continue

        goal_topic = user["stated_goal"]
        skill_gaps = {goal_topic, *rng.sample(TOPICS, k=rng.randint(0, 2))}
        goals = {goal_topic, *rng.sample(TOPICS, k=rng.randint(0, 1))}
        preferred_topics = {goal_topic, *rng.sample(TOPICS, k=rng.randint(1, 2))}

        confidence_topics = rng.sample(TOPICS, k=rng.randint(3, 5))
        confidence_by_topic = ";".join(f"{t}:{rng.randint(1, 5)}" for t in confidence_topics)

        responses.append({
            "user_id": user["user_id"],
            "skill_gaps": ";".join(skill_gaps),
            "goals": ";".join(goals),
            "preferred_topics": ";".join(preferred_topics),
            "confidence_by_topic": confidence_by_topic,
        })
    return responses


def generate_usage_events(rng: random.Random, users: list[dict], courses: list[dict]) -> list[dict]:
    """~30% of users are true cold-start (zero events), ~40% light usage,
    ~30% heavy usage. Events lean toward the user's stated_goal topic so
    there's an actual behavioral signal for engine/signals.py to find."""
    events = []
    courses_by_topic: dict[str, list[dict]] = {t: [] for t in TOPICS}
    for c in courses:
        courses_by_topic[c["topic"]].append(c)

    now = datetime.now()

    for user in users:
        tier_roll = rng.random()
        if tier_roll < 0.30:
            num_events = 0
        elif tier_roll < 0.70:
            num_events = rng.randint(1, 4)
        else:
            num_events = rng.randint(5, 15)

        for _ in range(num_events):
            if rng.random() < 0.6:
                topic = user["stated_goal"]
            else:
                topic = rng.choice(TOPICS)
            course = rng.choice(courses_by_topic[topic])

            event_type = rng.choices(
                ["started", "completed", "dropped"], weights=[30, 50, 20], k=1
            )[0]

            if event_type == "completed":
                progress_pct = 100
                quiz_score = rng.randint(40, 100)
            elif event_type == "dropped":
                progress_pct = rng.randint(5, 70)
                quiz_score = ""
            else:
                progress_pct = rng.randint(10, 90)
                quiz_score = ""

            timestamp = now - timedelta(days=rng.randint(0, 180), hours=rng.randint(0, 23))

            events.append({
                "user_id": user["user_id"],
                "course_id": course["course_id"],
                "event_type": event_type,
                "progress_pct": progress_pct,
                "quiz_score": quiz_score,
                "timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%S"),
            })

    return events


def write_csv(path: pathlib.Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  wrote {len(rows):>6} rows -> {path.relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--num-users", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = random.Random(args.seed)

    courses = generate_courses(rng)
    users = generate_users(rng, args.num_users)
    survey_responses = generate_survey_responses(rng, users)
    usage_events = generate_usage_events(rng, users, courses)

    print(f"Generating synthetic data (seed={args.seed})")
    write_csv(DATA_DIR / "courses.csv", courses,
              ["course_id", "title", "topic", "level", "skills_taught", "duration_mins", "prerequisites"])
    write_csv(DATA_DIR / "users.csv", users,
              ["user_id", "role", "industry", "company_size", "seniority", "stated_goal"])
    write_csv(DATA_DIR / "survey_responses.csv", survey_responses,
              ["user_id", "skill_gaps", "goals", "preferred_topics", "confidence_by_topic"])
    write_csv(DATA_DIR / "usage_events.csv", usage_events,
              ["user_id", "course_id", "event_type", "progress_pct", "quiz_score", "timestamp"])

    no_survey = args.num_users - len(survey_responses)
    print(f"\n{no_survey} users have no survey response (missing-data edge case).")
    print("Usage tiers are randomized per user -- some have 0 events (cold-start),")
    print("check usage_events.csv grouped by user_id if you need exact counts.")


if __name__ == "__main__":
    main()
