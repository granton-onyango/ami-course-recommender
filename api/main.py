"""
AMI Course Recommendation API

Endpoints:
  GET /users/{user_id}/recommendations?n=5   - top N recommended courses
  GET /status                                - liveness + row counts

Run:
  python -m data.generate_data          # writes data/*.csv
  uvicorn api.main:app --reload
"""

import os
import pathlib
from contextlib import asynccontextmanager

import anthropic
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from engine.recommend import get_recommendation_breakdown, get_recommendations
from . import assistant
from .models import AskRequest, AskResponse, BreakdownResponse, CoachResponse, RecommendationsResponse

ROOT = pathlib.Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
STATIC_DIR = ROOT / "static"


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

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def ui():
    return FileResponse(STATIC_DIR / "index.html")


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


@app.get("/users/{user_id}/breakdown", response_model=BreakdownResponse)
def user_breakdown(user_id: str, n: int = 5):
    try:
        breakdown = get_recommendation_breakdown(
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

    return breakdown


@app.post("/users/{user_id}/ask", response_model=AskResponse)
def ask_assistant(user_id: str, request: AskRequest):
    try:
        breakdown = get_recommendation_breakdown(
            user_id=user_id,
            n=5,
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

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY is missing -- copy .env.example to .env and fill it in",
        )

    try:
        answer = assistant.ask(breakdown, request.question)
    except anthropic.AuthenticationError:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY is missing or invalid -- copy .env.example to .env and fill it in",
        )
    except anthropic.RateLimitError:
        raise HTTPException(status_code=429, detail="Claude API rate limit hit, try again shortly")
    except anthropic.APIStatusError as e:
        raise HTTPException(status_code=502, detail=f"Claude API error: {e.message}")

    return AskResponse(answer=answer)


@app.post("/users/{user_id}/coach", response_model=CoachResponse)
def coach_assistant(user_id: str, course_id: str, n: int = 5):
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

    course = next((r for r in recs if r["course_id"] == course_id), None)
    if course is None:
        raise HTTPException(
            status_code=404,
            detail=f"course_id '{course_id}' not found in this user's top {n} recommendations",
        )

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY is missing -- copy .env.example to .env and fill it in",
        )

    try:
        message = assistant.coach_message(course)
    except anthropic.AuthenticationError:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY is missing or invalid -- copy .env.example to .env and fill it in",
        )
    except anthropic.RateLimitError:
        raise HTTPException(status_code=429, detail="Claude API rate limit hit, try again shortly")
    except anthropic.APIStatusError as e:
        raise HTTPException(status_code=502, detail=f"Claude API error: {e.message}")

    return CoachResponse(course_id=course["course_id"], title=course["title"], message=message)
