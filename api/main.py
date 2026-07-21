"""
AMI Course Recommendation API

Endpoints:
  GET /users/{user_id}/recommendations?n=5   - top N recommended courses
  GET /status                                - liveness + row counts

Run:
  python -m data.generate_data          # writes data/*.csv
  uvicorn api.main:app --reload
"""

import pathlib
from contextlib import asynccontextmanager

import pandas as pd
from fastapi import FastAPI, HTTPException

from engine.recommend import get_recommendations
from .models import RecommendationsResponse

ROOT = pathlib.Path(__file__).parent.parent
DATA_DIR = ROOT / "data"


@asynccontextmanager
async def lifespan(app: FastAPI):
    required = ["courses.csv", "users.csv", "usage_events.csv", "survey_responses.csv"]
    missing = [f for f in required if not (DATA_DIR / f).exists()]
    if missing:
        raise RuntimeError(
            f"Missing data files {missing} in {DATA_DIR}. "
            "Run: python -m data.generate_data"
        )

    app.state.courses = pd.read_csv(DATA_DIR / "courses.csv", keep_default_na=False)
    app.state.users = pd.read_csv(DATA_DIR / "users.csv", keep_default_na=False)
    app.state.usage_events = pd.read_csv(DATA_DIR / "usage_events.csv", keep_default_na=False)
    app.state.survey_responses = pd.read_csv(DATA_DIR / "survey_responses.csv", keep_default_na=False)
    yield


app = FastAPI(
    title="AMI Course Recommendation API",
    description="Explainable course recommendations for the AI Coach Bot.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/status")
def status():
    return {
        "status": "ok",
        "courses": len(app.state.courses),
        "users": len(app.state.users),
        "usage_events": len(app.state.usage_events),
        "survey_responses": len(app.state.survey_responses),
    }


@app.get("/users/{user_id}/recommendations", response_model=RecommendationsResponse)
def user_recommendations(user_id: str, n: int = 5):
    try:
        recs = get_recommendations(
            user_id=user_id,
            n=n,
            courses=app.state.courses,
            users=app.state.users,
            usage_events=app.state.usage_events,
            survey_responses=app.state.survey_responses,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"user_id '{user_id}' not found")
    except NotImplementedError as e:
        raise HTTPException(
            status_code=501,
            detail=f"Recommendation engine not implemented yet: {e}",
        )

    return RecommendationsResponse(user_id=user_id, recommendations=recs)
