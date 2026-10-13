"""
Remove stored jobs that the eligibility rules would now reject:
interns / co-ops, and locations open to neither Canada nor the US.

Run from the Backend folder:

    python -m scripts.cleanupIneligible            # preview only
    python -m scripts.cleanupIneligible --apply    # delete

Rows whose location is Canada-only or US-only are kept, since they
are valid for one of the markets.
"""

import argparse

from dotenv import load_dotenv

load_dotenv()

from app.database.connection import get_connection
from app.ingestion.eligibility import is_excluded_title, is_ineligible_location


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, source, title, company, location FROM jobs")
            rows = cursor.fetchall()

        doomed = []

        for job_id, source, title, company, location in rows:
            if is_excluded_title(title):
                doomed.append((job_id, "intern/co-op", source, title, company, location))
            elif is_ineligible_location(location):
                doomed.append((job_id, "location", source, title, company, location))

        print(f"{len(doomed)} of {len(rows)} stored jobs are ineligible:\n")

        for _, reason, source, title, company, location in doomed:
            print(f"  [{reason:12}] {source:12} {title[:45]:45} {company[:22]:22} {location}")

        if not args.apply:
            print("\nPreview only. Re-run with --apply to delete.")
            return

        if doomed:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM jobs WHERE id = ANY(%s)",
                    ([row[0] for row in doomed],),
                )
            connection.commit()

        print(f"\nDeleted {len(doomed)} jobs.")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
