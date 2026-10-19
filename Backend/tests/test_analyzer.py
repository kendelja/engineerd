import re

import pytest

from app.ingestion.analyzer import (
    GHOST_JUNIOR,
    JUNIOR_FRIENDLY,
    SENIOR,
    STRETCH,
    UNCLEAR,
    UNVERIFIED,
    analyze_job,
    extract_skills,
    extract_years_required,
)


# ------------------------------------------------------------
# Years of experience
# ------------------------------------------------------------

@pytest.mark.parametrize(
    "text, expected",
    [
        ("Requires 5+ years of experience in backend", 5),
        ("5+ years building production backend and frontend systems", 5),
        ("three years of software development experience", 3),
        ("8 or more years leading the full software development life cycle", 8),
        (
            "10 years or more of distributed and cloud-native software "
            "engineering experience in large systems",
            10,
        ),
        ("3+ years of relevant experience, or equivalent practical experience", 3),
        ("8-15 years of professional experience in software development", 8),
        ("3-5 years of professional experience", 3),
        ("3 to 5 years experience with Python", 3),
        ("At least 2 years of software development experience", 2),
        ("Minimum of three years of experience", 3),
        ("5 or more years of experience building APIs", 5),
        ("1+ yrs experience", 1),
        ("0-1 years of experience", 0),
        # Real Built In posting wording.
        ("You have a total of 1.5+ years of experience as a software engineer.", 2),
        # Highest hard requirement wins.
        ("2+ years of Python experience and 6+ years of experience leading teams", 6),
    ],
)
def test_years_detected(text, expected):
    years, evidence = extract_years_required(text)

    assert years == expected
    assert evidence
    assert re.search(r"years?|yrs?", evidence, re.IGNORECASE)


@pytest.mark.parametrize(
    "text",
    [
        "We have been in business for 20 years",
        "Over the past 5 years we have grown 10x",
        "A 2 year contract role",
        "Founded 12 years ago in Toronto",
        "Join a company with 30+ years of experience serving clients",
        "We have six years of R&D, over 2,000 product iterations, and backing.",
        "Our founders bring 15 years of industry leadership to the team",
        "The company has 12 years serving customers across Canada",
        "Strong communication skills",
        "5 years of experience with Kubernetes is a plus",
        "Nice to have: 4+ years of experience in Go",
        "",
        None,
    ],
)
def test_years_not_detected(text):
    years, _ = extract_years_required(text)

    assert years is None


# ------------------------------------------------------------
# Skills
# ------------------------------------------------------------

def test_skills_found_in_order():
    skills = extract_skills(
        "Build services in Python and TypeScript on AWS using Docker, "
        "PostgreSQL and React."
    )

    assert skills == [
        "Python", "TypeScript", "AWS", "Docker", "PostgreSQL", "React",
    ]


def test_java_is_not_javascript():
    assert extract_skills("We use JavaScript heavily") == ["JavaScript"]
    assert extract_skills("Java and Kotlin") == ["Java", "Kotlin"]


def test_symbol_languages():
    assert extract_skills("Strong C++ and C# skills") == ["C++", "C#"]


def test_no_false_positives_for_common_words():
    text = "Be ready to react quickly. Spring 2026 co-op. Go to market with us."

    assert extract_skills(text) == []


def test_go_in_a_tech_list():
    assert "Go" in extract_skills("Python, Go, and Rust experience")
    assert "Go" in extract_skills("Experience with Golang")


# ------------------------------------------------------------
# Junior-fit labels
# ------------------------------------------------------------

LONG_FILLER = (
    " You will design, build and ship features alongside a "
    "friendly team of engineers in a collaborative environment."
)


def test_ghost_junior():
    result = analyze_job(
        "Junior Software Developer",
        "Requires 4+ years of professional experience." + LONG_FILLER,
        "Junior",
    )

    assert result.fit_label == GHOST_JUNIOR
    assert result.years_required == 4
    assert result.fit_confidence == "high"
    assert result.fit_score < 50


def test_realistic_junior():
    result = analyze_job(
        "Software Developer I",
        "0-2 years of experience. Python and SQL." + LONG_FILLER,
        "Entry Level/New Grad",
    )

    assert result.fit_label == JUNIOR_FRIENDLY
    assert result.years_required == 0
    assert result.fit_score >= 80
    assert "Python" in result.skills


def test_junior_without_description_is_unverified():
    result = analyze_job(
        "Associate Software Developer",
        None,
        "Entry Level/New Grad, Junior",
    )

    assert result.fit_label == UNVERIFIED
    assert result.fit_confidence == "low"
    # Pulled toward neutral rather than rewarded.
    assert 40 <= result.fit_score <= 65


def test_junior_with_description_but_no_years_is_medium_confidence():
    result = analyze_job(
        "Junior Developer",
        "Help the team build internal tools and learn from mentors." + LONG_FILLER,
        "Junior",
    )

    assert result.fit_label == JUNIOR_FRIENDLY
    assert result.fit_confidence == "medium"


@pytest.mark.parametrize(
    "title, level",
    [
        ("Senior Software Engineer", "Senior"),
        ("Staff Engineer", None),
        ("Engineering Manager", "Mid Level"),
        ("Software Engineer", "Senior, Expert or higher"),
        ("Software Developer III", None),
    ],
)
def test_senior(title, level):
    result = analyze_job(title, None, level)

    assert result.fit_label == SENIOR
    assert result.fit_score <= 20


def test_unlabelled_role_with_heavy_requirements_is_senior():
    result = analyze_job(
        "Software Engineer",
        "You bring 7+ years of experience shipping production systems." + LONG_FILLER,
        None,
    )

    assert result.fit_label == SENIOR


def test_mid_level_is_a_stretch():
    result = analyze_job("Software Engineer II", None, "Mid Level")

    assert result.fit_label == STRETCH


def test_unlabelled_without_signals_is_unclear():
    result = analyze_job("Software Engineer", None, None)

    assert result.fit_label == UNCLEAR


def test_junior_and_mid_tags_with_low_years_stay_junior_friendly():
    result = analyze_job(
        "Software Developer",
        "1-2 years of experience required." + LONG_FILLER,
        "Junior, Mid Level",
    )

    assert result.fit_label == JUNIOR_FRIENDLY


def test_more_years_never_raises_the_score():
    scores = [
        analyze_job(
            "Junior Developer",
            f"Requires {years}+ years of experience." + LONG_FILLER,
            "Junior",
        ).fit_score
        for years in range(0, 8)
    ]

    assert scores == sorted(scores, reverse=True)


def test_minimum_years_with_parenthetical_aside_is_a_hard_floor():
    text = (
        "Experience and skills: Minimum 2 years (ideally targeted around "
        "2 to around 4 years) of full-stack development experience."
    )
    years, _ = extract_years_required(text)
    assert years == 2


def test_minimum_years_marked_preferred_stays_ignored():
    years, _ = extract_years_required("Minimum 2 years (preferred) of experience")
    assert years is None
