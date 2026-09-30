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

    def parse(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        jobs = []

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

                info_elements = position.find_all("span", class_="pl-1 text-xs")

                salary = None
                location = None
                remote_type = False

                for element in info_elements:
                    text = element.get_text(" ", strip=True)

                    if "$" in text:
                        salary = text
                    else:
                        location = text

                        if "remote" in text.lower():
                            remote_type = True

                # Convert salary string into database-ready values
                salary_min, salary_max = self.parse_salary(salary)

                # -----------------------------------
                # EXPERIENCE
                # -----------------------------------

                experience_element = position.select_one(".fa-trophy")

                if experience_element:
                    experience_container = experience_element.parent.parent
                    experience = experience_container.get_text(strip=True)
                else:
                    experience = None

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
                # DESCRIPTION
                # -----------------------------------

                description_element = position.select_one(".collapse .fs-sm.fw-regular")

                description = (
                    description_element.get_text(strip=True)
                    if description_element
                    else None
                )

                # -----------------------------------
                # JOB ID
                # -----------------------------------

                job_id = None

                if link_element and link_element.get("href"):
                    href = link_element.get("href")

                    match = re.search(r"/jobs/(\d+)", href)

                    if match:
                        job_id = match.group(1)

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
                        "remote_type": remote_type,
                        "salary_min": salary_min,
                        "salary_max": salary_max,
                        "experience": experience,
                        "description": description,
                        "posted_at": posted_at,
                    }
                )

        return jobs
