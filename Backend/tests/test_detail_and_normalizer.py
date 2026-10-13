import pytest

from app.ingestion.detail import extract_builtin_text, extract_simplify_text
from app.ingestion.normalizer import normalize_job, parse_work_model


BUILTIN_HTML = """
<html><body>
  <nav>Browse 50,000 jobs. Our partners have 20 years of experience.</nav>
  <div class="container">
    <div class="col-12 col-lg-6 mb-sm">
      <div class="bg-white">
        <div id="job-post-body-123"><p><strong>What We Look For</strong></p>
          <p>You have a total of 1.5+ years of experience as a software engineer.</p></div>
      </div>
      <div class="bg-white"><h2>Skills Required</h2>
        <ul><li>Proficiency in Python or Kotlin</li><li>AWS and Kubernetes</li></ul>
      </div>
    </div>
    <div class="col-12 col-lg-6"><h2>About the company</h2>
      <p>Founded with 40 years of combined experience.</p></div>
  </div>
</body></html>
"""

SIMPLIFY_HTML = """
<html><body><main>
  <h1>Full-Stack Developer</h1>
  <h2>About the job</h2>
  <div><h3>Requirements</h3>
    <ul><li>At least 3 years of professional software development experience</li>
        <li>React and TypeScript</li></ul></div>
  <h2>About the company</h2>
  <p>Our team brings almost 60 years of combined experience.</p>
  <script>var x = "10 years";</script>
</main></body></html>
"""


def test_builtin_text_is_scoped_to_the_posting_column():
    text = extract_builtin_text(BUILTIN_HTML)

    assert "1.5+ years" in text
    assert "Proficiency in Python or Kotlin" in text
    assert "20 years" not in text
    assert "40 years" not in text


def test_builtin_missing_body_returns_none():
    assert extract_builtin_text("<html><body>nope</body></html>") is None


def test_simplify_text_stops_at_about_the_company():
    text = extract_simplify_text(SIMPLIFY_HTML)

    assert "At least 3 years" in text
    assert "React and TypeScript" in text
    assert "60 years" not in text
    assert "10 years" not in text  # script content


def test_simplify_missing_heading_returns_none():
    assert extract_simplify_text("<html><body><h2>Other</h2></body></html>") is None


@pytest.mark.parametrize(
    "raw, expected",
    [
        ({"remote": "Remote"}, "Remote"),
        ({"remote": "Hybrid"}, "Hybrid"),
        ({"remote": "In Person"}, "On-site"),
        ({"remote": "In-Office"}, "On-site"),
        ({"remote": "Hybrid or Remote"}, "Hybrid"),
        ({"remote": None}, None),
        ({"remote": "Flexible"}, None),
        ({"remote_type": True}, "Remote"),
        ({"remote_type": False}, None),
        ({}, None),
    ],
)
def test_work_model(raw, expected):
    assert parse_work_model(raw) == expected


def test_normalizer_sets_remote_flag_from_work_model():
    job = normalize_job(
        {
            "source": "BuiltIn",
            "source_job_id": "1",
            "title": "Junior Developer",
            "company": "Acme",
            "url": "https://example.com/1",
            "remote": "Remote",
        }
    )

    assert job.work_model == "Remote"
    assert job.remote_type is True
