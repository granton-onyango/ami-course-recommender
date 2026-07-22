from typing import Optional

from pydantic import BaseModel


class RecommendationItem(BaseModel):
    rank: int
    course_id: str
    title: str
    score: float
    reason: str


class RecommendationsResponse(BaseModel):
    user_id: str
    recommendations: list[RecommendationItem]


class SignalBreakdown(BaseModel):
    score: float
    reason: Optional[str]


class CourseBreakdown(BaseModel):
    rank: int
    course_id: str
    title: str
    signals: dict[str, SignalBreakdown]
    final_score: float
    final_reason: str


class FilterStage(BaseModel):
    stage: str
    count: int


class SurveyAnswers(BaseModel):
    skill_gaps: str
    goals: str
    preferred_topics: str
    confidence_by_topic: str


class BreakdownResponse(BaseModel):
    user_id: str
    survey: Optional[SurveyAnswers]
    filter_funnel: list[FilterStage]
    weights: dict[str, float]
    courses: list[CourseBreakdown]


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
