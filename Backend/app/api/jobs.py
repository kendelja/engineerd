from fastapi import APIRouter, HTTPException, Query

from app.database.repositories import (
    get_daily_postings,
    get_fit_summary,
    get_jobs,
    get_top_skills,
    clear_jobs,
)
from app.ingestion.analyzer import FIT_LABELS
from app.ingestion.runner import IngestionBusy, get_ingest_status, run_ingestion
from app.scheduler import next_run_at

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("/ingest")
async def ingest_jobs(
    market: str = "canada",
    #experience: str = "all",
):
    valid_markets = {"canada", "usa", "north-america"}
    #valid_experience = {"all", "junior", "senior"}

    if market not in valid_markets:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid market. Choose from: {', '.join(valid_markets)}",
        )

    # if experience not in valid_experience:
    #     raise HTTPException(
    #         status_code=400,
    #         detail=f"Invalid experience. Choose from: {', '.join(valid_experience)}",
    #     )

    #clear_jobs()

    try:
        result = await run_ingestion(market, "manual")

    except IngestionBusy:
        raise HTTPException(
            status_code=409,
            detail="A job refresh is already running. Try again in a minute.",
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="The refresh failed. Check the server log for details.",
        )

    return {
        "status": "complete",
        "market": market,
        "inserted": result["inserted"],
        #"experience": experience
    }


def _validate_fit_labels(labels: list[str] | None, param: str):
    unknown = set(labels or []) - FIT_LABELS

    if unknown:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid {param}: {', '.join(sorted(unknown))}. "
                f"Choose from: {', '.join(sorted(FIT_LABELS))}"
            ),
        )


@router.get("/")
def jobs(
    limit: int = Query(default=600, ge=1, le=600),
    fit: list[str] | None = Query(
        default=None,
        description="Only these fit labels (repeatable).",
    ),
    exclude_fit: list[str] | None = Query(
        default=None,
        description="Hide these fit labels, e.g. ghost-junior.",
    ),
    max_years: int | None = Query(
        default=None,
        ge=0,
        le=20,
        description="Hide jobs asking for more years than this.",
    ),
    skill: list[str] | None = Query(
        default=None,
        description="Jobs mentioning all of these skills (repeatable).",
    ),
):
    _validate_fit_labels(fit, "fit")
    _validate_fit_labels(exclude_fit, "exclude_fit")

    return get_jobs(
        limit,
        fit=fit,
        exclude_fit=exclude_fit,
        max_years=max_years,
        skills=skill,
    )


@router.get("/fit-summary")
def fit_summary():
    """How many postings fall under each junior-fit label."""
    return get_fit_summary()


@router.get("/activity")
def activity(days: int = Query(default=14, ge=1, le=60)):
    """Jobs posted per day, for the activity chart."""
    return get_daily_postings(days)


@router.get("/top-skills")
def top_skills(limit: int = Query(default=3, ge=1, le=500)):
    """Most-mentioned skills, for the summary cards."""
    return get_top_skills(limit)


@router.get("/ingest/status")
def ingest_status():
    """Whether a refresh is running, when jobs last updated, and what's next."""
    return {
        **get_ingest_status(),
        "next_run_at": next_run_at(),
    }
