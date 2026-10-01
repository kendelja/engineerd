from playwright.async_api import async_playwright


class WellfoundScraper:

    BASE_URL = "https://wellfound.com"

    JOB_URLS = {
        "canada": [
            "/role/l/engineer/canada-startups",
            "/role/l/developer/canada-startups",
        ],

        "usa": [
            "/role/l/engineer/united-states",
            "/role/l/developer/united-states",
        ],

        "north-america": [
            "/role/l/engineer/north-america",
            "/role/l/developer/north-america",
        ],
    }

    def __init__(self, market="canada", headless=True):
        self.market = market
        self.headless = headless

    async def fetch_jobs_page(self) -> str:
        pages = []

        urls = self.JOB_URLS[self.market]

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless
            )

            page = await browser.new_page()

            try:
                for path in urls:
                    url = f"{self.BASE_URL}{path}"

                    print(
                        f"Fetching Wellfound "
                        f"({self.market}): {url}"
                    )

                    await page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=60000
                    )

                    await page.wait_for_timeout(2000)

                    html = await page.content()

                    pages.append(html)

                    print("Page downloaded.")

            finally:
                await browser.close()

        return "\n".join(pages)