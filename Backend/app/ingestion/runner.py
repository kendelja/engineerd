"""
Runs an ingestion and records it in ingestion_runs.

Scheduled and manual refreshes both go through run_ingestion(). A lock
makes sure only one runs at a time: a manual click during a scheduled
run gets a "busy" answer instead of two scrapes at once.
"""

import asyncio
from datetime import datetime

from app.database.connection import get_connection


_lock = asyncio.Lock()


class IngestionBusy(Exception):
    """Another ingestion is already running."""


def is_running() -> bool:
    return _lock.locked()


def _start_run(market: str, trigger: str) -> int:
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO ingestion_runs (market, trigger, status)
                VALUES (%s, %s, 'running')
                RETURNING id
                """,
                (market, trigger),
            )
            run_id = cursor.fetchone()[0]

        connection.commit()

        return run_id

    finally:
        connection.close()


def _finish_run(run_id: int, status: str, inserted=None, error=None):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE ingestion_runs
                SET status = %s,
                    finished_at = %s,
                    inserted = %s,
                    error = %s
                WHERE id = %s
                """,
                (status, datetime.now(), inserted, error, run_id),
            )

        connection.commit()

    finally:
        connection.close()


async def run_ingestion(market: str, trigger: str) -> dict:
    """
    Scrape, enrich and store jobs for `market`.

    trigger -- "scheduled" or "manual", recorded with the run.
    Raises IngestionBusy if a run is already in progress.
    """

    if _lock.locked():
        raise IngestionBusy()

    # Imported here so the scheduler can load without the scraping stack.
    from scripts.runIngestion import main

    async with _lock:
        run_id = _start_run(market, trigger)

        try:
            inserted = await main(market)

        except Exception as error:
            _finish_run(run_id, "failed", error=str(error)[:2000])
            raise

        _finish_run(run_id, "success", inserted=inserted)

        return {"run_id": run_id, "inserted": inserted}


def get_ingest_status(limit: int = 5) -> dict:
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, market, trigger, status, started_at,
                       finished_at, inserted, error
                FROM ingestion_runs
                ORDER BY started_at DESC
                LIMIT %s
                """,
                (limit,),
            )

            columns = [column[0] for column in cursor.description]
            recent = [
                {
                    key: (value.isoformat() if isinstance(value, datetime) else value)
                    for key, value in zip(columns, row)
                }
                for row in cursor.fetchall()
            ]

    finally:
        connection.close()

    last_success = next(
        (run for run in recent if run["status"] == "success"),
        None,
    )

    return {
        "running": is_running(),
        "last_success_at": last_success["finished_at"] if last_success else None,
        "recent": recent,
    }
