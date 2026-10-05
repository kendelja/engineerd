from datetime import datetime

from app.models.job import Job


def normalize_job(raw_job: dict) -> Job:

    return Job(
        source=raw_job.get("source"),

        source_job_id=raw_job.get("source_job_id"),

        title=clean_text(raw_job.get("title")),
        company=clean_text(raw_job.get("company")),
        company_logo=(raw_job.get("company_logo")),
        location=clean_text(raw_job.get("location")),

        description=clean_text(raw_job.get("description")),

        url=raw_job.get("url"),

        posted_at=parse_date(raw_job.get("posted_at")),
        

        experience_level=clean_text(
            raw_job.get("experience_level")
        ),

        employment_type=clean_text(
            raw_job.get("employment_type")
        ),

        remote_type=bool(raw_job.get("remote_type")),



        salary_min=raw_job.get("salary_min"),
        salary_max=raw_job.get("salary_max"),
        salary_period=clean_text(raw_job.get("salary_period")),
    )


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