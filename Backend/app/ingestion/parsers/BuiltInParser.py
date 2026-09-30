import re
from datetime import datetime, timedelta

from bs4 import BeautifulSoup


class BuiltInParser:

    # ---------------------------------------------------------
    # Helper: Convert relative posted time into datetime
    # ---------------------------------------------------------
    def parse_posted_time(self, posted_text: str | None):
        if not posted_text:
            return None
        text = posted_text.lower().strip()
        now = datetime.now()
        # Remove "reposted" so we can parse the remaining time.
        text = text.replace("reposted", "").strip()
        # Special cases
        if "yesterday" in text:
            return now - timedelta(days=1)
        if "an hour" in text:
            return now - timedelta(hours=1)
        if "a minute" in text or "an minute" in text:
            return now - timedelta(minutes=1)
        # Numeric relative times
        match = re.search(r"\d+", text)
        if not match:
            return None
        value = int(match.group())
        if "second" in text:
            return now - timedelta(seconds=value)
        if "minute" in text:
            return now - timedelta(minutes=value)
        if "hour" in text:
            return now - timedelta(hours=value)
        if "day" in text:
            return now - timedelta(days=value)
        return None

    def parse_salary(self, salary_text: str | None):
        if not salary_text:
            return None, None

        values = re.findall(r"[\d,.]+", salary_text)

        if not values:
            return None, None

        numbers = []

        for value in values:
            number = float(value.replace(",", ""))

            if "k" in salary_text.lower():
                number *= 1000

            numbers.append(number)

        if len(numbers) >= 2:
            return numbers[0], numbers[1]

        return numbers[0], None

    # ---------------------------------------------------------
    # Main parser
    # ---------------------------------------------------------
    def parse(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        jobs = []
        # Each Built In job is contained in a job card.
        job_cards = soup.select('[data-id="job-card"]')
        for card in job_cards:
            # -------------------------------------------------
            # Basic job information
            # -------------------------------------------------
            title_element = card.select_one('[data-id="job-card-title"]')
            company_element = card.select_one('[data-id="company-title"]')
            link_element = card.select_one('[data-id="job-card-title"]')
            # -------------------------------------------------
            # Location
            # -------------------------------------------------
            location_element = card.select_one(".fa-location-dot")
            if location_element:
                location_container = location_element.parent.parent
                location = location_container.get_text(strip=True)
            else:
                location = None
            # -------------------------------------------------
            # Remote / onsite
            # -------------------------------------------------
            remote_element = card.select_one(".fa-house-building")
            if remote_element:
                remote_container = remote_element.parent.parent
                remote = remote_container.get_text(strip=True)
            else:
                remote = None
            # -------------------------------------------------
            # Salary
            # -------------------------------------------------
            salary_elements = card.select(
                "span.font-barlow.text-gray-04"
            )

            salary = None

            for element in salary_elements:
                text = element.get_text(" ", strip=True)

                if re.search(r"\d", text):
                    salary = text
                    break

            salary_min, salary_max = self.parse_salary(salary)
            # -------------------------------------------------
            # Experience level
            # -------------------------------------------------
            experience_element = card.select_one(".fa-trophy")
            if experience_element:
                experience_container = experience_element.parent.parent
                experience = experience_container.get_text(strip=True)
            else:
                experience = None
            # -------------------------------------------------
            # Posted date
            # -------------------------------------------------
            time_element = card.select_one("span.fs-xs.fw-bold.bg-gray-01")
            if time_element:
                posted_text = time_element.get_text(strip=True)
            else:
                posted_text = None
            posted_at = self.parse_posted_time(posted_text)
            # -------------------------------------------------
            # Description
            # -------------------------------------------------
            description_element = card.select_one(".collapse .fs-sm.fw-regular")
            description = (
                description_element.get_text(strip=True)
                if description_element
                else None
            )
            # -------------------------------------------------
            # Company logo
            # -------------------------------------------------
            logo_element = card.select_one('[data-id="company-img"]')
            company_logo = logo_element.get("src") if logo_element else None
            # -------------------------------------------------
            # Job ID
            # -------------------------------------------------
            job_id = card.get("id")
            # -------------------------------------------------
            # URL
            # -------------------------------------------------
            main = "https://builtin.com"
            url = (
                main + link_element.get("href")
                if link_element and link_element.get("href")
                else main
            )
            # -------------------------------------------------
            # Build normalized raw job
            # -------------------------------------------------
            jobs.append(
                {
                    "source": "BuiltIn",
                    "source_job_id": job_id,
                    "title": (
                        title_element.get_text(strip=True) if title_element else None
                    ),
                    "company": (
                        company_element.get_text(strip=True)
                        if company_element
                        else None
                    ),
                    "company_logo": company_logo,
                    "url": url,
                    "location": location,
                    "remote": remote,
                    "salary_min": salary_min,
                    "salary_max": salary_max,
                    "experience": experience,
                    "description": description,
                    "posted_at": posted_at,
                }
            )
        return jobs