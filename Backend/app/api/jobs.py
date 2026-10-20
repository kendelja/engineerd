import os
import secrets

from datetime import datetime

from fastapi import APIRouter, Header, HTTPException, Query

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

# Unfiltered list: junior-tagged roles get their own slots, so a flood of
# senior roles can't push them out of the window. Senior and every other
# label share the rest, up to SENIOR_MAX.
JUNIOR_FITS = ["junior-friendly", "junior-unconfirmed", "ghost-junior"]
JUNIOR_SLOTS = 200
SENIOR_MAX = 400


@router.post("/ingest")
async def ingest_jobs(
    market: str = "canada",
    x_admin_token: str | None = Header(default=None),
    #experience: str = "all",
):
    # Manual refresh is for the owner only. With no ADMIN_TOKEN set it is off.
    expected_token = os.getenv("ADMIN_TOKEN")

    if not expected_token:
        raise HTTPException(status_code=403, detail="Manual refresh is disabled.")

    if not secrets.compare_digest(x_admin_token or "", expected_token):
        raise HTTPException(status_code=403, detail="Admin token rejected.")

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
    market: str | None = Query(
        default=None,
        description="Country tab: canada, usa or north-america.",
    ),
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

    if market is not None and market not in {"canada", "usa", "north-america"}:
        raise HTTPException(status_code=400, detail="Invalid market.")

    if fit is None and exclude_fit is None:
        junior = get_jobs(
            min(JUNIOR_SLOTS, limit),
            market=market,
            fit=JUNIOR_FITS,
            max_years=max_years,
            skills=skill,
        )

        others = get_jobs(
            min(SENIOR_MAX, limit - len(junior)),
            market=market,
            exclude_fit=JUNIOR_FITS,
            max_years=max_years,
            skills=skill,
        )

        return sorted(
            junior + others,
            key=lambda job: job["posted_at"] or datetime.min,
            reverse=True,
        )

    return get_jobs(
        limit,
        market=market,
        fit=fit,
        exclude_fit=exclude_fit,
        max_years=max_years,
        skills=skill,
    )


@router.get("/fit-summary")
def fit_summary():
    """How many postings fall under each junior-fit label."""
    return get_fit_summary()


def _check_market(market):
    if market is not None and market not in {"canada", "usa", "north-america"}:
        raise HTTPException(status_code=400, detail="Invalid market.")


@router.get("/activity")
def activity(
    days: int = Query(default=14, ge=1, le=60),
    market: str | None = Query(default=None),
):
    """Jobs posted per day in a Country tab, for the activity chart."""
    _check_market(market)
    return get_daily_postings(days, market=market)


@router.get("/top-skills")
def top_skills(
    limit: int = Query(default=3, ge=1, le=500),
    market: str | None = Query(default=None),
):
    """Most-mentioned skills in a Country tab, for the summary cards."""
    _check_market(market)
    return get_top_skills(limit, market=market)


@router.get("/ingest/status")
def ingest_status():
    """Whether a refresh is running, when jobs last updated, and what's next."""
    return {
        **get_ingest_status(),
        "next_run_at": next_run_at(),
    }
