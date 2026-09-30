from playwright.async_api import async_playwright


class WellfoundScraper:

    BASE_URL = "https://wellfound.com"

    # Multiple Wellfound feeds for broader software/tech coverage
    JOB_URLS = [
        "/role/l/engineer/north-america",
        "/role/l/developer/north-america",
    ]

    def __init__(self, headless=True):
        self.headless = headless

    async def fetch_jobs_page(self) -> str:
        pages = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless
            )

            page = await browser.new_page()

            try:
                for path in self.JOB_URLS:
                    url = f"{self.BASE_URL}{path}"

                    print(f"Fetching Wellfound: {url}")

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