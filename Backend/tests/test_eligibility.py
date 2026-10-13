import pytest

from app.ingestion.eligibility import (
    is_excluded_title,
    is_ineligible_location,
    location_eligible,
)


@pytest.mark.parametrize(
    "title",
    [
        "Software Engineer Intern",
        "Firmware Engineer Intern",
        "AI Product Engineer Intern - Match Group Core",
        "Test and Automated Test Co-op",
        "Software Developer Co-op (Winter 2027)",
        "Software Engineering Internship",
        "Coop Developer",
    ],
)
def test_interns_and_coops_excluded(title):
    assert is_excluded_title(title)


@pytest.mark.parametrize(
    "title",
    [
        "Software Engineer",
        "International Software Engineer",  # "intern" inside a word
        "Cooperative Platform Engineer",  # "co-op" inside a word
        "Senior Backend Engineer",
        None,
    ],
)
def test_real_titles_kept(title):
    assert not is_excluded_title(title)


@pytest.mark.parametrize(
    "location, market, expected",
    [
        # The Infisical case: Brazil-only remote is never for us.
        ("Brazil", "canada", False),
        ("Brazil", "usa", False),
        ("Brazil", "north-america", False),
        ("India", "canada", False),
        ("Germany", "usa", False),
        # Canadian places on the Canada market.
        ("Toronto", "canada", True),
        ("Vancouver", "canada", True),
        ("Canada", "canada", True),
        ("Toronto, ON, CAN", "canada", True),
        ("Remote only • Canada", "canada", True),
        ("Montreal, Qu�bec", "canada", True),
        ("Richmond Hill", "canada", True),
        # Canadian places are not for the US market.
        ("Toronto", "usa", False),
        ("Canada", "usa", False),
        # US places on the US market.
        ("Denver", "usa", True),
        ("United States", "usa", True),
        ("Remote in USA, Remote in Canada", "usa", True),
        ("Denver", "canada", False),
        ("Austin", "canada", False),
        # Global wording is open to both.
        ("Everywhere", "canada", True),
        ("Everywhere", "usa", True),
        ("North America", "canada", True),
        ("North America", "usa", True),
        ("Remote", "canada", True),
        # Anything unrecognised is kept rather than lost.
        ("Some Unknown Town", "canada", True),
        (None, "canada", True),
        ("", "usa", True),
        # London, Ontario is Canada, not the UK.
        ("London, ON", "canada", True),
    ],
)
def test_location_eligibility(location, market, expected):
    assert location_eligible(location, market) is expected


def test_no_market_keeps_everything():
    assert location_eligible("Brazil", None) is True


def test_ineligible_everywhere_is_cleanup_candidate():
    assert is_ineligible_location("Brazil")
    assert not is_ineligible_location("Denver")
    assert not is_ineligible_location("Toronto")
    assert not is_ineligible_location("Everywhere")
