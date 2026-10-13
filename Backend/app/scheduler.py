"""
Scheduled ingestion.

Runs inside the API process, so the schedule only fires while the API
is running. Configure with environment variables (all optional):

    INGEST_SCHEDULE_ENABLED   "1" (default) or "0" to turn it off
    INGEST_HOURS              hours of the day, default "0,6,12,18"
    INGEST_MARKETS            comma-separated, default "canada"
    INGEST_TIMEZONE           default "America/Toronto"
"""

import os
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.ingestion.runner import IngestionBusy, run_ingestion


JOB_ID = "scheduled-ingest"

DEFAULT_HOURS = "0,6,12,18"
DEFAULT_MARKETS = "canada"
DEFAULT_TIMEZONE = "America/Toronto"


def _config():
    enabled = os.getenv("INGEST_SCHEDULE_ENABLED", "1").strip().lower() not in (
        "0", "false", "no", "off", "",
    )

    hours = [
        int(hour)
        for hour in os.getenv("INGEST_HOURS", DEFAULT_HOURS).split(",")
        if hour.strip()
    ]

    markets = [
        market.strip()
        for market in os.getenv("INGEST_MARKETS", DEFAULT_MARKETS).split(",")
        if market.strip()
    ]

    timezone = ZoneInfo(os.getenv("INGEST_TIMEZONE", DEFAULT_TIMEZONE))

    return enabled, hours, markets, timezone


scheduler = AsyncIOScheduler()


async def scheduled_ingest():
    _, _, markets, _ = _config()

    for market in markets:
        try:
            result = await run_ingestion(market, "scheduled")
            print(
                f"[{datetime.now():%Y-%m-%d %H:%M}] scheduled {market}: "
                f"{result['inserted']} new jobs"
            )

        except IngestionBusy:
            print(
                f"[{datetime.now():%Y-%m-%d %H:%M}] scheduled {market}: "
                "skipped, a refresh is already running"
            )

        except Exception as error:
            # Logged in ingestion_runs; the next scheduled run still happens.
            print(
                f"[{datetime.now():%Y-%m-%d %H:%M}] scheduled {market} failed: "
                f"{error}"
            )


def start_scheduler():
    enabled, hours, _, timezone = _config()

    if not enabled or not hours:
        print("Scheduled ingestion is off.")
        return

    scheduler.configure(timezone=timezone)

    scheduler.add_job(
        scheduled_ingest,
        CronTrigger(hour=",".join(str(h) for h in hours), minute=0, timezone=timezone),
        id=JOB_ID,
        replace_existing=True,
        max_instances=1,      # never two scheduled runs at once
        coalesce=True,        # missed runs collapse into one
        misfire_grace_time=3600,
    )

    scheduler.start()

    print(f"Scheduled ingestion on: {hours} ({timezone.key})")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)


def next_run_at():
    if not scheduler.running:
        return None

    job = scheduler.get_job(JOB_ID)

    if job is None or job.next_run_time is None:
        return None

    return job.next_run_time.isoformat()
