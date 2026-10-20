"""
Read the detail page of stored jobs and fill in years required,
skills and the junior-fit label from the real posting text.

Run from the Backend folder:

    python -m scripts.enrichJobs                  # everything pending
    python -m scripts.enrichJobs --limit 20       # just a sample
    python -m scripts.enrichJobs --source BuiltIn
    python -m scripts.enrichJobs --all            # re-read already
                                                  # enriched jobs too

Jobs whose page cannot be read are retried on later runs, up to
3 attempts, so expired postings stop being requested.
"""

import argparse
import asyncio
from collections import Counter
from types import SimpleNamespace

from dotenv import load_dotenv

load_dotenv()

from app.database.repositories import (
    get_pending_detail_jobs,
    record_detail_failure,
    update_job_analysis,
)
from app.ingestion.analyzer import analyze_job
from app.ingestion.detail import SOURCES, fetcher_for


async def enrich(source=None, limit=None, include_checked=False):
    sources = [source] if source else list(SOURCES)

    labels = Counter()
    read = failed = 0

    for source_name in sources:
        rows = get_pending_detail_jobs(
            source=source_name,
            limit=limit,
            include_checked=include_checked,
        )

        if not rows:
            print(f"{source_name}: nothing pending.")
            continue

        jobs = [SimpleNamespace(**row) for row in rows]

        texts = await fetcher_for(source_name).fetch_texts(jobs)

        for job, text in zip(jobs, texts):
            if not text:
                record_detail_failure(job.id)
                failed += 1
                continue

            analysis = analyze_job(
                job.title,
                text,
                job.experience_level,
                salary_min=job.salary_min,
                salary_max=job.salary_max,
            )

            update_job_analysis(job.id, analysis, detail_checked=True)

            labels[analysis.fit_label] += 1
            read += 1

    print()
    print(f"Enriched {read} jobs ({failed} pages could not be read).")

    for label, count in labels.most_common():
        print(f"  {label:<16} {count}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=sorted(SOURCES))
    parser.add_argument("--limit", type=int)
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    asyncio.run(
        enrich(
            source=args.source,
            limit=args.limit,
            include_checked=args.all,
        )
    )


if __name__ == "__main__":
    main()
