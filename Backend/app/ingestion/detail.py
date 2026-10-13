"""
Detail-page enrichment.

Listing pages only carry a short blurb (Built In) or no text at all
(SimplifyJobs), which is not enough to tell how much experience a job
really asks for. This module opens each job's own page, pulls out the
posting text, and hands it to the analyzer.

The text is analysed and then discarded -- it is never stored or
shown, only the derived years / skills / fit fields are kept.
"""

import asyncio
import random
from dataclasses import dataclass
from typing import Callable, Optional

from bs4 import BeautifulSoup, Tag
from playwright.async_api import async_playwright


# ============================================================
# EXTRACTORS (pure: HTML in, posting text out)
# ============================================================

def _text(element: Tag) -> str:
    return " ".join(element.get_text(" ", strip=True).split())


def extract_builtin_text(html: str) -> Optional[str]:
    """
    Built In: the description lives in div#job-post-body-<id>; the
    "Skills Required" block sits in the same column and usually states
    the years requirement most plainly, so take the whole column.
    """

    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style"]):
        tag.decompose()

    body = soup.select_one('[id^="job-post-body-"]')

    if body is None:
        return None

    column = body.find_parent(
        class_=lambda value: value and "col-lg-6" in value.split()
    )

    return _text(column or body) or None


def extract_simplify_text(html: str) -> Optional[str]:
    """
    SimplifyJobs: everything between the "About the job" and
    "About the company" headings. The rest of the page is company
    marketing ("60 years of combined experience"), which would
    otherwise look like requirements.
    """

    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style"]):
        tag.decompose()

    start = soup.find(
        "h2",
        string=lambda value: value and value.strip().lower() == "about the job",
    )

    if start is None:
        return None

    parts: list[str] = []

    for element in start.next_elements:
        if isinstance(element, Tag) and element.name == "h2":
            if element is not start:
                break

        if isinstance(element, str) and element.parent.name not in (
            "script",
            "style",
        ):
            parts.append(element.strip())

    text = " ".join(" ".join(parts).split())

    return text or None


# ============================================================
# FETCHER
# ============================================================

@dataclass
class DetailSource:
    name: str
    page_url: Callable          # job -> URL to open
    ready_selector: str         # element that signals the text rendered
    extract: Callable           # html -> text | None


def _builtin_url(job) -> str:
    return job.url


def _simplify_url(job) -> str:
    # job.url is a redirecting "click" link; the /p/ page has the posting.
    return f"https://simplify.jobs/p/{job.source_job_id}"


BUILT_IN = DetailSource(
    name="BuiltIn",
    page_url=_builtin_url,
    ready_selector='[id^="job-post-body-"]',
    extract=extract_builtin_text,
)

SIMPLIFY_JOBS = DetailSource(
    name="SimplifyJobs",
    page_url=_simplify_url,
    ready_selector="h2:has-text('About the job')",
    extract=extract_simplify_text,
)

SOURCES = {
    BUILT_IN.name: BUILT_IN,
    SIMPLIFY_JOBS.name: SIMPLIFY_JOBS,
}


class DetailFetcher:
    """
    Opens job pages one at a time with a random pause between
    requests. A page that fails to load or parse yields None; one
    bad page never aborts the batch.
    """

    def __init__(
        self,
        source: DetailSource,
        delay_seconds: tuple[float, float] = (1.5, 3.0),
        max_pages: int = 300,
        headless: bool = True,
    ):
        self.source = source
        self.delay_seconds = delay_seconds
        self.max_pages = max_pages
        self.headless = headless

    async def fetch_texts(self, jobs: list) -> list[Optional[str]]:
        """Return posting text for each job, aligned with `jobs`."""

        results: list[Optional[str]] = [None] * len(jobs)

        if not jobs:
            return results

        total = min(len(jobs), self.max_pages)

        print(
            f"Reading {total} {self.source.name} job pages "
            f"(~{self.delay_seconds[0]:.1f}-{self.delay_seconds[1]:.1f}s each)..."
        )

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()

            try:
                for index, job in enumerate(jobs[:total]):
                    results[index] = await self._fetch_one(page, job)

                    if (index + 1) % 10 == 0 or index + 1 == total:
                        found = sum(1 for r in results if r)
                        print(f"  {index + 1}/{total} pages read ({found} with text)")

                    await asyncio.sleep(random.uniform(*self.delay_seconds))

            finally:
                await browser.close()

        return results

    async def _fetch_one(self, page, job) -> Optional[str]:
        url = self.source.page_url(job)

        try:
            response = await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=45000,
            )

            if response is not None and response.status >= 400:
                return None

            await page.wait_for_selector(
                self.source.ready_selector,
                timeout=15000,
            )

            # Let late-rendering sections settle.
            await page.wait_for_timeout(500)

            return self.source.extract(await page.content())

        except Exception as error:
            print(f"  could not read {url}: {type(error).__name__}")
            return None


def fetcher_for(source_name: str, **kwargs) -> DetailFetcher:
    return DetailFetcher(SOURCES[source_name], **kwargs)
