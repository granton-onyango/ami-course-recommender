# AMI Course Recommendation Engine

Explainable course recommendations for the AI Coach Bot — given a user,
returns the top N recommended courses, each with a rank, a score, and a
specific human-readable reason.

See [ARCHITECTURE.md](ARCHITECTURE.md) for how the pieces fit together and
why, and [WRITEUP.md](WRITEUP.md) for the design writeup.

## Install & run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python -m data.generate_data      # writes data/*.csv (~200 courses, ~1,000 users)
uvicorn api.main:app --reload
```

## Example request/response

```bash
curl "http://127.0.0.1:8000/users/U00001/recommendations?n=5"
```

```json
{
  "user_id": "U00001",
  "recommendations": [
    {
      "rank": 1,
      "course_id": "C0007",
      "title": "Intro to Bookkeeping",
      "score": 0.82,
      "reason": "Because you told us you want to improve at financial planning and haven't started a bookkeeping course yet, we suggest this."
    }
  ]
}
```

<!-- TODO once the engine is implemented: replace the above with a real
captured response, and paste outputs for 3 users into samples/sample_output.md
(one cold-start, one heavy-usage, one in between) per the case study's
deliverables checklist. -->

## Project structure

```
.
├── README.md
├── requirements.txt
├── taxonomy.py              shared topic/level/skill vocabulary (single source of truth)
├── api/
│   ├── __init__.py
│   ├── main.py              FastAPI app, GET /users/{user_id}/recommendations
│   └── models.py
├── data/
│   ├── __init__.py
│   ├── generate_data.py     synthetic data generator
│   ├── courses.csv
│   ├── users.csv
│   ├── usage_events.csv
│   └── survey_responses.csv
├── engine/
│   ├── __init__.py
│   ├── filters.py           candidate filtering (completed / prerequisites / level)
│   ├── signals.py           survey / usage / work_info signal scoring
│   ├── weighting.py         blends the three signals, handles cold-start, builds the reason
│   └── recommend.py         orchestration: filter -> score -> rank -> top N
└── samples/
    └── sample_output.md
```

## Status

`engine/filters.py` (partially), `engine/signals.py`, and
`engine/weighting.py` are stubs — see the docstrings in each for exactly
what's expected. The API runs and returns a clear `501` until they're
implemented.

## Environment variables

None required for the core engine. If you build the optional LLM bonus, copy
`.env.example` to `.env` and set `ANTHROPIC_API_KEY` there — never commit
`.env` (it's gitignored) or hardcode a key.
