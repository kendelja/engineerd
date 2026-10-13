from dataclasses import dataclass, field
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

    # "Remote" | "Hybrid" | "On-site" | None (unknown)
    work_model: Optional[str] = None

    # Set when the detail page was read (see app.ingestion.detail).
    detail_checked_at: Optional[datetime] = None

    # Populated by app.ingestion.analyzer during normalization.
    years_required: Optional[int] = None
    years_evidence: Optional[str] = None
    skills: list[str] = field(default_factory=list)
    fit_score: Optional[int] = None
    fit_label: Optional[str] = None
    fit_reasons: list[str] = field(default_factory=list)
    fit_confidence: Optional[str] = None