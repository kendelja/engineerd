from datetime import datetime, timedelta

from app.ingestion.analyzer import analyze_job
from app.ingestion.normalizer import apply_analysis, normalize_job
from app.ingestion.validator import validate_job
from app.ingestion.eligibility import is_excluded_title, location_eligible
from app.ingestion.deduplicator import job_exists
from app.database.repositories import insert_job, refresh_work_model


MAX_JOB_AGE_DAYS = 30


def is_recent_job(posted_at):
    if posted_at is None:
        return False

    cutoff = datetime.now() - timedelta(days=MAX_JOB_AGE_DAYS)

    return posted_at >= cutoff


async def run_pipeline(scraper, parser, source_name, detail_fetcher=None, market=None):
    """
    scraper         -- downloads the listing page(s)
    parser          -- turns the listing into raw job dicts
    detail_fetcher  -- optional DetailFetcher; opens each *new* job's
                       page so years / skills come from the real
                       posting instead of the listing blurb
    market          -- "canada" | "usa" | "north-america"; jobs whose
                       location is not open to it are dropped. None
                       keeps every location.
    """

    print(f"Starting {source_name} ingestion...")

    html = await scraper.fetch_jobs_page()

    print("Page downloaded.")

    raw_jobs = parser.parse(html)

    print(f"Parsed {len(raw_jobs)} jobs.")

    inserted = 0
    skipped = 0
    invalid = 0
    expired = 0
    excluded = 0
    enriched = 0

    new_jobs = []

    for raw_job in raw_jobs:
        try:
            job = normalize_job(raw_job)

            valid, errors = validate_job(job)

            if not valid:
                invalid += 1
                print(f"Invalid job: {errors}")
                continue

            if is_excluded_title(job.title):
                excluded += 1
                continue

            if not location_eligible(job.location, market):
                excluded += 1
                continue

            if not is_recent_job(job.posted_at):
                expired += 1
                continue

            if job_exists(
                job.source,
                job.source_job_id,
                job.url
            ):
                # Work model was not captured by earlier versions.
                refresh_work_model(job)
                skipped += 1
                continue

            new_jobs.append(job)

        except Exception as error:
            print(f"Failed processing job: {error}")

    if detail_fetcher is not None and new_jobs:
        texts = await detail_fetcher.fetch_texts(new_jobs)

        for job, text in zip(new_jobs, texts):
            if not text:
                # Stored anyway; enrichJobs.py can retry later.
                continue

            apply_analysis(
                job,
                analyze_job(
                    job.title,
                    text,
                    job.experience_level,
                    salary_min=job.salary_min,
                    salary_max=job.salary_max,
                ),
            )
            job.detail_checked_at = datetime.now()
            enriched += 1

    for job in new_jobs:
        try:
            insert_job(job)
            inserted += 1

        except Exception as error:
            print(f"Failed inserting job: {error}")

    print()
    print(f"{source_name} ingestion complete.")
    print(f"Inserted: {inserted}")
    print(f"Enriched: {enriched}")
    print(f"Skipped:  {skipped}")
    print(f"Invalid:  {invalid}")
    print(f"Expired:  {expired}")
    print(f"Excluded: {excluded}  (non-software titles, other markets)")

    return inserted
