# Sample Output

Real responses from `GET /users/{user_id}/recommendations?n=5`, generated
with `python -m data.generate_data` (seed=42, 1,000 users). One user per
usage tier, per the case study's deliverables checklist.

## Cold-start user (no usage_events)

`user_id`: U00005 -- zero usage_events and no survey_response. The only
signal that fires is work_info (stated_goal matches the topic), which is
exactly the tie-breaker / cold-start floor it's meant to be.

```json
{
  "user_id": "U00005",
  "recommendations": [
    {
      "course_id": "C0129",
      "title": "Intro to Strategy",
      "score": 0.6,
      "reason": "Because this matches your stated goal of Strategy, we suggest this course.",
      "rank": 1
    },
    {
      "course_id": "C0130",
      "title": "Fundamentals of Strategy",
      "score": 0.6,
      "reason": "Because this matches your stated goal of Strategy, we suggest this course.",
      "rank": 2
    },
    {
      "course_id": "C0131",
      "title": "Getting Started with Strategy",
      "score": 0.6,
      "reason": "Because this matches your stated goal of Strategy, we suggest this course.",
      "rank": 3
    },
    {
      "course_id": "C0132",
      "title": "Intro to Strategy 2",
      "score": 0.6,
      "reason": "Because this matches your stated goal of Strategy, we suggest this course.",
      "rank": 4
    },
    {
      "course_id": "C0133",
      "title": "Fundamentals of Strategy 2",
      "score": 0.6,
      "reason": "Because this matches your stated goal of Strategy, we suggest this course.",
      "rank": 5
    }
  ]
}
```

## Mid-usage user

`user_id`: U00001 -- 4 usage_events, has a survey_response. usage_signal
fires (completed other Bookkeeping courses with a good quiz average);
survey didn't overlap with this particular topic for this user.

```json
{
  "user_id": "U00001",
  "recommendations": [
    {
      "course_id": "C0018",
      "title": "Fundamentals of Bookkeeping",
      "score": 0.8,
      "reason": "Because you did well in other Bookkeeping courses, we suggest this course.",
      "rank": 1
    },
    {
      "course_id": "C0019",
      "title": "Getting Started with Bookkeeping",
      "score": 0.8,
      "reason": "Because you did well in other Bookkeeping courses, we suggest this course.",
      "rank": 2
    },
    {
      "course_id": "C0020",
      "title": "Intro to Bookkeeping 2",
      "score": 0.8,
      "reason": "Because you did well in other Bookkeeping courses, we suggest this course.",
      "rank": 3
    },
    {
      "course_id": "C0021",
      "title": "Fundamentals of Bookkeeping 2",
      "score": 0.8,
      "reason": "Because you did well in other Bookkeeping courses, we suggest this course.",
      "rank": 4
    },
    {
      "course_id": "C0022",
      "title": "Getting Started with Bookkeeping 2",
      "score": 0.8,
      "reason": "Because you did well in other Bookkeeping courses, we suggest this course.",
      "rank": 5
    }
  ]
}
```

## Heavy-usage user

`user_id`: U00012 -- 11 usage_events, has a survey_response. Both survey
and usage fire and agree on the same topic (Financial Planning), so the
reason cites both.

```json
{
  "user_id": "U00012",
  "recommendations": [
    {
      "course_id": "C0001",
      "title": "Intro to Financial Planning",
      "score": 0.8,
      "reason": "Because you told us Financial Planning is a skill gap, and you did well in other Financial Planning courses, we suggest this course.",
      "rank": 1
    },
    {
      "course_id": "C0003",
      "title": "Getting Started with Financial Planning",
      "score": 0.8,
      "reason": "Because you told us Financial Planning is a skill gap, and you did well in other Financial Planning courses, we suggest this course.",
      "rank": 2
    },
    {
      "course_id": "C0004",
      "title": "Intro to Financial Planning 2",
      "score": 0.8,
      "reason": "Because you told us Financial Planning is a skill gap, and you did well in other Financial Planning courses, we suggest this course.",
      "rank": 3
    },
    {
      "course_id": "C0005",
      "title": "Fundamentals of Financial Planning 2",
      "score": 0.8,
      "reason": "Because you told us Financial Planning is a skill gap, and you did well in other Financial Planning courses, we suggest this course.",
      "rank": 4
    },
    {
      "course_id": "C0006",
      "title": "Getting Started with Financial Planning 2",
      "score": 0.8,
      "reason": "Because you told us Financial Planning is a skill gap, and you did well in other Financial Planning courses, we suggest this course.",
      "rank": 5
    }
  ]
}
```

## Observation worth noting

All three users get top-5 lists that are near-duplicate courses in a
single topic, tied at the same score. That's a direct consequence of how
little the current signals differentiate between courses that share a
topic and level (e.g. "Intro to X" vs "Fundamentals of X") -- worth
naming as a known limitation in WRITEUP.md rather than something to hide.
