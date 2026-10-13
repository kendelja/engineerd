from datetime import datetime, timedelta

from app.ingestion.analyzer import (
    GHOST_JUNIOR,
    JUNIOR_FRIENDLY,
    SENIOR,
    analyze_job,
)
from app.ingestion.normalizer import normalize_job
from app.ingestion.parsers.WellfoundParser import WellfoundParser
from app.ingestion.scrapers.WellfoundScraper import WellfoundScraper


def position(job_id, title, info_spans, posted="5 days ago"):
    spans = "".join(info_spans)

    return f"""
    <div class="min-h-[50px] items-end justify-between rounded-2xl px-2 py-2 sm:flex">
      <a class="mr-2 text-sm font-semibold text-brand-burgandy hover:underline"
         href="/jobs/{job_id}-slug">{title}</a>
      {spans}
      <span class="text-xs lowercase text-dark-a md:hidden">{posted}</span>
    </div>"""


def company(name, *positions):
    return f"""
    <div class="mb-6 w-full rounded border border-gray-400 bg-white">
      <a class="text-neutral-1000 hover:underline focus:no-underline">{name}</a>
      {"".join(positions)}
    </div>"""


LOCATION = (
    '<span class="pl-1 text-xs">Remote only • Canada'
    '<span class="badge">+<!-- -->1</span></span>'
)
OFFICE = '<span class="pl-1 text-xs">In office • Vancouver</span>'
CITY_ONLY = '<span class="pl-1 text-xs">Toronto</span>'
SALARY = '<span class="pl-1 text-xs">$75k – $150k CAD • 0.0% – 0.1%</span>'
YEARS = '<span class="pl-1 text-xs">{n} years of exp</span>'


def parse(*companies):
    return WellfoundParser().parse("<html><body>" + "".join(companies) + "</body></html>")


# ------------------------------------------------------------
# Parser
# ------------------------------------------------------------

def test_experience_does_not_overwrite_location():
    # Regression: the last non-salary span used to win, so every
    # location came out as "5 years of exp".
    jobs = parse(
        company(
            "Acme",
            position(111, "Senior QA Engineer", [LOCATION, YEARS.format(n=5)]),
        )
    )

    assert len(jobs) == 1
    assert jobs[0]["location"] == "Canada"
    assert jobs[0]["remote"] == "Remote only"
    assert jobs[0]["years_required"] == 5


def test_info_spans_in_any_order():
    jobs = parse(
        company(
            "Acme",
            position(
                222,
                "Software Engineer",
                [YEARS.format(n=2), SALARY, OFFICE],
            ),
        )
    )

    job = jobs[0]

    assert job["years_required"] == 2
    assert job["location"] == "Vancouver"
    assert job["remote"] == "In office"
    assert job["salary_min"] == 75000
    assert job["salary_max"] == 150000
    assert job["salary_period"] == "annually"


def test_location_without_work_model():
    jobs = parse(company("Acme", position(333, "Developer", [CITY_ONLY])))

    assert jobs[0]["location"] == "Toronto"
    assert jobs[0]["remote"] is None
    assert jobs[0]["years_required"] is None
    assert jobs[0]["salary_period"] is None


def test_zero_years_is_kept():
    jobs = parse(
        company("Acme", position(444, "Software Engineer Intern", [YEARS.format(n=0)]))
    )

    assert jobs[0]["years_required"] == 0


def test_multiple_positions_per_company_and_dedupe_across_pages():
    page = company(
        "Acme",
        position(1, "Backend Engineer", [YEARS.format(n=3)]),
        position(2, "Frontend Engineer", [YEARS.format(n=1)]),
    )

    # The same company shows up again on the next page.
    jobs = parse(page, page)

    assert [job["source_job_id"] for job in jobs] == ["1", "2"]
    assert all(job["company"] == "Acme" for job in jobs)


def test_posted_time_is_relative_to_now():
    job = parse(company("Acme", position(5, "Engineer", [], posted="5 days ago")))[0]

    expected = datetime.now() - timedelta(days=5)

    assert abs((job["posted_at"] - expected).total_seconds()) < 60


# ------------------------------------------------------------
# Through the normalizer / analyzer
# ------------------------------------------------------------

def test_work_model_and_years_reach_the_job():
    raw = parse(
        company(
            "Acme",
            position(7, "Software Engineer", [LOCATION, YEARS.format(n=2)]),
        )
    )[0]

    job = normalize_job(raw)

    assert job.work_model == "Remote"
    assert job.remote_type is True
    assert job.years_required == 2
    assert job.years_evidence


def test_junior_title_asking_for_years_is_ghost_junior():
    result = analyze_job("Junior Software Developer", None, None, years_required=4)

    assert result.fit_label == GHOST_JUNIOR
    assert result.years_required == 4
    assert result.fit_confidence == "high"


def test_structured_years_beat_text_and_label_without_description():
    realistic = analyze_job("Junior Developer", None, None, years_required=1)
    senior = analyze_job("Software Engineer", None, None, years_required=7)

    assert realistic.fit_label == JUNIOR_FRIENDLY
    assert senior.fit_label == SENIOR


# ------------------------------------------------------------
# Scraper (no network)
# ------------------------------------------------------------

def test_scraper_reads_urls_from_config():
    scraper = WellfoundScraper(market="canada")

    assert scraper.paths() == [
        "/role/l/engineer/canada-startups",
        "/role/l/developer/canada-startups",
    ]


def test_north_america_combines_both_markets():
    paths = WellfoundScraper(market="north-america").paths()

    assert any("canada-startups" in p for p in paths)
    assert any("united-states" in p for p in paths)


def test_us_urls_are_not_the_redirecting_slug():
    assert not any(
        "usa-startups" in p for p in WellfoundScraper(market="usa").paths()
    )


def test_page_urls():
    scraper = WellfoundScraper()

    assert scraper.build_page_url("/role/l/engineer/x", 1).endswith("/role/l/engineer/x")
    assert scraper.build_page_url("/role/l/engineer/x", 3).endswith("/role/l/engineer/x?page=3")
