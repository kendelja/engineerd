"""
Which jobs are worth keeping, regardless of source.

Two checks, both applied in the pipeline before anything is stored:

1. Title: interns, co-ops, students and non-software engineering roles
   (mechanical, materials, photonics, hardware...) are never shown. These
   are matched by discipline, so a new posting in one of those fields is
   caught without adding its exact title anywhere.
2. Location: a job must be open to the market being ingested. A role
   whose location is only a country outside Canada / the US (e.g.
   "Brazil") is dropped for every market.

Location handling is deliberately conservative. Anything unrecognised
is kept, so a missing or unfamiliar city doesn't silently lose a job.
"""

import re
from typing import Optional


# ============================================================
# TITLE
# ============================================================

_EXCLUDED_TITLE_RE = re.compile(
    r"\b(?:intern|interns|internship|internships|"
    r"co-?op|co-?ops|coop|students?)\b",
    re.IGNORECASE,
)

# Engineering disciplines that are not software. Matched anywhere in the
# title, so "Engineer I, Mechanical (R6302)" and "Photonics Integration
# Engineer, MTS" are both caught.
_NON_SOFTWARE_DISCIPLINE_RE = re.compile(
    r"\b(?:mechanical|electrical|electronics?|civil|chemical|aerospace|"
    r"structural|industrial|manufacturing|materials?|photonics?|optics?|"
    r"optical|mechatronics?|hardware|semiconductor|fab|process|quality|"
    r"facilities|controls|thermal|propulsion|avionics|battery|rf|antenna|"
    r"laboratory|lab|toolmaker|tool\s*(?:&|and)\s*die|machinist)\b",
    re.IGNORECASE,
)

# A software term rescues a title that also names a discipline:
# "Robotics Software Engineer, Hardware Platform" is still software.
_SOFTWARE_TERM_RE = re.compile(
    r"\b(?:software|developer|programmer|full[- ]?stack|front[- ]?end|"
    r"back[- ]?end|devops|sre|data|machine learning|ai|ml|cloud|web|"
    r"mobile|test automation)\b",
    re.IGNORECASE,
)

# Non-software IT and language-QA roles, which are not discipline words.
_NON_SOFTWARE_ROLE_RE = re.compile(
    r"\b(?:systems? administrator|network administrator|"
    r"wireless networking tester|networking tester|"
    r"lqa analyst|linguistic quality assurance|language quality assurance|"
    r"quality assurance linguistique|testeur réseautique)\b",
    re.IGNORECASE,
)


def is_excluded_title(title: Optional[str]) -> bool:
    """True for interns, co-ops, students and non-software engineering roles."""

    if not title:
        return False

    if _EXCLUDED_TITLE_RE.search(title) or _NON_SOFTWARE_ROLE_RE.search(title):
        return True

    return bool(
        _NON_SOFTWARE_DISCIPLINE_RE.search(title)
        and not _SOFTWARE_TERM_RE.search(title)
    )


# ============================================================
# LOCATION
# ============================================================

# Regions a location can point at. "CA" and "US" are the two markets
# the app ingests. "GLOBAL" is remote-anywhere wording, which is open
# to both. "OTHER" is any other country or region.

_CA_TERMS = [
    r"canada", r"canadian", r"can", r"ontario", r"british columbia", r"alberta",
    r"quebec", r"québec", r"qu\W{1,2}bec", r"toronto", r"vancouver", r"montreal",
    r"montréal", r"ottawa", r"calgary", r"edmonton", r"waterloo", r"kitchener",
    r"richmond hill", r"mississauga", r"winnipeg", r"halifax", r"moncton",
    r"victoria", r"courtenay", r"hamilton", r"markham", r"burlington",
    r"london, on", r"london, ontario", r"london on",
    r"saskatoon", r"regina", r"oakville", r"guelph", r"burnaby",
    r"surrey", r"kelowna", r"st\.? john'?s", r"fredericton", r"charlottetown",
]

_US_TERMS = [
    r"united states", r"usa", r"u\.s\.", r"us",
    r"new york", r"san francisco", r"seattle", r"boston", r"chicago",
    r"los angeles", r"austin", r"denver", r"atlanta", r"dallas", r"houston",
    r"portland", r"washington", r"miami", r"redmond", r"palo alto",
    r"mountain view", r"sunnyvale", r"menlo park", r"san jose", r"san diego",
    r"brooklyn", r"philadelphia", r"phoenix", r"minneapolis", r"raleigh",
    r"charlotte", r"nashville", r"pittsburgh", r"boulder", r"salt lake city",
]

_GLOBAL_TERMS = [
    r"everywhere", r"anywhere", r"worldwide", r"global", r"remote",
    r"north america",
]

# Countries and regions we never ingest for. Keep this list to places
# that are clearly outside both markets.
_OTHER_TERMS = [
    r"brazil", r"brasil", r"india", r"germany", r"australia", r"united kingdom",
    r"uk", r"england", r"scotland", r"ireland", r"france", r"spain", r"italy",
    r"portugal", r"netherlands", r"belgium", r"sweden", r"norway", r"denmark",
    r"finland", r"poland", r"romania", r"ukraine", r"greece", r"austria",
    r"switzerland", r"czech", r"hungary", r"israel", r"turkey", r"türkiye",
    r"egypt", r"nigeria", r"kenya", r"south africa", r"mexico", r"argentina",
    r"colombia", r"chile", r"peru", r"singapore", r"japan", r"china",
    r"hong kong", r"taiwan", r"korea", r"philippines", r"vietnam", r"indonesia",
    r"malaysia", r"thailand", r"pakistan", r"bangladesh", r"new zealand",
    r"emea", r"apac", r"latam", r"europe", r"asia", r"dubai", r"uae", r"saudi",
    r"berlin", r"paris", r"amsterdam", r"dublin", r"madrid",
    r"barcelona", r"lisbon", r"warsaw", r"tel aviv", r"bangalore", r"bengaluru",
    r"hyderabad", r"pune", r"mumbai", r"delhi", r"gurgaon", r"noida",
    r"sao paulo", r"são paulo", r"rio de janeiro", r"singapore", r"sydney",
    r"melbourne", r"tokyo", r"seoul", r"shanghai", r"beijing", r"manila",
]


def _matches(text: str, terms: list[str]) -> bool:
    return any(
        re.search(rf"(?<![a-z]){term}(?![a-z])", text)
        for term in terms
    )


def location_regions(location: Optional[str]) -> set[str]:
    """Which of CA / US / GLOBAL / OTHER a location string mentions."""

    if not location:
        return set()

    text = location.lower()

    regions = set()

    if _matches(text, _CA_TERMS):
        regions.add("CA")

    if _matches(text, _US_TERMS):
        regions.add("US")

    if _matches(text, _GLOBAL_TERMS):
        regions.add("GLOBAL")

    if _matches(text, _OTHER_TERMS):
        regions.add("OTHER")

    return regions


# Which regions each ingestion market accepts.
MARKET_REGIONS = {
    "canada": {"CA"},
    "usa": {"US"},
    "north-america": {"CA", "US"},
}


def location_eligible(location: Optional[str], market: Optional[str]) -> bool:
    """
    True if the job is open to `market`.

    Rules, in order:
    - Mentions a place outside CA/US and no CA/US place: drop.
    - Mentions only CA (or only US) and the market is the other one: drop.
    - Anything else, including no location at all: keep.
    """

    if market is None:
        return True

    accepted = MARKET_REGIONS[market]
    regions = location_regions(location)

    places = regions & {"CA", "US"}

    if not places:
        # Global wording ("Everywhere") is open to both markets; so is
        # no information, and so is a location we don't recognise.
        return "OTHER" not in regions

    return bool(places & accepted)


def is_ineligible_location(location: Optional[str]) -> bool:
    """Ineligible for every market we ingest (used for cleanup)."""

    return not any(location_eligible(location, m) for m in MARKET_REGIONS)


# ============================================================
# MARKETS A JOB BELONGS TO (stored, and used to filter the list)
# ============================================================

ALL_MARKETS = ["canada", "usa", "north-america"]


def markets_for_location(location: Optional[str]) -> list[str]:
    """
    Every market a job is open to, for the Country filter.

    A Canada-only job belongs to Canada and North America. Remote-anywhere
    or unrecognised locations belong to all three, so nothing is hidden
    from a tab just because we couldn't place it.
    """

    if not location:
        return list(ALL_MARKETS)

    markets = [
        market
        for market in ("canada", "usa")
        if location_eligible(location, market)
    ]

    if not markets:
        return []

    if "canada" in markets or "usa" in markets:
        markets.append("north-america")

    return markets
