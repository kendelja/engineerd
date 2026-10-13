import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup


class WellfoundParser:

    # ---------------------------------------------------------
    # Helper: Convert relative posted time into datetime
    # ---------------------------------------------------------
    def parse_posted_time(self, posted_text: str | None):
        if not posted_text:
            return None

        text = posted_text.lower().strip()
        now = datetime.now()

        # Special cases
        if text == "today":
            return now

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

        if "week" in text:
            return now - timedelta(weeks=value)

        if "month" in text:
            # Approximation — useful for sorting/displaying
            return now - timedelta(days=value * 30)

        if "year" in text:
            # Approximation
            return now - timedelta(days=value * 365)

        return None

    def parse_salary(self, salary_text: str | None):
        if not salary_text:
            return None, None

        values = re.findall(r"\$([\d,.]+)k?", salary_text.lower())

        if not values:
            return None, None

        numbers = [
            float(value.replace(",", ""))
            for value in values
        ]

        numbers = [
            value * 1000 if value < 1000 else value
            for value in numbers
        ]

        if len(numbers) >= 2:
            return numbers[0], numbers[1]

        return numbers[0], None

    # "5 years of exp", "0 years of exp"
    EXPERIENCE_PATTERN = re.compile(
        r"(\d+)\s*\+?\s*years?\s*of\s*exp",
        re.IGNORECASE,
    )

    WORK_MODEL_PATTERN = re.compile(
        r"^(?:remote|hybrid|in[- ]office|on[- ]?site|office)\b",
        re.IGNORECASE,
    )

    def split_location(self, text: str):
        """
        "Remote only • Canada" -> ("Remote only", "Canada")
        "In office • Vancouver" -> ("In office", "Vancouver")
        "Toronto"              -> (None, "Toronto")
        """

        parts = [
            part.strip()
            for part in re.split(r"[•·]", text)
            if part.strip()
        ]

        if parts and self.WORK_MODEL_PATTERN.match(parts[0]):
            return parts[0], (" · ".join(parts[1:]) or None)

        return None, text

    def parse(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        jobs = []
        seen_ids = set()

        # Each company card
        job_cards = soup.select(
            "div.mb-6.w-full.rounded.border.border-gray-400.bg-white"
        )

        for card in job_cards:

            # -----------------------------------
            # COMPANY-LEVEL INFORMATION
            # -----------------------------------

            company_element = card.select_one(
                ".text-neutral-1000.hover\\:underline.focus\\:no-underline"
            )

            company = company_element.get_text(strip=True) if company_element else None

            logo_element = card.select_one(
                ".flex.h-14.w-14.justify-center.overflow-hidden.rounded-2xl.border.border-gray-400.bg-gray-100 img"
            )

            if logo_element:
                logo_src = logo_element.get("src")

                if logo_src and "https://" in logo_src:
                    company_logo = "https://" + logo_src.split("https://", 1)[1]
                else:
                    company_logo = logo_src
            else:
                company_logo = None

            # -----------------------------------
            # FIND ALL POSITIONS IN THIS COMPANY
            # -----------------------------------

            positions = card.select(
                "div.min-h-\\[50px\\].items-end.justify-between.rounded-2xl.px-2.py-2.sm\\:flex"
            )

            for position in positions:

                # Job title + URL
                link_element = position.select_one(
                    "a.mr-2.text-sm.font-semibold.text-brand-burgandy.hover\\:underline"
                )

                title = link_element.get_text(strip=True) if link_element else None

                url = (
                    "https://wellfound.com" + link_element.get("href")
                    if link_element and link_element.get("href")
                    else "https://wellfound.com"
                )

                # -----------------------------------
                # SALARY + LOCATION
                # -----------------------------------

                # Each position lists up to three of these, in no
                # fixed order: location / work model, salary, and
                # required experience ("5 years of exp"). Classify
                # by content so one never overwrites another.
                info_elements = position.find_all("span", class_="pl-1 text-xs")

                salary = None
                location = None
                work_model_text = None
                years_required = None

                for element in info_elements:
                    # Own text only: the location span nests a
                    # "+ 3" badge for additional locations.
                    text = " ".join(
                        "".join(
                            element.find_all(string=True, recursive=False)
                        ).split()
                    )

                    if not text:
                        continue

                    years_match = self.EXPERIENCE_PATTERN.search(text)

                    if "$" in text:
                        salary = text
                    elif years_match:
                        years_required = int(years_match.group(1))
                    else:
                        work_model_text, location = self.split_location(text)

                # Convert salary string into database-ready values
                salary_min, salary_max = self.parse_salary(salary)

                # Wellfound compensation is always quoted per year.
                salary_period = "annually" if salary_min is not None else None

                # -----------------------------------
                # POSTED DATE
                # -----------------------------------

                time_element = position.select_one(
                    ".text-xs.lowercase.text-dark-a.md\\:hidden"
                )

                if time_element:
                    posted_text = time_element.get_text(strip=True)
                else:
                    # Desktop version
                    time_element = position.select_one(".text-xs.lowercase.text-dark-a")

                    posted_text = (
                        time_element.get_text(strip=True) if time_element else None
                    )

                posted_at = self.parse_posted_time(posted_text)

                # -----------------------------------
                # JOB ID
                # -----------------------------------

                job_id = None

                if link_element and link_element.get("href"):
                    href = link_element.get("href")

                    match = re.search(r"/jobs/(\d+)", href)

                    if match:
                        job_id = match.group(1)

                # The same position can appear on several pages
                # (engineer and developer role pages overlap).
                if job_id:
                    if job_id in seen_ids:
                        continue

                    seen_ids.add(job_id)

                # -----------------------------------
                # CREATE ONE JOB
                # -----------------------------------

                jobs.append(
                    {
                        "source": "Wellfound",
                        "source_job_id": job_id,
                        "title": title,
                        "company": company,
                        "company_logo": company_logo,
                        "url": url,
                        "location": location,
                        "remote": work_model_text,
                        "salary_min": salary_min,
                        "salary_max": salary_max,
                        "salary_period": salary_period,
                        # Structured; the analyzer prefers this
                        # over mining text.
                        "years_required": years_required,
                        "description": None,
                        "posted_at": posted_at,
                    }
                )

        return jobs
