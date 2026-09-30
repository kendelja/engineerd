from app.database.connection import get_connection
from app.models.job import Job


def insert_job(job: Job):

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO jobs (
                    source,
                    source_job_id,
                    title,
                    company,
                    company_logo,
                    location,
                    description,
                    url,
                    posted_at,
                    experience_level,
                    employment_type,
                    remote_type,
                    salary_min,
                    salary_max
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (source, source_job_id)
                DO NOTHING
                """,
                (
                    job.source,
                    job.source_job_id,
                    job.title,
                    job.company,
                    job.company_logo,
                    job.location,
                    job.description,
                    job.url,
                    job.posted_at,
                    job.experience_level,
                    job.employment_type,
                    job.remote_type,
                    job.salary_min,
                    job.salary_max
                )
            )
        connection.commit()

    finally:
        connection.close()


def get_jobs(limit=100):

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    id,
                    source,
                    title,
                    company,
                    company_logo,
                    location,
                    description,
                    salary_min,
                    salary_max,
                    url,
                    posted_at,
                    experience_level,
                    employment_type,
                    remote_type
                FROM jobs
                ORDER BY
                    posted_at DESC NULLS LAST,
                    discovered_at DESC
                LIMIT %s
                """,
                (limit,)
            )

            rows = cursor.fetchall()

            columns = [
                "id",
                "source",
                "title",
                "company",
                "company_logo",
                "location",
                "description",
                "salary_min",
                "salary_max",
                "url",
                "posted_at",
                "experience_level",
                "employment_type",
                "remote_type"
            ]

            return [
                dict(zip(columns, row))
                for row in rows
            ]

    finally:
        connection.close()