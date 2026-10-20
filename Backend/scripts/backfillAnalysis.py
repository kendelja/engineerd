"""
Apply the database migrations and (re)analyze stored jobs from the
text we have for them (title, tags, listing blurb).

Jobs already enriched from their detail page are left alone -- the
full posting text is not stored, so re-analysing them here would
overwrite better data with worse. Use `scripts.enrichJobs --all` to
redo those.

Run from the Backend folder:

    python -m scripts.backfillAnalysis

Safe to run repeatedly -- e.g. after tweaking the rules in
app/ingestion/analyzer.py.
"""

from collections import Counter
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from app.database.connection import get_connection
from app.database.repositories import update_job_analysis
from app.ingestion.analyzer import analyze_job

MIGRATIONS = sorted(
    (Path(__file__).resolve().parents[2] / "database" / "migrations")
    .glob("*.sql")
)


def apply_migration():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            for migration in MIGRATIONS:
                cursor.execute(migration.read_text(encoding="utf-8"))

        connection.commit()

    finally:
        connection.close()


def main():
    apply_migration()
    print(f"Applied {len(MIGRATIONS)} migrations.")

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, title, description, experience_level, salary_min, salary_max FROM jobs "
                "WHERE detail_checked_at IS NULL"
            )
            rows = cursor.fetchall()

    finally:
        connection.close()

    labels = Counter()
    with_years = 0

    for job_id, title, description, experience_level, salary_min, salary_max in rows:
        analysis = analyze_job(
            title, description, experience_level,
            salary_min=salary_min, salary_max=salary_max,
        )

        update_job_analysis(job_id, analysis)

        labels[analysis.fit_label] += 1

        if analysis.years_required is not None:
            with_years += 1

    print(f"Analyzed {len(rows)} jobs ({with_years} with a years requirement).")

    for label, count in labels.most_common():
        print(f"  {label:<16} {count}")


if __name__ == "__main__":
    main()
