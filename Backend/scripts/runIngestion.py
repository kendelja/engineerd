import asyncio

from app.ingestion.pipeline import run_pipeline

from app.ingestion.scrapers.BuiltInScraper import BuiltInScraper
from app.ingestion.parsers.BuiltInParser import BuiltInParser

from app.ingestion.scrapers.WellfoundScraper import WellfoundScraper
from app.ingestion.parsers.WellfoundParser import WellfoundParser


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


if __name__ == "__main__":
    asyncio.run(main())