import asyncio
from urllib.parse import urljoin

from playwright.async_api import async_playwright


class JobBankScraper:

    BASE_URL = "https://www.jobbank.gc.ca"

    SEARCH_URL = (
        "https://www.jobbank.gc.ca/jobsearch/jobsearch"
        "?fcid=5169"
        "&fcid=12083"
        "&fcid=17880"
        "&fcid=24510"
        "&fcid=25803"
        "&fcid=296553"
        "&fcid=296554"
        "&fcid=296805"
        "&fn21=21230"
        "&fn21=21231"
        "&fn21=21232"
        "&fn21=21234"
        "&fn21=94153"
        "&page=1"
        "&sort=D"
        "&term=data+engineer"
        "&term=developer"
        "&term=engineer"
        "&term=software+engineer%2C+software"
    )

    MORE_RESULTS_CLICKS = 2
    CONCURRENT_PAGES = 5

    def __init__(self, market="canada", headless=True):
        self.market = market
        self.headless = headless

    async def wait_for_results(self, page):
        try:
            await page.locator(
                "a.resultJobItem"
            ).first.wait_for(
                state="visible",
                timeout=30000
            )

            print("Job Bank results loaded.")
            return True

        except Exception as error:
            print(
                f"Timed out waiting for Job Bank results: {error}"
            )

            return False

    async def expand_results(self, page):
        for click_number in range(
            1,
            self.MORE_RESULTS_CLICKS + 1
        ):
            button = page.locator("#moreresultbutton")

            try:
                await button.wait_for(
                    state="visible",
                    timeout=15000
                )
            except Exception:
                print(
                    f"More Results button not found "
                    f"for click {click_number}."
                )
                break

            print(
                f"Clicking More Results "
                f"({click_number}/{self.MORE_RESULTS_CLICKS})..."
            )

            try:
                previous_count = await page.locator(
                    "a.resultJobItem"
                ).count()

                await button.click()

                # Wait for additional results to appear.
                try:
                    await page.wait_for_function(
                        """
                        (previousCount) => {
                            return document.querySelectorAll(
                                "a.resultJobItem"
                            ).length > previousCount;
                        }
                        """,
                        previous_count,
                        timeout=15000
                    )
                except Exception:
                    # The button may have completed without adding
                    # more results, so continue rather than failing.
                    await page.wait_for_timeout(2000)

            except Exception as error:
                print(
                    f"Failed clicking More Results: {error}"
                )
                break

    async def collect_job_urls(self, page):
        try:
            await page.locator(
                "a.resultJobItem"
            ).first.wait_for(
                state="attached",
                timeout=15000
            )
        except Exception:
            print("No Job Bank result cards appeared.")
            return []

        cards = page.locator("a.resultJobItem")

        count = await cards.count()

        print(
            f"Found {count} Job Bank result cards."
        )

        job_urls = []

        for index in range(count):
            href = await cards.nth(index).get_attribute(
                "href"
            )

            if not href:
                continue

            job_url = urljoin(
                self.BASE_URL,
                href
            )

            if job_url not in job_urls:
                job_urls.append(job_url)

        print(
            f"Collected {len(job_urls)} unique "
            f"Job Bank posting URLs."
        )

        return job_urls

    async def fetch_job_page(
        self,
        context,
        job_url,
        index,
        total
    ):
        page = await context.new_page()

        try:
            print(
                f"Fetching Job Bank job "
                f"{index}/{total}"
            )

            await page.goto(
                job_url,
                wait_until="domcontentloaded",
                timeout=30000
            )

            try:
                await page.locator(
                    "#externalJobLink"
                ).wait_for(
                    state="attached",
                    timeout=10000
                )

                print(
                    f"External apply link found "
                    f"for job {index}/{total}"
                )

            except Exception:
                print(
                    f"No external apply link found "
                    f"for job {index}/{total}"
                )

            html = await page.content()

            return {
                "url": job_url,
                "html": html
            }

        except Exception as error:
            print(
                f"Failed to fetch Job Bank job "
                f"{index}/{total}: {error}"
            )

            return None

        finally:
            await page.close()

    async def fetch_job_pages(
        self,
        context,
        job_urls
    ):
        total = len(job_urls)

        semaphore = asyncio.Semaphore(
            self.CONCURRENT_PAGES
        )

        async def fetch_with_limit(
            index,
            job_url
        ):
            async with semaphore:
                return await self.fetch_job_page(
                    context,
                    job_url,
                    index,
                    total
                )

        tasks = [
            fetch_with_limit(
                index,
                job_url
            )
            for index, job_url in enumerate(
                job_urls,
                start=1
            )
        ]

        results = await asyncio.gather(
            *tasks
        )

        return [
            result
            for result in results
            if result is not None
        ]

    async def fetch_jobs_page(self) -> str:
        if self.market != "canada":
            print(
                f"Skipping Job Bank. "
                f"Market '{self.market}' is not Canada."
            )

            return ""

        print("Starting Job Bank ingestion...")

        async with async_playwright() as p:

            browser = await p.chromium.launch(
                headless=self.headless
            )

            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/151.0.0.0 "
                    "Safari/537.36"
                ),
                viewport={
                    "width": 1920,
                    "height": 1080
                }
            )

            search_page = await context.new_page()

            try:
                # -------------------------------------------------
                # 1. Establish a Job Bank browser session first.
                # -------------------------------------------------

                print("Opening Job Bank...")

                await search_page.goto(
                    self.BASE_URL,
                    wait_until="domcontentloaded",
                    timeout=30000
                )

                await search_page.wait_for_timeout(
                    2000
                )

                print(
                    "Job Bank session established."
                )

                # -------------------------------------------------
                # 2. Navigate to the actual search page.
                # -------------------------------------------------

                print(
                    f"Fetching Job Bank search: "
                    f"{self.SEARCH_URL}"
                )

                await search_page.goto(
                    self.SEARCH_URL,
                    wait_until="commit",
                    timeout=30000
                )

                print(
                    "Job Bank search navigation started."
                )

                # Give the JSF/PrimeFaces page time to build.
                await search_page.wait_for_timeout(
                    5000
                )

                # -------------------------------------------------
                # 3. Wait for actual job cards.
                # -------------------------------------------------

                results_loaded = await self.wait_for_results(
                    search_page
                )

                if not results_loaded:
                    print(
                        "Job Bank search results "
                        "could not be loaded."
                    )

                    print(
                        "Current URL:",
                        search_page.url
                    )

                    print(
                        "Page title:",
                        await search_page.title()
                    )

                    # Useful diagnostic if Job Bank again
                    # returns only the <head>.
                    html = await search_page.content()

                    print(
                        f"Received HTML length: "
                        f"{len(html)} characters"
                    )

                    return ""

                # -------------------------------------------------
                # 4. Load two additional result batches.
                # -------------------------------------------------

                await self.expand_results(
                    search_page
                )

                await search_page.wait_for_timeout(
                    1000
                )

                # -------------------------------------------------
                # 5. Collect individual posting URLs.
                # -------------------------------------------------

                job_urls = await self.collect_job_urls(
                    search_page
                )

                search_html = await search_page.content()

            finally:
                await search_page.close()

            # -----------------------------------------------------
            # 6. Visit each posting concurrently.
            # -----------------------------------------------------

            print(
                f"Fetching {len(job_urls)} Job Bank postings "
                f"with {self.CONCURRENT_PAGES} concurrent pages..."
            )

            detail_pages = await self.fetch_job_pages(
                context,
                job_urls
            )

            await context.close()
            await browser.close()

        # ---------------------------------------------------------
        # 7. Combine search results + detail pages.
        #
        # The parser will:
        # - parse the cards
        # - match each posting ID
        # - find #externalJobLink
        # - replace the temporary Job Bank URL
        #   with the external application URL
        # ---------------------------------------------------------

        output = [
            "<!-- ENGINERD_JOB_BANK_SEARCH_RESULTS -->",
            search_html,
            "<!-- ENGINERD_JOB_BANK_DETAIL_PAGES -->",
        ]

        for detail in detail_pages:

            output.append(
                f'<!-- JOB_BANK_URL: {detail["url"]} -->'
            )

            output.append(
                detail["html"]
            )

        return "\n".join(output)