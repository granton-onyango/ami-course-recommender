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
