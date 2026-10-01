from playwright.async_api import async_playwright


class BuiltInScraper:

    BASE_URL = "https://builtin.com"

    JOB_FEEDS = {
        "canada": [
            "/jobs/remote/hybrid/office/engineering?country=CAN&allLocations=true",
        ],

        "usa": [
            "/jobs/remote/hybrid/office/engineering?city=&state=&country=USA&allLocations=true",
        ],
    }

    # Number of pages to collect from each feed.
    PAGES_PER_FEED = 2

    def __init__(self, market="canada", headless=True):
        self.market = market
        self.headless = headless

    async def fetch_page(self, page, url: str) -> str:
        """
        Load a single Built In job listing page and return
        the rendered HTML.
        """

        print(f"Fetching Built In: {url}")

        await page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60000
        )

        # Give dynamically rendered job cards time to load.
        await page.wait_for_timeout(2000)

        html = await page.content()

        print("Page downloaded.")

        return html

    def build_page_url(self, base_url: str, page_number: int) -> str:
        """
        Build the URL for a specific pagination page.

        Page 1 uses the original URL.

        Page 2+ appends the appropriate page parameter.
        """

        if page_number == 1:
            return base_url

        separator = "&" if "?" in base_url else "?"

        return f"{base_url}{separator}page={page_number}"

    async def fetch_jobs_page(self) -> str:
        """
        Scrape the Built In feeds associated with the selected
        market.

        Returns all rendered HTML pages joined together so the
        existing BuiltInParser can process them.
        """

        # Validate market
        if self.market not in {"canada", "usa", "north-america"}:
            raise ValueError(
                f"Invalid market: {self.market}. "
                f"Expected one of: canada, usa, north-america"
            )

        # North America = Canada + USA
        if self.market == "north-america":
            feeds = (
                self.JOB_FEEDS["canada"]
                + self.JOB_FEEDS["usa"]
            )
        else:
            feeds = self.JOB_FEEDS[self.market]

        pages = []

        print()
        print(
            f"Starting Built In ingestion "
            f"for market: {self.market}"
        )
        print(
            f"Feeds: {len(feeds)} | "
            f"Pages per feed: {self.PAGES_PER_FEED}"
        )
        print()

        async with async_playwright() as p:

            browser = await p.chromium.launch(
                headless=self.headless
            )

            page = await browser.new_page()

            try:

                for feed_number, feed_url in enumerate(
                    feeds,
                    start=1
                ):
                    print(
                        f"--- Built In Feed "
                        f"{feed_number}/{len(feeds)} ---"
                    )

                    for page_number in range(
                        1,
                        self.PAGES_PER_FEED + 1
                    ):
                        url = self.build_page_url(
                            feed_url,
                            page_number
                        )

                        if url.startswith("/"):
                            url = self.BASE_URL + url

                        print(
                            f"Fetching page "
                            f"{page_number}/"
                            f"{self.PAGES_PER_FEED}"
                        )

                        html = await self.fetch_page(
                            page,
                            url
                        )

                        pages.append(html)

                    print()

            finally:
                await browser.close()

        print(
            f"Built In scraping complete. "
            f"Downloaded {len(pages)} pages."
        )

        return "\n".join(pages)