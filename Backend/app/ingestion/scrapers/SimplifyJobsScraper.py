import json
import os
import httpx

import requests

from app.ingestion.config import (
    SIMPLIFYJOBS_API_URL,
    SIMPLIFYJOBS_QUERY,
    SIMPLIFYJOBS_PER_PAGE,
    SIMPLIFYJOBS_MAX_PAGES,
)


class SimplifyJobsScraper:
    SOURCE = "SimplifyJobs"
    API_URL = (
        "https://js-ha.simplify.jobs/multi_search"
        "?use_cache=true&cache_ttl=120"
    )

    def __init__(
        self,
        filter_by: str,
        query: str = SIMPLIFYJOBS_QUERY,
        per_page: int = SIMPLIFYJOBS_PER_PAGE,
        max_pages: int = SIMPLIFYJOBS_MAX_PAGES,
    ):
        self.api_key = os.getenv("SIMPLIFYJOBS_API_KEY")
        self.api_url = SIMPLIFYJOBS_API_URL
        self.filter_by = filter_by
        self.query = query
        self.per_page = per_page
        self.max_pages = max_pages

        if not self.api_key:
            raise RuntimeError(
                "SIMPLIFYJOBS_API_KEY environment variable is missing."
            )

    async def fetch_jobs_page(self) -> str:
        headers = {
            "x-typesense-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        all_hits = []
        page = 1
        total_found = None

        async with httpx.AsyncClient(timeout=30.0) as session:
            while (total_found is None or len(all_hits) < total_found) and len(all_hits) < 200:
                search = {
                    "collection": "jobs",
                    "q": "software engineer",
                    "query_by": "title,company_name,functions,locations",
                    "sort_by": "start_date:desc,posting_id:desc",
                    "page": page,
                    "per_page": self.per_page,
                    "filter_by": self.filter_by,
                }

                response = await session.post(
                    self.api_url,
                    headers=headers,
                    json={"searches": [search]},
                )
                if response.is_error:
                    print("SimplifyJobs API status:", response.status_code)
                    print("SimplifyJobs API response:", response.text)
                    response.raise_for_status()

                data = response.json()

                results = data.get("results", [])
                if not results:
                    break

                result = results[0]
                hits = result.get("hits", [])

                if total_found is None:
                    total_found = result.get("found", 0)

                if not hits:
                    break

                remaining = 200 - len(all_hits)
                all_hits.extend(hits[:remaining])
                page += 1

        return json.dumps({"results": [{
            "hits": all_hits,
            "found": total_found or 0,
        }]})