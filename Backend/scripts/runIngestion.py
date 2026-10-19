
import asyncio
from dotenv import load_dotenv

load_dotenv()

from app.ingestion.pipeline import run_pipeline
from app.ingestion.detail import fetcher_for

from app.ingestion.scrapers.BuiltInScraper import BuiltInScraper
from app.ingestion.parsers.BuiltInParser import BuiltInParser

from app.ingestion.scrapers.WellfoundScraper import WellfoundScraper
from app.ingestion.parsers.WellfoundParser import WellfoundParser

from app.ingestion.scrapers.JobBankScraper import JobBankScraper
from app.ingestion.parsers.JobBankParser import JobBankParser

from app.ingestion.scrapers.SimplifyJobsScraper import SimplifyJobsScraper
from app.ingestion.parsers.SimplifyJobsParser import SimplifyJobsParser

from app.ingestion.config import build_simplifyjobs_filter

from scripts.enrichJobs import enrich
from scripts.pruneOldJobs import prune
from app.database.connection import get_connection


# Stored jobs whose detail page is still unread are retried at the end of
# every run, up to this many per source. Each read takes a few seconds.
DETAIL_RETRIES_PER_SOURCE = 150


async def main(market="canada"):
    total = 0

    # Keep your existing sources disabled for now.
    # Re-enable them later when you're ready to run their market-specific pulls.

    total += await run_pipeline(
        BuiltInScraper(market=market, experience="junior"),
        BuiltInParser(experience="junior"),
        "Built In (junior)",
        detail_fetcher=fetcher_for("BuiltIn"),
        market=market,
    )

    total += await run_pipeline(
        BuiltInScraper(market=market, experience="senior"),
        BuiltInParser(experience="senior"),
        "Built In (mid/senior)",
        detail_fetcher=fetcher_for("BuiltIn"),
        market=market,
    )
    total += await run_pipeline(
        WellfoundScraper(market=market),
        WellfoundParser(),
        "Wellfound",
        market=market,
    )

    # if market == "canada":
    #     await run_pipeline(
    #         JobBankScraper(market=market),
    #         JobBankParser(),
    #         "Job Bank",
    #     )

    # Fetch junior jobs.
    junior_filter = build_simplifyjobs_filter("junior")

    total += await run_pipeline(
        SimplifyJobsScraper(filter_by=junior_filter),
        SimplifyJobsParser(),
        "SimplifyJobs (junior)",
        detail_fetcher=fetcher_for("SimplifyJobs"),
        market=market,
    )

    # Fetch mid-level and senior jobs in the same refresh.
    senior_filter = build_simplifyjobs_filter("senior")

    total += await run_pipeline(
        SimplifyJobsScraper(filter_by=senior_filter),
        SimplifyJobsParser(),
        "SimplifyJobs (mid/senior)",
        detail_fetcher=fetcher_for("SimplifyJobs"),
        market=market,
    )

    # Jobs stored before their detail page was read (or whose read failed
    # earlier) are never revisited by the pipeline, so read them here.
    # A failure must not undo the inserts above.
    try:
        await enrich(limit=DETAIL_RETRIES_PER_SOURCE)
    except Exception as error:
        print(f"Reading pending detail pages failed: {error}")

    # Drop stored jobs that have aged out of the ingestion window.
    try:
        connection = get_connection()
        try:
            pruned = prune(connection, apply=True)
            print(f"Pruned {pruned} jobs older than the ingestion window.")
        finally:
            connection.close()
    except Exception as error:
        print(f"Pruning old jobs failed: {error}")

    return total


if __name__ == "__main__":
    asyncio.run(main())
