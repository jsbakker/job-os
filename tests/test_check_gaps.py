"""Tests for scripts/check_gaps.py.

Pure sort/diff math on top of LLM-extracted date ranges. Returns raw gap
data only -- it does not decide what counts as a FAIL vs. a warning, since
/tailor-resume and /ats-validate apply two different policies on top of the
same underlying gaps.
"""
import json


def test_empty_roles_list(roles_json_file, run_json):
    path = roles_json_file([])
    _, data = run_json("check_gaps.py", "--input", str(path))
    assert data == {"gaps": [], "chronological_order": []}


def test_single_role_has_no_gaps(roles_json_file, run_json):
    path = roles_json_file([{"role": "Solo Role", "start": "2020-01", "end": "2022-01"}])
    _, data = run_json("check_gaps.py", "--input", str(path))
    assert data == {"gaps": [], "chronological_order": ["Solo Role"]}


def test_overlapping_ongoing_role_produces_no_bogus_gap(roles_json_file, run_json):
    # An "Ongoing" independent-work role that started long before, and ends
    # "present", sorts first by start date -- but its (today) end date is
    # far after later roles' start dates, so the naive adjacent-pair gap
    # would be deeply negative and must be filtered out entirely.
    path = roles_json_file([
        {"role": "Independent Developer", "start": "2000-01", "end": "present"},
        {"role": "Mid Role", "start": "2005-01", "end": "2010-01"},
        {"role": "Recent Role", "start": "2010-02", "end": "2015-01"},
    ])
    _, data = run_json("check_gaps.py", "--input", str(path))
    assert data["chronological_order"] == ["Independent Developer", "Mid Role", "Recent Role"]
    assert data["gaps"] == [
        {
            "gap_months": 1,
            "before_role": "Mid Role", "before_end": "2010-01",
            "after_role": "Recent Role", "after_start": "2010-02",
        }
    ]


def test_zero_month_gap_is_absent_from_gaps_list(roles_json_file, run_json):
    # gap_months > 0 filters this out entirely -- adjacent same-month roles
    # produce NO entry, not a zero-value entry.
    path = roles_json_file([
        {"role": "Role A", "start": "2018-01", "end": "2020-01"},
        {"role": "Role B", "start": "2020-01", "end": "2022-01"},
    ])
    _, data = run_json("check_gaps.py", "--input", str(path))
    assert data["gaps"] == []


def test_exactly_six_month_gap(roles_json_file, run_json):
    path = roles_json_file([
        {"role": "Role A", "start": "2018-01", "end": "2020-01"},
        {"role": "Role B", "start": "2020-07", "end": "2022-01"},
    ])
    _, data = run_json("check_gaps.py", "--input", str(path))
    assert len(data["gaps"]) == 1
    assert data["gaps"][0]["gap_months"] == 6


def test_exactly_twenty_four_month_gap(roles_json_file, run_json):
    path = roles_json_file([
        {"role": "Role A", "start": "2018-01", "end": "2020-01"},
        {"role": "Role B", "start": "2022-01", "end": "2024-01"},
    ])
    _, data = run_json("check_gaps.py", "--input", str(path))
    assert len(data["gaps"]) == 1
    assert data["gaps"][0]["gap_months"] == 24


def test_twenty_five_month_gap(roles_json_file, run_json):
    path = roles_json_file([
        {"role": "Role A", "start": "2018-01", "end": "2020-01"},
        {"role": "Role B", "start": "2022-02", "end": "2024-01"},
    ])
    _, data = run_json("check_gaps.py", "--input", str(path))
    assert len(data["gaps"]) == 1
    assert data["gaps"][0]["gap_months"] == 25


def test_present_words_are_case_insensitive(roles_json_file, run_script):
    for word in ["present", "Present", "CURRENT", "Ongoing", "now"]:
        path = roles_json_file([{"role": "Role A", "start": "2020-01", "end": word}])
        result = run_script("check_gaps.py", "--input", str(path))
        assert result.returncode == 0, f"{word!r} failed: {result.stderr}"


def test_unsorted_input_is_sorted_by_start_date(roles_json_file, run_json):
    path = roles_json_file([
        {"role": "Later Role", "start": "2022-01", "end": "2024-01"},
        {"role": "Earlier Role", "start": "2018-01", "end": "2020-01"},
    ])
    _, data = run_json("check_gaps.py", "--input", str(path))
    assert data["chronological_order"] == ["Earlier Role", "Later Role"]


def test_multiple_gaps_all_reported(roles_json_file, run_json):
    path = roles_json_file([
        {"role": "Role A", "start": "2010-01", "end": "2012-01"},
        {"role": "Role B", "start": "2013-01", "end": "2015-01"},  # 12mo gap
        {"role": "Role C", "start": "2018-01", "end": "2020-01"},  # 36mo gap
    ])
    _, data = run_json("check_gaps.py", "--input", str(path))
    assert [g["gap_months"] for g in data["gaps"]] == [12, 36]


def test_stdin_input_mode(run_script):
    payload = json.dumps({"roles": [{"role": "Solo Role", "start": "2020-01", "end": "2022-01"}]})
    result = run_script("check_gaps.py", input=payload)
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["chronological_order"] == ["Solo Role"]
