from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Job:
    source: str
    source_job_id: Optional[str]

    title: str
    company: str
    company_logo: Optional[str]
    location: Optional[str]

    description: Optional[str]
    url: str

    posted_at: Optional[datetime]

    experience_level: Optional[str]
    employment_type: Optional[str]
    remote_type: Optional[bool]

    salary_min: Optional[float]
    salary_max: Optional[float]
    salary_period: Optional[str]