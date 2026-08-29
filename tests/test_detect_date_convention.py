"""Tests for scripts/detect_date_convention.py.

Used by /import-applications to disambiguate MM/DD/YYYY vs. DD/MM/YYYY: if
any date anywhere in the file has a component >12, that single date
unambiguously reveals the whole file's convention.
"""
import json


def _dates_file(tmp_path, dates):
    path = tmp_path / "dates.json"
    path.write_text(json.dumps({"dates": dates}))
    return path


def test_mm_dd_disambiguation(tmp_path, run_json):
    # Second component (13) > 12 -> must be MM/DD/YYYY.
    path = _dates_file(tmp_path, ["03/04/2026", "01/13/2026", "07/09/2026"])
    _, data = run_json("detect_date_convention.py", "--input", str(path))
    assert data["convention"] == "MM/DD/YYYY"
    assert data["disambiguating_date"] == "01/13/2026"
    assert data["normalized"]["01/13/2026"] == "2026-01-13"
    assert data["normalized"]["03/04/2026"] == "2026-03-04"  # applied file-wide


def test_dd_mm_disambiguation(tmp_path, run_json):
    # First component (25) > 12 -> must be DD/MM/YYYY.
    path = _dates_file(tmp_path, ["25/12/2025", "03/04/2026"])
    _, data = run_json("detect_date_convention.py", "--input", str(path))
    assert data["convention"] == "DD/MM/YYYY"
    assert data["disambiguating_date"] == "25/12/2025"
    assert data["normalized"]["25/12/2025"] == "2025-12-25"
    assert data["normalized"]["03/04/2026"] == "2026-04-03"  # applied file-wide


def test_fully_ambiguous_when_nothing_disambiguates(tmp_path, run_json):
    path = _dates_file(tmp_path, ["03/04/2026", "01/05/2026", "07/09/2026"])
    _, data = run_json("detect_date_convention.py", "--input", str(path))
    assert data["convention"] == "ambiguous"
    assert data["disambiguating_date"] is None
    assert all(v is None for v in data["normalized"].values())


def test_disambiguating_date_not_first_still_applies_file_wide(tmp_path, run_json):
    path = _dates_file(tmp_path, ["01/02/2026", "03/04/2026", "20/06/2026", "05/07/2026"])
    _, data = run_json("detect_date_convention.py", "--input", str(path))
    assert data["convention"] == "DD/MM/YYYY"
    assert data["disambiguating_date"] == "20/06/2026"
    # An earlier, individually-ambiguous date still gets normalized per the
    # file-wide convention once it's determined.
    assert data["normalized"]["01/02/2026"] == "2026-02-01"


def test_malformed_date_string_skipped_gracefully(tmp_path, run_json):
    # "2026-01-15" (ISO format, not the M/D/YYYY shape DATE_RE expects) and
    # plain garbage should not crash detection or count toward disambiguation.
    # "13/05/2025" has 13 in the FIRST position, so it disambiguates as
    # DD/MM/YYYY (day=13, month=05), not MM/DD/YYYY.
    path = _dates_file(tmp_path, ["2026-01-15", "not-a-date", "13/05/2025"])
    _, data = run_json("detect_date_convention.py", "--input", str(path))
    assert data["convention"] == "DD/MM/YYYY"
    assert data["normalized"]["2026-01-15"] is None
    assert data["normalized"]["not-a-date"] is None
    assert data["normalized"]["13/05/2025"] == "2025-05-13"


def test_zero_padding_in_normalized_output(tmp_path, run_json):
    path = _dates_file(tmp_path, ["1/2/2026", "9/13/2026"])
    _, data = run_json("detect_date_convention.py", "--input", str(path))
    assert data["convention"] == "MM/DD/YYYY"  # 13 in second position disambiguates
    assert data["normalized"]["1/2/2026"] == "2026-01-02"


def test_shape_valid_but_calendar_invalid_date_is_a_known_limitation(tmp_path, run_json):
    # "13/13/2025" has BOTH components > 12. The script has no calendar
    # validation, so it hits the `first > 12` branch first (DD/MM/YYYY) and
    # happily emits a nonsense "2025-13-13" as "normalized." This is
    # documented current behavior, not something this test fixes.
    path = _dates_file(tmp_path, ["13/13/2025"])
    _, data = run_json("detect_date_convention.py", "--input", str(path))
    assert data["convention"] == "DD/MM/YYYY"
    assert data["normalized"]["13/13/2025"] == "2025-13-13"


def test_stdin_input_mode(run_script):
    payload = json.dumps({"dates": ["01/13/2026"]})
    result = run_script("detect_date_convention.py", input=payload)
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["convention"] == "MM/DD/YYYY"
