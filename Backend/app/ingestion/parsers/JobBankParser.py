import re
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup


class JobBankParser:

    def parse(self, html: str):
        soup = BeautifulSoup(html, "html.parser")

        search_marker = soup.find(
            string=lambda text: text and
            "ENGINERD_JOB_BANK_SEARCH_RESULTS" in text
        )

        detail_marker = soup.find(
            string=lambda text: text and
            "ENGINERD_JOB_BANK_DETAIL_PAGES" in text
        )

        if not search_marker or not detail_marker:
            print(
                "Job Bank search/detail sections were not found."
            )
            return []

        jobs = {}

        current = search_marker

        while current and current != detail_marker:

            if getattr(current, "name", None) == "a":

                if "resultJobItem" in current.get("class", []):
                    job = self.parse_search_result(current)

                    if job:
                        jobs[job["source_job_id"]] = job

            current = current.find_next()

        detail_markers = re.findall(
            r"<!-- JOB_BANK_URL: (.*?) -->",
            html
        )

        for job_url in detail_markers:

            detail_start = html.find(
                f"<!-- JOB_BANK_URL: {job_url} -->"
            )

            if detail_start == -1:
                continue

            detail_start += len(
                f"<!-- JOB_BANK_URL: {job_url} -->"
            )

            next_marker = html.find(
                "<!-- JOB_BANK_URL:",
                detail_start
            )

            if next_marker == -1:
                detail_html = html[detail_start:]
            else:
                detail_html = html[
                    detail_start:next_marker
                ]

            apply_url = self.parse_apply_url(
                detail_html
            )

            if not apply_url:
                print(
                    f"No external apply URL found for: "
                    f"{job_url}"
                )
                continue

            source_job_id = self.extract_job_id(
                job_url
            )

            if source_job_id not in jobs:
                continue

            jobs[source_job_id]["url"] = apply_url

        valid_jobs = [
            job
            for job in jobs.values()
            if job.get("url")
        ]

        print(
            f"Parsed {len(valid_jobs)} Job Bank jobs "
            f"with application URLs."
        )

        return valid_jobs

    def parse_search_result(self, card):

        href = card.get("href")

        if not href:
            return None

        source_job_id = self.extract_job_id(
            href
        )

        if not source_job_id:
            return None

        title_element = card.select_one(
            "h3.title .noctitle"
        )

        company_element = card.select_one(
            "li.business"
        )

        location_element = card.select_one(
            "li.location"
        )

        salary_element = card.select_one(
            "li.salary"
        )

        date_element = card.select_one(
            "li.date"
        )

        # -----------------------------------------
        # Title
        # -----------------------------------------

        title = self.clean_title(
            title_element.get_text(
                " ",
                strip=True
            )
            if title_element
            else None
        )

        # -----------------------------------------
        # Company
        # -----------------------------------------

        company = self.clean_text(
            company_element.get_text(
                " ",
                strip=True
            )
            if company_element
            else None
        )

        # -----------------------------------------
        # Location
        # -----------------------------------------

        location = self.clean_location(
            location_element.get_text(
                " ",
                strip=True
            )
            if location_element
            else None
        )

        # -----------------------------------------
        # Salary
        # -----------------------------------------

        salary_text = (
            salary_element.get_text(
                " ",
                strip=True
            )
            if salary_element
            else None
        )

        salary_min, salary_max, salary_period = self.parse_salary(
            salary_text
        )

        # -----------------------------------------
        # Posted date
        # -----------------------------------------

        posted_text = (
            date_element.get_text(
                " ",
                strip=True
            )
            if date_element
            else None
        )

        posted_at = self.parse_posted_date(
            posted_text
        )

        # -----------------------------------------
        # Temporary Job Bank URL
        #
        # This gets replaced later with the actual
        # external application URL.
        # -----------------------------------------

        job_url = (
            href
            if href.startswith("http")
            else urljoin(
                "https://www.jobbank.gc.ca",
                href
            )
        )

        return {
            "source": "Job Bank",
            "source_job_id": source_job_id,
            "title": title,
            "company": company,
            "company_logo": "/JobBank.png",
            "location": location,
            "description": None,
            "url": job_url,
            "posted_at": posted_at,
            "experience_level": None,
            "employment_type": None,
            "remote_type": None,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_period": salary_period,
        }

    def parse_apply_url(self, html):

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        external_link = soup.select_one(
            "#externalJobLink"
        )

        if not external_link:
            return None

        href = external_link.get(
            "href"
        )

        if not href:
            return None

        return href.strip()

    def extract_job_id(self, url):

        match = re.search(
            r"/jobsearch/jobposting/(\d+)",
            url
        )

        if not match:
            return None

        return match.group(1)

    def parse_posted_date(self, value):

        if not value:
            return None

        value = value.strip()

        try:
            return datetime.strptime(
                value,
                "%B %d, %Y"
            )

        except ValueError:
            return None

    def parse_salary(self, salary_text):

        if not salary_text:
            return None, None, None

        salary_text = self.clean_text(
            salary_text
        )

        salary_text = re.sub(
            r"^Salary\s*",
            "",
            salary_text,
            flags=re.IGNORECASE
        )

        matches = re.findall(
            r"\$\s*([\d,]+(?:\.\d{1,2})?)",
            salary_text
        )

        if not matches:
            return None, None, None

        values = []

        for value in matches:
            try:
                values.append(
                    float(value.replace(",", ""))
                )
            except ValueError:
                continue

        if not values:
            return None, None, None

        period_match = re.search(
            r"\b(hourly|daily|monthly|annually)\b",
            salary_text,
            flags=re.IGNORECASE
        )

        salary_period = None

        if period_match:
            salary_period = (
                period_match.group(1).lower()
            )

        if len(values) >= 2:
            return (
                values[0],
                values[1],
                salary_period
            )

        return (
            values[0],
            None,
            salary_period
        )

    def clean_location(self, value):

        if not value:
            return None

        value = self.clean_text(
            value
        )

        # Job Bank sometimes includes the
        # accessibility label "Location".
        value = re.sub(
            r"^Location\s*",
            "",
            value,
            flags=re.IGNORECASE
        )

        return value

    def clean_title(self, value):

        if not value:
            return None

        value = self.clean_text(
            value
        )

        # Job Bank frequently returns titles in
        # lowercase. Capitalize normal words while
        # preserving common technical casing.
        words = value.split()

        cleaned_words = []

        special_casing = {
            "ai": "AI",
            "api": "API",
            "apis": "APIs",
            "ar": "AR",
            "aws": "AWS",
            "azure": "Azure",
            "c++": "C++",
            "c#": "C#",
            "css": "CSS",
            "devops": "DevOps",
            "etl": "ETL",
            "gis": "GIS",
            "html": "HTML",
            "ios": "iOS",
            "it": "IT",
            "java": "Java",
            "javascript": "JavaScript",
            "js": "JS",
            "kotlin": "Kotlin",
            "ml": "ML",
            "mysql": "MySQL",
            "node": "Node",
            "node.js": "Node.js",
            "php": "PHP",
            "postgresql": "PostgreSQL",
            "python": "Python",
            "react": "React",
            "react.js": "React.js",
            "sql": "SQL",
            "typescript": "TypeScript",
            "ui": "UI",
            "ux": "UX",
            "vue": "Vue",
            "web": "Web",
        }

        for word in words:

            stripped = word.strip(
                ".,()[]{}:;"
            )

            lowercase = stripped.lower()

            if lowercase in special_casing:

                replacement = special_casing[
                    lowercase
                ]

                # Preserve punctuation attached to
                # the original word.
                prefix = word[
                    :len(word) - len(word.lstrip(
                        ".,()[]{}:;"
                    ))
                ]

                suffix = word[
                    len(word.rstrip(
                        ".,()[]{}:;"
                    )):]
                
                cleaned_words.append(
                    prefix +
                    replacement +
                    suffix
                )

            else:
                cleaned_words.append(
                    word[:1].upper() +
                    word[1:]
                )

        return " ".join(
            cleaned_words
        )

    def clean_text(self, value):

        if value is None:
            return None

        return " ".join(
            str(value).split()
        )