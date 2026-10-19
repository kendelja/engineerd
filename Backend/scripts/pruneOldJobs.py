"""
Delete stored jobs whose posting is older than the ingestion window.

A job older than MAX_JOB_AGE_DAYS is never inserted, so keeping it only
leaves stale listings in the tabs. Rows with no posted date are kept.

Run from the Backend folder:

    python -m scripts.pruneOldJobs            # preview only
    python -m scripts.pruneOldJobs --apply    # delete
"""

import argparse
from datetime import datetime, timedelta

from dotenv import load_dotenv

load_dotenv()

from app.database.connection import get_connection
from app.ingestion.pipeline import MAX_JOB_AGE_DAYS


def prune(connection, apply=False):
    cutoff = datetime.now() - timedelta(days=MAX_JOB_AGE_DAYS)

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT count(*) FROM jobs WHERE posted_at < %s",
            (cutoff,),
        )
        count = cursor.fetchone()[0]

        if apply and count:
            cursor.execute(
                "DELETE FROM jobs WHERE posted_at < %s",
                (cutoff,),
            )
            connection.commit()

    return count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    connection = get_connection()

    try:
        count = prune(connection, apply=args.apply)

        if args.apply:
            print(f"Deleted {count} jobs posted before the last {MAX_JOB_AGE_DAYS} days.")
        else:
            print(f"{count} jobs posted before the last {MAX_JOB_AGE_DAYS} days would be deleted.")
            print("Preview only. Re-run with --apply to delete.")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
