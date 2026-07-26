# AMI Course Recommendation Engine

**🔗 Live demo: [https://ami-course-recommender.onrender.com](https://ami-course-recommender.onrender.com)**

*Free Render tier — the first request after a period of inactivity can take ~30-60s to wake up (cold start). Give it a moment before assuming it's broken. 😂*

Explainable course recommendations for the AI Coach Bot — given a user,
returns the top N recommended courses, each with a rank, a score, and a
specific human-readable reason.

See [WRITEUP.md](WRITEUP.md) for the design writeup.

## Install & run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python -m data.generate_data      # writes data/*.csv (192 courses, 1,000 users)
uvicorn api.main:app --reload
```

Then open `http://127.0.0.1:8000/` in a browser for the UI, or hit the API
directly (below). If `uvicorn` isn't found after activating the venv, run
`.venv/bin/uvicorn api.main:app --reload` instead.

## Example request/response

```bash
curl "http://127.0.0.1:8000/users/U00012/recommendations?n=1"
```

```json
{
  "user_id": "U00012",
  "recommendations": [
    {
      "rank": 1,
      "course_id": "C0001",
      "title": "Intro to Financial Planning",
      "score": 0.8,
      "reason": "Because you told us Financial Planning is a skill gap, and you did well in other Financial Planning courses, we suggest this course."
    }
  ]
}
```

Real, captured output — not a mockup. `samples/sample_output.md` has full
responses (`n=5`) for three usage tiers: a true cold-start user, a
mid-usage user, and a heavy-usage user.

## Running tests

```bash
pytest
```

26 tests, split by file: `tests/test_filters.py` (the hard eligibility
gates — completed courses, prerequisites, level caps), `tests/test_signals.py`
(the three independent scoring functions), `tests/test_weighting.py` (the
cold-start renormalization policy — including a test that directly proves
renormalizing scores higher than a naive treat-missing-as-zero policy
would), and `tests/test_recommend.py` (the full filter -> score -> rank
pipeline, end to end). Each test builds a small, hand-crafted table inline
rather than depending on the generated `data/*.csv` files, so what's being
tested is obvious from reading the test itself.

## API endpoints

| Method | Path | What it does |
|---|---|---|
| `GET` | `/` | The web UI (recommendations / breakdown / AI tabs) |
| `GET` | `/status` | Liveness check + row counts for the loaded data |
| `GET` | `/users/{user_id}/recommendations?n=5` | Top N recommendations, with score + reason |
| `GET` | `/users/{user_id}/breakdown?n=5` | Debug view: survey answers, filter funnel, per-signal scores behind each recommendation |
| `POST` | `/users/{user_id}/ask` `{"question": "..."}` | Claude answers free-form questions about a user's breakdown (optional, needs `ANTHROPIC_API_KEY`) |
| `POST` | `/users/{user_id}/coach?course_id=C0001&n=5` | Claude rewrites one recommendation's existing score + reason as a warm coaching message — the LLM never sees or changes the underlying decision (optional, needs `ANTHROPIC_API_KEY`) |

## Project structure

```
.
├── README.md
├── ARCHITECTURE.md
├── WRITEUP.md
├── requirements.txt
├── pytest.ini                 tells pytest to add the repo root to sys.path (so `from engine import ...` resolves)
├── .python-version           pins the interpreter this was built/tested against (3.9.6)
├── taxonomy.py                shared topic/level/skill vocabulary (single source of truth)
├── api/
│   ├── __init__.py
│   ├── main.py                FastAPI app: recommendations, breakdown, ask, coach, and the UI route
│   ├── models.py               request/response schemas
│   └── assistant.py            Claude-powered Q&A + coaching-message features (optional LLM bonus)
├── data/
│   ├── __init__.py
│   ├── generate_data.py        synthetic data generator
│   ├── courses.csv
│   ├── users.csv
│   ├── usage_events.csv
│   └── survey_responses.csv
├── engine/
│   ├── __init__.py
│   ├── filters.py               candidate filtering (completed / prerequisites / level)
│   ├── signals.py                survey / usage / work_info signal scoring
│   ├── weighting.py              blends the three signals, handles cold-start, builds the reason
│   └── recommend.py              orchestration: filter -> score -> rank -> top N
├── static/
│   ├── index.html                single-page UI (recommendations / breakdown / AI tabs)
│   └── marked.min.js             markdown rendering for the AI tab's answers (bundled, no CDN)
├── tests/
│   ├── test_filters.py           completed / prerequisite / level filtering
│   ├── test_signals.py           survey / usage / work_info scoring
│   ├── test_weighting.py         blending + cold-start renormalization
│   └── test_recommend.py         full pipeline, end to end
└── samples/
    └── sample_output.md          real output for a cold-start, mid-usage, and heavy-usage user
```

## Status

Fully implemented and running end to end — filtering, all three signals,
cold-start-aware weighting, the API, the UI, and both optional LLM
features. `GET /users/{user_id}/recommendations` returns real
recommendations, not a `501`.

## Environment variables

None required for the core recommendation engine — `/recommendations` and
`/breakdown` work with no configuration. The AI tab's two features (`/ask`
and `/coach`) need a Claude API key: copy `.env.example` to `.env` and set
`ANTHROPIC_API_KEY` there. `.env` is gitignored — never commit it or
hardcode a key. In production (e.g. Render), set `ANTHROPIC_API_KEY` as a
platform environment variable instead of shipping a `.env` file.

## Deployment

Runs as a normal long-lived Python process (`uvicorn`), so it fits
conventional Python hosts (Render, Fly.io, Railway) directly — no
rearchitecting needed. `.python-version` pins the interpreter to `3.9.6` to
match what this was actually built and tested against; without it, a host
defaulting to a newer Python can fail installing `pydantic-core` (no
prebuilt wheel yet, forces a source build that isn't guaranteed to work in
every build sandbox).
