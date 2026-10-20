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
                    work_model,
                    markets,
                    salary_min,
                    salary_max,
                    salary_period,
                    years_required,
                    years_evidence,
                    skills,
                    fit_score,
                    fit_label,
                    fit_reasons,
                    fit_confidence,
                    detail_checked_at
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s
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
                    job.work_model,
                    job.markets,
                    job.salary_min,
                    job.salary_max,
                    job.salary_period,
                    job.years_required,
                    job.years_evidence,
                    job.skills,
                    job.fit_score,
                    job.fit_label,
                    job.fit_reasons,
                    job.fit_confidence,
                    job.detail_checked_at,
                )
            )
        connection.commit()

    finally:
        connection.close()


def get_jobs(
    limit=100,
    fit=None,
    exclude_fit=None,
    max_years=None,
    skills=None,
    market=None,
):
    """
    Return jobs, newest first.

    fit          -- only these fit labels
    exclude_fit  -- drop these fit labels
    max_years    -- drop jobs that ask for more than this many years
                    (jobs with no detected requirement are kept)
    skills       -- jobs mentioning ALL of these skills
    """

    conditions = []
    params = []

    if market:
        conditions.append("%s = ANY(markets)")
        params.append(market)

    if fit:
        conditions.append("fit_label = ANY(%s)")
        params.append(list(fit))

    if exclude_fit:
        conditions.append(
            "(fit_label IS NULL OR NOT (fit_label = ANY(%s)))"
        )
        params.append(list(exclude_fit))

    if max_years is not None:
        conditions.append(
            "(years_required IS NULL OR years_required <= %s)"
        )
        params.append(max_years)

    if skills:
        conditions.append("skills @> %s::text[]")
        params.append(list(skills))

    where = (
        "WHERE " + " AND ".join(conditions)
        if conditions
        else ""
    )

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                f"""
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
                    salary_period,
                    url,
                    posted_at,
                    experience_level,
                    employment_type,
                    remote_type,
                    work_model,
                    years_required,
                    years_evidence,
                    skills,
                    fit_score,
                    fit_label,
                    fit_reasons,
                    fit_confidence
                FROM jobs
                {where}
                ORDER BY
                    posted_at DESC NULLS LAST,
                    discovered_at DESC
                LIMIT %s
                """,
                (*params, limit)
            )

            rows = cursor.fetchall()

            columns = [column[0] for column in cursor.description]

            return [
                dict(zip(columns, row))
                for row in rows
            ]

    finally:
        connection.close()


def get_fit_summary():
    """Counts of each fit label overall and per source."""

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    source,
                    COALESCE(fit_label, 'unanalyzed') AS fit_label,
                    COUNT(*) AS jobs,
                    COUNT(years_required) AS with_years
                FROM jobs
                GROUP BY source, COALESCE(fit_label, 'unanalyzed')
                ORDER BY source, fit_label
                """
            )

            rows = cursor.fetchall()

    finally:
        connection.close()

    by_label = {}
    by_source = {}
    total = 0
    with_years = 0

    for source, label, count, years_count in rows:
        total += count
        with_years += years_count

        by_label[label] = by_label.get(label, 0) + count

        by_source.setdefault(source, {})[label] = count

    return {
        "total": total,
        "years_detected": with_years,
        "by_label": by_label,
        "by_source": by_source,
    }


def update_job_analysis(job_id: int, analysis, detail_checked: bool = False):
    """
    Persist a JobAnalysis for an existing row.

    detail_checked -- True when the analysis came from the job's
                      detail page (stamps detail_checked_at).
    """

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                UPDATE jobs
                SET
                    years_required = %s,
                    years_evidence = %s,
                    skills = %s,
                    fit_score = %s,
                    fit_label = %s,
                    fit_reasons = %s,
                    fit_confidence = %s,
                    detail_checked_at = CASE
                        WHEN %s THEN CURRENT_TIMESTAMP
                        ELSE detail_checked_at
                    END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    analysis.years_required,
                    analysis.years_evidence,
                    analysis.skills,
                    analysis.fit_score,
                    analysis.fit_label,
                    analysis.fit_reasons,
                    analysis.fit_confidence,
                    detail_checked,
                    job_id,
                )
            )

        connection.commit()

    finally:
        connection.close()


def record_detail_failure(job_id: int):
    """Count a failed detail-page fetch so dead links stop retrying."""

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                "UPDATE jobs SET detail_attempts = detail_attempts + 1 WHERE id = %s",
                (job_id,)
            )

        connection.commit()

    finally:
        connection.close()


def refresh_work_model(job: Job):
    """Fill in work model on a job that is already stored."""

    if job.work_model is None:
        return

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                UPDATE jobs
                SET work_model = %s, remote_type = %s
                WHERE source = %s
                AND source_job_id = %s
                AND work_model IS DISTINCT FROM %s
                """,
                (
                    job.work_model,
                    job.remote_type,
                    job.source,
                    job.source_job_id,
                    job.work_model,
                )
            )

        connection.commit()

    finally:
        connection.close()


def get_pending_detail_jobs(
    source=None,
    limit=None,
    max_attempts=3,
    include_checked=False,
):
    """
    Jobs whose detail page has not been read yet (newest first).

    include_checked -- also return jobs that were already enriched
                       (used to re-run after changing analyzer rules).
    """

    conditions = ["detail_attempts < %s"]
    params = [max_attempts]

    if not include_checked:
        conditions.append("detail_checked_at IS NULL")

    if source:
        conditions.append("source = %s")
        params.append(source)

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                f"""
                SELECT id, source, source_job_id, url, title,
                       experience_level, salary_min, salary_max
                FROM jobs
                WHERE {" AND ".join(conditions)}
                ORDER BY posted_at DESC NULLS LAST, id DESC
                {"LIMIT %s" if limit else ""}
                """,
                (*params, limit) if limit else tuple(params)
            )

            columns = [column[0] for column in cursor.description]

            return [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]

    finally:
        connection.close()


def clear_jobs():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM jobs")

        connection.commit()

    finally:
        connection.close()


def get_daily_postings(days=14, market=None):
    """
    Jobs per posted day for the last `days` days, oldest first.
    Days with no postings are included as zero so the chart has no gaps.
    """

    from datetime import date, timedelta

    today = date.today()
    start = today - timedelta(days=days - 1)

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT posted_at::date AS day, COUNT(*)
                FROM jobs
                WHERE posted_at IS NOT NULL
                AND posted_at::date >= %s
                AND (%s::text IS NULL OR %s::text = ANY(markets))
                GROUP BY 1
                """,
                (start, market, market)
            )

            counts = {row[0]: row[1] for row in cursor.fetchall()}

    finally:
        connection.close()

    return [
        {
            "date": (start + timedelta(days=offset)).isoformat(),
            "count": counts.get(start + timedelta(days=offset), 0),
        }
        for offset in range(days)
    ]


def get_top_skills(limit=3, market=None):
    """Most-mentioned skills across all postings, with posting counts."""

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT skill, COUNT(*) AS postings
                FROM jobs, UNNEST(skills) AS skill
                WHERE (%s::text IS NULL OR %s::text = ANY(markets))
                GROUP BY skill
                ORDER BY postings DESC, skill
                LIMIT %s
                """,
                (market, market, limit)
            )

            return [
                {"skill": skill, "postings": postings}
                for skill, postings in cursor.fetchall()
            ]

    finally:
        connection.close()
