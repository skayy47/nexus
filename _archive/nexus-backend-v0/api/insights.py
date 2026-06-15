from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter(tags=["insights"])


class InsightsResponse(BaseModel):
    contradiction_count: int
    gap_count: int
    document_count: int
    top_topics: list[str]


@router.get("/insights", response_model=InsightsResponse)
async def get_insights() -> InsightsResponse:
    # TODO Week 2: aggregate from DB — stub for now
    return InsightsResponse(
        contradiction_count=0,
        gap_count=0,
        document_count=0,
        top_topics=[],
    )
