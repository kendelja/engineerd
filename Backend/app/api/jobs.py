from fastapi import APIRouter, HTTPException, Query

from app.database.repositories import get_jobs, clear_jobs
from scripts.runIngestion import main

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("/ingest")
async def ingest_jobs(market: str = "canada"):
    valid_markets = {"canada", "usa", "north-america"}

    if market not in valid_markets:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid market. Choose from: {', '.join(valid_markets)}"
        )

    clear_jobs()

    await main(market)

    return {
        "status": "complete",
        "market": market
    }


@router.get("/")
def jobs(limit: int = Query(default=200, ge=1, le=200)):
    return get_jobs(limit)