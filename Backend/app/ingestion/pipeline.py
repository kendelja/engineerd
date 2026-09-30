from datetime import datetime, timedelta

from app.ingestion.normalizer import normalize_job
from app.ingestion.validator import validate_job
from app.ingestion.deduplicator import job_exists
from app.database.repositories import insert_job


MAX_JOB_AGE_DAYS = 30


def is_recent_job(posted_at):
    if posted_at is None:
        return False

    cutoff = datetime.now() - timedelta(days=MAX_JOB_AGE_DAYS)

    return posted_at >= cutoff


async def run_pipeline(scraper, parser, source_name):
    print(f"Starting {source_name} ingestion...")

    html = await scraper.fetch_jobs_page()

    print("Page downloaded.")

    raw_jobs = parser.parse(html)

    print(f"Parsed {len(raw_jobs)} jobs.")

    inserted = 0
    skipped = 0
    invalid = 0
    expired = 0

    for raw_job in raw_jobs:
        try:
            job = normalize_job(raw_job)

            valid, errors = validate_job(job)

            if not valid:
                invalid += 1
                print(f"Invalid job: {errors}")
                continue

            if not is_recent_job(job.posted_at):
                expired += 1
                continue

            if job_exists(
                job.source,
                job.source_job_id,
                job.url
            ):
                skipped += 1
                continue

            insert_job(job)
            inserted += 1

        except Exception as error:
            print(f"Failed processing job: {error}")

    print()
    print(f"{source_name} ingestion complete.")
    print(f"Inserted: {inserted}")
    print(f"Skipped:  {skipped}")
    print(f"Invalid:  {invalid}")
    print(f"Expired:  {expired}")