
from datetime import datetime
from zoneinfo import ZoneInfo
import json

# Stored times are naive local (Toronto), matching the other sources.
LOCAL_TZ = ZoneInfo("America/Toronto")


class SimplifyJobsParser:
    SOURCE = "SimplifyJobs"
    BASE_URL = "https://simplify.jobs/jobs"

    def parse(self, payload: str) -> list[dict]:
        """
        Parse the SimplifyJobs multi_search JSON response
        into Engineerd's normalized raw-job format.
        """

        data = json.loads(payload) if isinstance(payload, str) else payload
        jobs = []
        seen = set()

        for result in data.get("results", []):
            for hit in result.get("hits", []):
                document = hit.get("document", {})

                job_id = (
                    document.get("posting_id")
                    or document.get("id")
                )
                title = document.get("title")
                company = document.get("company_name")

                if not job_id or not title or not company:
                    continue

                # Avoid duplicate records within this response.
                if job_id in seen:
                    continue
                seen.add(job_id)

                locations = document.get("locations") or []
                experience_levels = (
                    document.get("experience_level") or []
                )

                min_salary = document.get("min_salary")
                max_salary = document.get("max_salary")

                # SimplifyJobs provides salary values as numbers.
                # Do not infer a salary period that the API
                # does not explicitly provide.
                start_date = document.get("start_date")
                posted_at = None

                if isinstance(start_date, (int, float)) and start_date > 0:
                    posted_at = datetime.fromtimestamp(
                        start_date,
                        tz=LOCAL_TZ
                    ).replace(tzinfo=None)

                jobs.append({
                    "source": self.SOURCE,
                    "source_job_id": str(job_id),
                    "title": title.strip(),
                    "company": company.strip(),
                    "company_logo": document.get("company_logo"),
                    "url": f"https://simplify.jobs/jobs/click/{job_id}",
                    "location": ", ".join(locations) if locations else None,
                    "remote": document.get("travel_requirements"),
                    "salary_min": min_salary,
                    "salary_max": max_salary,
                    "salary_period": None,
                    "experience_level": ", ".join(experience_levels) or None,
                    "description": None,
                    "posted_at": posted_at,
                })

        return jobs
