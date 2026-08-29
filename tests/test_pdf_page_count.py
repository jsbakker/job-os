"""Tests for scripts/pdf_page_count.py.

Uses fake_mdls_tools (see conftest.py) to deterministically control what
`mdimport`/`mdls`/`pdfinfo` "return," since the real tools' Spotlight-index
timing is exactly the kind of flakiness this script exists to paper over.
Every invocation passes --retry-delay 0 so the suite doesn't burn real
wall-clock time on the script's internal time.sleep calls.
"""
import json

import pytest


@pytest.fixture
def pdf_path(tmp_path):
    path = tmp_path / "resume.pdf"
    path.touch()
    return path


# ---- pdfinfo branch (used whenever pdfinfo is on PATH) ------------------

def test_pdfinfo_present_one_shot_no_retry(fake_mdls_tools, pdf_path, run_script):
    fake_mdls_tools(mdls_responses=[], pdfinfo_output="Pages:          3")
    result = run_script("pdf_page_count.py", str(pdf_path), "--retry-delay", "0")
    assert result.returncode == 0
    assert result.stdout.strip() == "3"


def test_pdfinfo_json_output(fake_mdls_tools, pdf_path, run_script):
    fake_mdls_tools(mdls_responses=[], pdfinfo_output="Pages:          5")
    result = run_script("pdf_page_count.py", str(pdf_path), "--retry-delay", "0", "--json")
    assert result.returncode == 0
    assert json.loads(result.stdout) == {"pages": 5, "method": "pdfinfo"}


def test_pdfinfo_nonzero_exit_reported_as_failure(fake_mdls_tools, pdf_path, run_script):
    fake_mdls_tools(mdls_responses=[], pdfinfo_output="some error", pdfinfo_exit=1)
    result = run_script("pdf_page_count.py", str(pdf_path), "--retry-delay", "0")
    assert result.returncode == 1
    assert result.stderr.strip() != ""


# ---- mdls branch (used when pdfinfo is not on PATH) ---------------------

def test_mdls_succeeds_when_two_consecutive_reads_agree(fake_mdls_tools, pdf_path, run_script):
    fake_mdls_tools(mdls_responses=[
        "kMDItemNumberOfPages = 2",
        "kMDItemNumberOfPages = 2",
    ])
    result = run_script("pdf_page_count.py", str(pdf_path), "--retry-delay", "0")
    assert result.returncode == 0
    assert result.stdout.strip() == "2"


def test_mdls_json_output_reports_method(fake_mdls_tools, pdf_path, run_script):
    fake_mdls_tools(mdls_responses=[
        "kMDItemNumberOfPages = 2",
        "kMDItemNumberOfPages = 2",
    ])
    result = run_script("pdf_page_count.py", str(pdf_path), "--retry-delay", "0", "--json")
    assert json.loads(result.stdout) == {"pages": 2, "method": "mdls"}


def test_mdls_null_then_succeed(fake_mdls_tools, pdf_path, run_script):
    # The original documented failure mode: mdls returns (null) once before
    # Spotlight's index catches up, then a real value.
    fake_mdls_tools(mdls_responses=[
        "kMDItemNumberOfPages = (null)",
        "kMDItemNumberOfPages = 3",
        "kMDItemNumberOfPages = 3",
    ])
    result = run_script("pdf_page_count.py", str(pdf_path), "--retry-delay", "0")
    assert result.returncode == 0
    assert result.stdout.strip() == "3"


def test_mdls_stale_then_correct_regression(fake_mdls_tools, pdf_path, run_script):
    # The real bug found and fixed this session: a fast-following mdls call
    # after regenerating a PDF at the same path can return a stale but VALID
    # page count from the previous version of the file, not (null). A bare
    # "retry on null" loop never catches this because a stale number still
    # matches. This asserts the fix returns the stable, repeated value (3),
    # not the first stale one (5).
    fake_mdls_tools(mdls_responses=[
        "kMDItemNumberOfPages = 5",
        "kMDItemNumberOfPages = 3",
        "kMDItemNumberOfPages = 3",
    ])
    result = run_script("pdf_page_count.py", str(pdf_path), "--retry-delay", "0")
    assert result.returncode == 0
    assert result.stdout.strip() == "3"


def test_mdls_always_null_exhausts_retries(fake_mdls_tools, pdf_path, run_script):
    fake_mdls_tools(mdls_responses=["kMDItemNumberOfPages = (null)"])
    result = run_script("pdf_page_count.py", str(pdf_path), "--retries", "2", "--retry-delay", "0")
    assert result.returncode == 1
    assert "no page count" in result.stderr


def test_retries_zero_means_a_single_attempt(fake_mdls_tools, pdf_path, run_script, tmp_path):
    fake_mdls_tools(mdls_responses=["kMDItemNumberOfPages = (null)"])
    result = run_script("pdf_page_count.py", str(pdf_path), "--retries", "0", "--retry-delay", "0")
    assert result.returncode == 1
    # Exactly one mdls invocation should have happened (the fake mdls
    # fixture's state-counter file, see conftest.py's fake_mdls_tools).
    assert (tmp_path / "mdls_state.txt").read_text().strip() == "1"


@pytest.mark.xfail(
    strict=True,
    reason="Known limitation: two consecutive identical STALE reads before the real "
           "value ever appears still satisfies the two-consecutive-match heuristic, "
           "so the script commits to the stale value early. Not fixed -- tracked here "
           "so it stays a known, monitored blind spot rather than a silent one.",
)
def test_repeating_stale_value_twice_still_fools_current_heuristic(fake_mdls_tools, pdf_path, run_json):
    fake_mdls_tools(mdls_responses=[
        "kMDItemNumberOfPages = 5",
        "kMDItemNumberOfPages = 5",
        "kMDItemNumberOfPages = 3",
        "kMDItemNumberOfPages = 3",
    ])
    _, data = run_json("pdf_page_count.py", str(pdf_path), "--retry-delay", "0", "--json")
    # The eventually-correct value; today the script actually returns 5.
    assert data["pages"] == 3
