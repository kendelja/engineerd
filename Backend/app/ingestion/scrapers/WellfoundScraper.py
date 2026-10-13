import asyncio
import random

from playwright.async_api import async_playwright

from app.ingestion.config import (
    WELLFOUND_PAGES_PER_URL,
    WELLFOUND_URLS,
)


class WellfoundScraper:
    """
    Reads Wellfound role pages for a market.

    All experience levels come back together; each position carries
    its required years of experience, which WellfoundParser extracts
    so the analyzer can tell junior from senior.
    """

    BASE_URL = "https://wellfound.com"

    # Polite pause between page loads.
    PAGE_DELAY_SECONDS = (1.5, 3.0)

    def __init__(
        self,
        market="canada",
        pages_per_url=WELLFOUND_PAGES_PER_URL,
        headless=True,
    ):
        self.market = market
        self.pages_per_url = pages_per_url
        self.headless = headless

    def build_page_url(self, path: str, page_number: int) -> str:
        url = f"{self.BASE_URL}{path}"

        if page_number == 1:
            return url

        return f"{url}?page={page_number}"

    def paths(self) -> list[str]:
        if self.market == "north-america":
            markets = ["canada", "usa"]
        else:
            markets = [self.market]

        unknown = [m for m in markets if m not in WELLFOUND_URLS]

        if unknown:
            raise ValueError(
                f"No Wellfound URLs configured for market: {unknown[0]}"
            )

        return [
            path
            for market in markets
            for path in WELLFOUND_URLS[market]
        ]

    async def fetch_jobs_page(self) -> str:
        pages = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless
            )

            page = await browser.new_page()

            try:
                for path in self.paths():
                    for page_number in range(1, self.pages_per_url + 1):
                        url = self.build_page_url(path, page_number)

                        print(
                            f"Fetching Wellfound "
                            f"({self.market}) page {page_number}: {url}"
                        )

                        response = await page.goto(
                            url,
                            wait_until="domcontentloaded",
                            timeout=60000
                        )

                        if response is not None and response.status >= 400:
                            print(f"  skipped (HTTP {response.status})")
                            break

                        await page.wait_for_timeout(2000)

                        html = await page.content()

                        pages.append(html)

                        print("Page downloaded.")

                        # Stop once this listing runs out of pages.
                        if 'aria-label="Next page"' not in html:
                            break

                        await asyncio.sleep(
                            random.uniform(*self.PAGE_DELAY_SECONDS)
                        )

            finally:
                await browser.close()

        return "\n".join(pages)
