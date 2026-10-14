"""
Apply migration 004 and fill in the Country tabs for stored jobs.

Run from the Backend folder:

    python -m scripts.backfillMarkets

New jobs get their markets at ingestion; this is only for existing rows.
"""

from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from app.database.connection import get_connection
from app.ingestion.eligibility import markets_for_location

MIGRATION = (
    Path(__file__).resolve().parents[2]
    / "database"
    / "migrations"
    / "004_job_markets.sql"
)


def main():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(MIGRATION.read_text(encoding="utf-8"))
            cursor.execute("SELECT id, location FROM jobs")
            rows = cursor.fetchall()

            for job_id, location in rows:
                cursor.execute(
                    "UPDATE jobs SET markets = %s WHERE id = %s",
                    (markets_for_location(location), job_id),
                )

        connection.commit()

    finally:
        connection.close()

    print(f"Set Country tabs for {len(rows)} jobs.")


if __name__ == "__main__":
    main()
