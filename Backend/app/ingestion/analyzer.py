"""
Job analysis: required experience, skills, and junior-fit scoring.

Everything here is a pure function (no I/O) so it can run at ingestion
time, in a backfill script, and in unit tests.

The core idea is "ghost-junior" detection: a posting that is *labelled*
junior/entry-level (by the board or by its title) but whose description
asks for 3+ years of experience.
"""

import math
import re
from dataclasses import dataclass, field
from typing import Optional


# ============================================================
# LABELS
# ============================================================

JUNIOR_FRIENDLY = "junior-friendly"
JUNIOR_UNCONFIRMED = "junior-unconfirmed"  # junior-tagged, but the posting or pay says otherwise
STRETCH = "stretch"
GHOST_JUNIOR = "ghost-junior"
SENIOR = "senior"
UNVERIFIED = "unverified"  # labelled junior, but no text to check against
UNCLEAR = "unclear"

FIT_LABELS = {
    JUNIOR_FRIENDLY,
    JUNIOR_UNCONFIRMED,
    STRETCH,
    GHOST_JUNIOR,
    SENIOR,
    UNVERIFIED,
    UNCLEAR,
}


@dataclass
class JobAnalysis:
    years_required: Optional[int] = None
    years_evidence: Optional[str] = None
    skills: list[str] = field(default_factory=list)
    fit_score: int = 50
    fit_label: str = UNCLEAR
    fit_reasons: list[str] = field(default_factory=list)
    fit_confidence: str = "low"  # low | medium | high


# ============================================================
# YEARS OF EXPERIENCE
# ============================================================

_NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "twelve": 12, "fifteen": 15,
}

_NUMBER = r"\d{1,2}(?:\.\d)?|" + "|".join(_NUMBER_WORDS)

# "5 years", "5+ years", "3-5 years", "3 to 5 yrs", "five or more years"
_YEARS_RE = re.compile(
    rf"(?<![\w$.,])(?P<lo>{_NUMBER})"
    rf"(?:\s*(?:-|–|—|to)\s*(?P<hi>{_NUMBER}))?"
    r"\s*(?P<plus>\+|plus|or\s+more|or\s+greater)?"
    r"\s*(?:years?|yrs?)\b",
    re.IGNORECASE,
)

# The match must look like an experience requirement, not
# "20 years in business" or "six years of R&D".
_CONTEXT_RE = re.compile(
    r"\b(experience|experienced|exp|background|proven|hands-on|"
    r"track record|expertise)\b",
    re.IGNORECASE,
)

# "5+ years building APIs", "3 years in software engineering"
_TAIL_VERB_RE = re.compile(
    r"^\W*(?:in|with|as|using|working|developing|building|"
    r"designing|leading|delivering|architecting|managing|"
    r"implementing|writing|creating|maintaining|operating|"
    r"shipping|deploying|testing|coding|programming|engineering)\b",
    re.IGNORECASE,
)

# "3 years of (relevant) experience" -- but not "6 years of R&D".
_TAIL_OF_RE = re.compile(
    r"^\W*(?:or\s+(?:more|greater)\s+)?of\b",
    re.IGNORECASE,
)

_TAIL_REJECT_RE = re.compile(
    r"^\W*(?:ago|old|of age|in business|of history|since|"
    r"of operation|of service|of growth|of excellence|"
    r"contract|term|anniversary|warranty|vesting)",
    re.IGNORECASE,
)

_HEAD_REJECT_RE = re.compile(
    r"\b(?:past|last|next|every|each|within|after|previous|"
    r"over the|less than|fewer than|founded|established|since)"
    r"\s+(?:\w+\s+){0,2}$",
    re.IGNORECASE,
)

_SOFT_RE = re.compile(
    r"\b(?:preferred|nice to have|nice-to-have|bonus|asset|ideally|"
    r"a plus|is a plus|desirable|desired|optional|would be)\b",
    re.IGNORECASE,
)

_CLAUSE_BREAK = ".;\n•"

# Anything above this is almost certainly company marketing copy
# ("with 25+ years of experience serving...").
_MAX_PLAUSIBLE_YEARS = 15


# "Minimum 2 years" is a hard floor even when a parenthetical follows it:
# "Minimum 2 years (ideally targeted around 2 to 4 years) of ..." needs 2.
_HARD_CUE_RE = re.compile(
    r"\b(?:minimum|at least|min\.?|must have|required)\s+(?:of\s+)?$",
    re.IGNORECASE,
)

_LEADING_ASIDE_RE = re.compile(r"^\s*\([^)]*\)")

# A parenthetical that only says the years are optional is still soft.
_SOFT_ASIDE_RE = re.compile(
    r"^\s*\(\s*(?:preferred|nice to have|a plus|bonus|optional|desired)\s*\)",
    re.IGNORECASE,
)


def _to_int(token: Optional[str]) -> Optional[int]:
    if token is None:
        return None

    token = token.lower()

    if token in _NUMBER_WORDS:
        return _NUMBER_WORDS[token]

    # "1.5+ years" is stored as 2: the requirement is "at least 1.5".
    return math.ceil(float(token))


def _clause_before(text: str, start: int, width: int = 60) -> str:
    chunk = text[max(0, start - width):start]
    cut = max(chunk.rfind(c) for c in _CLAUSE_BREAK)

    return chunk[cut + 1:] if cut != -1 else chunk


def _clause_after(text: str, end: int, width: int = 60) -> str:
    chunk = text[end:end + width]
    cuts = [chunk.find(c) for c in _CLAUSE_BREAK if c in chunk]

    return chunk[:min(cuts)] if cuts else chunk


def extract_years_required(
    text: Optional[str],
) -> tuple[Optional[int], Optional[str]]:
    """
    Return (minimum years required, evidence snippet).

    Of all hard requirements found, the highest lower bound wins:
    "2+ years Python, 5+ years leading teams" is a 5-year role.
    Ranges use their lower bound ("3-5 years" -> 3). Statements that
    are marked preferred / a bonus are ignored.
    """

    if not text:
        return None, None

    best: Optional[int] = None
    evidence: Optional[str] = None

    for match in _YEARS_RE.finditer(text):
        low = _to_int(match.group("lo"))

        if low is None or low > _MAX_PLAUSIBLE_YEARS:
            continue

        before = _clause_before(text, match.start())
        # "of ... experience" can have a long qualifier in between
        # ("10 years or more of distributed and cloud-native software
        # engineering experience"), so look further for that.
        after_long = _clause_after(text, match.end(), 130)

        if _HARD_CUE_RE.search(before):
            if _SOFT_ASIDE_RE.match(after_long):
                continue
            aside = _LEADING_ASIDE_RE.match(after_long)
            if aside:
                after_long = after_long[aside.end():]

        after = after_long[:60]

        if _HEAD_REJECT_RE.search(before):
            continue

        if _TAIL_REJECT_RE.match(after):
            continue

        clause = before + match.group(0) + after

        looks_like_requirement = (
            _TAIL_VERB_RE.match(after)
            or (
                _TAIL_OF_RE.match(after_long)
                and _CONTEXT_RE.search(after_long)
            )
            or _CONTEXT_RE.search(clause)
        )

        if not looks_like_requirement:
            continue

        if _SOFT_RE.search(before) or _SOFT_RE.search(after):
            continue

        if best is None or low > best:
            best = low
            snippet = text[match.start():match.end() + 45].strip()
            # Split on sentence breaks, but not the dot in "1.5".
            evidence = re.split(r"[;\n]|\.(?!\d)", snippet)[0].strip()

    return best, evidence


# ============================================================
# SENIORITY SIGNALS
# ============================================================

_SENIOR_TITLE_RE = re.compile(
    r"\b(?:senior|sr\.?|staff|principal|lead|director|head of|vp|"
    r"vice president|manager|architect|distinguished|chief)\b"
    r"|\b(?:engineer|developer|swe|analyst)\s+(?:iii|iv|v|3|4|5)\b"
    r"|\blevel\s*(?:[3-9]|\d{2,})\b",
    re.IGNORECASE,
)

_MID_TITLE_RE = re.compile(
    r"\b(?:intermediate|mid[- ]?level)\b"
    r"|\b(?:engineer|developer|swe|analyst)\s+(?:ii|2)\b"
    r"|\blevel\s*2\b",
    re.IGNORECASE,
)

_JUNIOR_TITLE_RE = re.compile(
    r"\b(?:junior|jr\.?|entry[- ]level|new grad(?:uate)?|graduate|"
    r"associate|intern(?:ship)?|co-?op|apprentice|trainee|"
    r"early career)\b"
    r"|\b(?:engineer|developer|swe|analyst)\s+(?:i|1)\b"
    r"|\blevel\s*(?:1|i)\b",
    re.IGNORECASE,
)


def _declared_levels(experience_level: Optional[str]) -> set[str]:
    """Map a source's experience tags onto {junior, mid, senior}."""

    levels: set[str] = set()

    for tag in (experience_level or "").lower().split(","):
        tag = tag.strip()

        if not tag:
            continue

        if "entry" in tag or "junior" in tag or "new grad" in tag:
            levels.add("junior")
        elif "mid" in tag or "intermediate" in tag:
            levels.add("mid")
        elif "senior" in tag or "expert" in tag or "lead" in tag:
            levels.add("senior")

    return levels


# ============================================================
# SKILLS
# ============================================================

def _word(*names: str) -> str:
    """Whole-token match that won't fire inside C++, node.js, etc."""
    body = "|".join(re.escape(name) for name in names)

    return r"(?<![\w+#.])(?:" + body + r")(?![\w+#])"


_SKILLS: list[tuple[str, re.Pattern]] = [
    (name, re.compile(pattern, flags))
    for name, pattern, flags in [
        ("Python", _word("Python"), re.I),
        ("Java", _word("Java"), re.I),
        ("JavaScript", _word("JavaScript", "Javascript", "ECMAScript"), re.I),
        ("TypeScript", _word("TypeScript"), re.I),
        ("C++", r"(?<![\w])C\+\+(?![\w+])", 0),
        ("C#", r"(?<![\w])C#(?![\w])", 0),
        (
            "Go",
            r"(?i:\bgolang\b)|(?:(?<=, )|(?<=,)|(?<=/ )|(?<=/)|(?<=\())Go\b"
            r"|\bGo(?=\s*[,/)])|\bGo\s+(?:developer|engineer|programming)\b",
            0,
        ),
        ("Rust", _word("Rust"), 0),
        ("Ruby", _word("Ruby"), re.I),
        ("PHP", _word("PHP"), re.I),
        ("Kotlin", _word("Kotlin"), re.I),
        ("Swift", _word("Swift"), 0),
        ("Scala", _word("Scala"), re.I),
        ("SQL", _word("SQL"), re.I),
        # Case-sensitive: "react to incidents" is not a skill.
        ("React", _word("React", "React.js", "ReactJS"), 0),
        ("Angular", _word("Angular", "AngularJS"), re.I),
        ("Vue", _word("Vue", "Vue.js", "VueJS"), re.I),
        ("Next.js", _word("Next.js", "NextJS"), re.I),
        ("Node.js", _word("Node.js", "NodeJS"), re.I),
        ("HTML", _word("HTML", "HTML5"), re.I),
        ("CSS", _word("CSS", "CSS3"), re.I),
        ("Tailwind", _word("Tailwind"), re.I),
        ("GraphQL", _word("GraphQL"), re.I),
        ("REST", _word("REST", "RESTful"), 0),
        ("Django", _word("Django"), re.I),
        ("Flask", _word("Flask"), re.I),
        ("FastAPI", _word("FastAPI"), re.I),
        # "Spring 2026 co-op" is a season, not a framework.
        (
            "Spring",
            _word("Spring Boot", "Spring Framework", "Spring MVC",
                  "Spring Cloud"),
            re.I,
        ),
        (".NET", r"(?<![\w])(?:ASP)?\.NET\b|\bdotnet\b", re.I),
        ("Rails", r"\bRuby on Rails\b|\bRails\b", 0),
        ("PostgreSQL", _word("PostgreSQL", "Postgres"), re.I),
        ("MySQL", _word("MySQL"), re.I),
        ("MongoDB", _word("MongoDB", "Mongo"), re.I),
        ("Redis", _word("Redis"), re.I),
        ("Kafka", _word("Kafka"), re.I),
        ("Spark", _word("Spark", "PySpark"), 0),
        ("Airflow", _word("Airflow"), re.I),
        ("Snowflake", _word("Snowflake"), re.I),
        ("Pandas", _word("Pandas"), 0),
        ("Elasticsearch", _word("Elasticsearch", "OpenSearch"), re.I),
        ("AWS", _word("AWS", "Amazon Web Services"), re.I),
        ("Azure", _word("Azure"), re.I),
        ("GCP", _word("GCP", "Google Cloud"), re.I),
        ("Docker", _word("Docker"), re.I),
        ("Kubernetes", _word("Kubernetes", "k8s"), re.I),
        ("Terraform", _word("Terraform"), re.I),
        ("CI/CD", r"(?<![\w])CI\s*/\s*CD(?![\w])|\bCICD\b", re.I),
        ("Jenkins", _word("Jenkins"), re.I),
        ("Linux", _word("Linux"), re.I),
        ("Git", _word("Git", "GitHub", "GitLab"), re.I),
        ("Machine Learning", r"(?i:\bmachine learning\b)|\bML\b", 0),
        ("PyTorch", _word("PyTorch"), re.I),
        ("TensorFlow", _word("TensorFlow"), re.I),
        ("LLMs", r"\bLLMs?\b|\blarge language models?\b", re.I),
        ("iOS", _word("iOS"), 0),
        ("Android", _word("Android"), re.I),
        ("React Native", _word("React Native"), re.I),
        ("Flutter", _word("Flutter"), re.I),
        ("Selenium", _word("Selenium"), re.I),
        ("Cypress", _word("Cypress"), re.I),
    ]
]


def extract_skills(*texts: Optional[str], limit: int = 12) -> list[str]:
    """Known technologies mentioned, in order of first appearance."""

    text = " ".join(t for t in texts if t)

    if not text:
        return []

    found: list[tuple[int, str]] = []

    for name, pattern in _SKILLS:
        match = pattern.search(text)

        if match:
            found.append((match.start(), name))

    found.sort()

    return [name for _, name in found[:limit]]


# ============================================================
# JUNIOR-FIT
# ============================================================

# A junior-tagged role whose pay starts at or above this is treated as
# senior-range pay, or whose pay range tops out at SENIOR_PAY_TOP or more.
# Applies only when the posting states no years.
SENIOR_PAY_FLOOR = 120_000
SENIOR_PAY_TOP = 200_000

# Titles that say the role is entry-level. High pay on these is normal
# for new grad and associate roles, so the pay rule does not apply.
_ENTRY_TITLE_RE = re.compile(
    r"\b(?:new grad|new graduate|associate|junior|jr|entry|early career|intern)\b",
    re.IGNORECASE,
)


def analyze_job(
    title: Optional[str],
    description: Optional[str],
    experience_level: Optional[str] = None,
    years_required: Optional[int] = None,
    salary_min: Optional[float] = None,
    salary_max: Optional[float] = None,
) -> JobAnalysis:
    """
    years_required -- a structured value from the source (e.g. a
                      "5 years of exp" field). Preferred over mining
                      the text, which is only a fallback.
    """

    title = title or ""
    description = description or ""
    has_text = len(description) >= 80

    years, evidence = extract_years_required(f"{title}. {description}")
    skills = extract_skills(title, description)

    if years_required is not None:
        years = years_required
        evidence = f"{years_required} years of experience (listed)"

    declared = _declared_levels(experience_level)

    title_senior = bool(_SENIOR_TITLE_RE.search(title))
    title_mid = bool(_MID_TITLE_RE.search(title))
    title_junior = bool(_JUNIOR_TITLE_RE.search(title))

    labelled_senior = title_senior or (
        "senior" in declared and "junior" not in declared
    )
    labelled_junior = not labelled_senior and (
        title_junior or "junior" in declared
    )
    labelled_mid = (
        not labelled_senior
        and not labelled_junior
        and (title_mid or "mid" in declared)
    )

    reasons: list[str] = []

    # ---- label ------------------------------------------------
    if labelled_senior:
        label = SENIOR
        reasons.append(
            "Senior-level title" if title_senior
            else "Listed as senior-level"
        )

        if years is not None:
            reasons.append(f"Asks for {years} years")

    elif labelled_junior:
        reasons.append(
            "Junior/entry-level title" if title_junior
            else "Listed as junior/entry-level"
        )

        if years is not None and years >= 3:
            label = GHOST_JUNIOR
            reasons.append(
                f"Labelled junior but asks for {years} years"
            )
        elif years is not None:
            label = JUNIOR_FRIENDLY
            reasons.append(
                f"Asks for {years} years"
                if years else "No experience required"
            )
        elif (
            (
                (salary_min is not None and salary_min >= SENIOR_PAY_FLOOR)
                or (salary_max is not None and salary_max >= SENIOR_PAY_TOP)
            )
            and not _ENTRY_TITLE_RE.search(title)
        ):
            label = JUNIOR_UNCONFIRMED
            reasons.append(
                "Labelled junior, but the pay is in the senior range "
                "and no years are listed"
            )
        elif has_text:
            label = JUNIOR_FRIENDLY
            reasons.append("No years requirement found in description")
        else:
            label = UNVERIFIED
            reasons.append(
                "No description available to verify the requirements"
            )

    else:
        if labelled_mid:
            reasons.append("Mid-level role")

        if years is None:
            label = STRETCH if labelled_mid else UNCLEAR
        elif years >= 5:
            label = SENIOR
            reasons.append(f"Asks for {years} years")
        elif years >= 3:
            label = STRETCH
            reasons.append(f"Asks for {years} years")
        else:
            label = STRETCH if labelled_mid else JUNIOR_FRIENDLY
            reasons.append(
                f"Asks for {years} years"
                if years else "No experience required"
            )

    # ---- score ------------------------------------------------
    if labelled_senior:
        base = 15
    elif labelled_junior:
        base = 65
    elif labelled_mid:
        base = 40
    else:
        base = 45

    if years is None:
        adjust = 0
    else:
        adjust = {0: 25, 1: 20, 2: 8, 3: -15, 4: -25}.get(years, -40)

    score = base + adjust

    # ---- confidence -------------------------------------------
    if years is not None:
        confidence = "high"
    elif has_text:
        confidence = "medium"
    else:
        confidence = "low"

        # With nothing to verify against, pull toward neutral.
        score = round((score + 50) / 2)

    if label == SENIOR:
        score = min(score, 20)

    return JobAnalysis(
        years_required=years,
        years_evidence=evidence,
        skills=skills,
        fit_score=max(0, min(100, score)),
        fit_label=label,
        fit_reasons=reasons,
        fit_confidence=confidence,
    )
