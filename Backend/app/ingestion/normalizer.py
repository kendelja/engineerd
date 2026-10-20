from datetime import datetime

from app.ingestion.analyzer import analyze_job
from app.ingestion.eligibility import markets_for_location
from app.models.job import Job


def normalize_job(raw_job: dict) -> Job:

    title = clean_text(raw_job.get("title"))
    description = clean_text(raw_job.get("description"))
    experience_level = clean_text(raw_job.get("experience_level"))

    analysis = analyze_job(
        title,
        description,
        experience_level,
        years_required=raw_job.get("years_required"),
        salary_min=raw_job.get("salary_min"),
        salary_max=raw_job.get("salary_max"),
    )

    work_model = parse_work_model(raw_job)

    return Job(
        source=raw_job.get("source"),

        source_job_id=raw_job.get("source_job_id"),

        title=title,
        company=clean_text(raw_job.get("company")),
        company_logo=(raw_job.get("company_logo")),
        location=clean_text(raw_job.get("location")),

        description=description,

        url=raw_job.get("url"),

        posted_at=parse_date(raw_job.get("posted_at")),
        

        experience_level=experience_level,

        employment_type=clean_text(
            raw_job.get("employment_type")
        ),

        remote_type=(
            None if work_model is None
            else work_model == "Remote"
        ),

        work_model=work_model,

        markets=markets_for_location(clean_text(raw_job.get("location"))),



        salary_min=raw_job.get("salary_min"),
        salary_max=raw_job.get("salary_max"),
        salary_period=clean_text(raw_job.get("salary_period")),

        years_required=analysis.years_required,
        years_evidence=analysis.years_evidence,
        skills=analysis.skills,
        fit_score=analysis.fit_score,
        fit_label=analysis.fit_label,
        fit_reasons=analysis.fit_reasons,
        fit_confidence=analysis.fit_confidence,
    )


def parse_work_model(raw_job: dict):
    """
    Map each source's wording onto Remote / Hybrid / On-site.

    Parsers emit this under "remote" (Built In: "Remote", "Hybrid",
    "In-Office"; SimplifyJobs: "Remote", "Hybrid", "In Person").
    A boolean "remote_type" (Wellfound) is honoured too; False is
    ambiguous (could be hybrid), so it stays unknown.
    """

    value = raw_job.get("remote") or raw_job.get("work_model")

    if not value:
        return "Remote" if raw_job.get("remote_type") is True else None

    text = str(value).lower()

    if "hybrid" in text:
        return "Hybrid"

    if "remote" in text:
        return "Remote"

    if any(
        term in text
        for term in ("in person", "in-person", "office", "on-site", "onsite", "on site")
    ):
        return "On-site"

    return None


def apply_analysis(job: Job, analysis) -> None:
    """Copy a JobAnalysis onto a Job."""

    job.years_required = analysis.years_required
    job.years_evidence = analysis.years_evidence
    job.skills = analysis.skills
    job.fit_score = analysis.fit_score
    job.fit_label = analysis.fit_label
    job.fit_reasons = analysis.fit_reasons
    job.fit_confidence = analysis.fit_confidence


def clean_text(value):

    if value is None:
        return None

    return " ".join(str(value).split())


def parse_date(value):

    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    # TODO:
    # Convert the source's date representation
    # into a Python datetime.

    return None