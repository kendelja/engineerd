import asyncio

from app.ingestion.pipeline import run_pipeline

from app.ingestion.scrapers.BuiltInScraper import BuiltInScraper
from app.ingestion.parsers.BuiltInParser import BuiltInParser

from app.ingestion.scrapers.WellfoundScraper import WellfoundScraper
from app.ingestion.parsers.WellfoundParser import WellfoundParser

from app.ingestion.scrapers.JobBankScraper import JobBankScraper
from app.ingestion.parsers.JobBankParser import JobBankParser


async def main(market="canada"):
    await run_pipeline(
        BuiltInScraper(market=market),
        BuiltInParser(),
        "Built In"
    )

    await run_pipeline(
        WellfoundScraper(market=market),
        WellfoundParser(),
        "Wellfound"
    )

     # Job Bank is Canada-only.
    if market == "canada":
        await run_pipeline(
            JobBankScraper(market=market),
            JobBankParser(),
            "Job Bank"
        )


if __name__ == "__main__":
    asyncio.run(main())