"""Tests for scripts/find_tracking_row.py.

Multi-signal lookup used by /update-status, /prep-interview, and (with a
subset of signals) /import-applications. The script only returns
candidates -- it never talks to the user; "zero matches, stop" and "more
than one match, ask which one" stay as prose in each calling command.
"""


def test_zero_matches_on_nonexistent_file(tmp_path, run_json):
    _, data = run_json(
        "find_tracking_row.py", "lookup",
        "--file", str(tmp_path / "does-not-exist.ndjson"),
        "--base-name", "dana-whitfield-acme-role",
    )
    assert data == {"match_count": 0, "matches": []}


def test_zero_matches_on_empty_file(ndjson_file, run_json):
    path = ndjson_file([])
    _, data = run_json(
        "find_tracking_row.py", "lookup",
        "--file", str(path), "--base-name", "dana-whitfield-acme-role",
    )
    assert data == {"match_count": 0, "matches": []}


def test_zero_matches_when_no_row_matches(ndjson_file, run_json):
    path = ndjson_file([
        {"company": "Harborline Logistics", "position_title": "Software Engineer II",
         "job_id": None, "resume_file": None, "cover_letter_file": None},
    ])
    _, data = run_json(
        "find_tracking_row.py", "lookup",
        "--file", str(path), "--company", "Solace Metrics", "--position-title", "Senior Software Engineer",
    )
    assert data["match_count"] == 0


def test_single_match_by_base_name_substring(ndjson_file, run_json):
    path = ndjson_file([
        {"company": "Solace Metrics", "position_title": "Senior Software Engineer",
         "job_id": None, "resume_file": "output/dana-whitfield-solace-metrics.pdf", "cover_letter_file": None},
    ])
    _, data = run_json(
        "find_tracking_row.py", "lookup",
        "--file", str(path), "--base-name", "dana-whitfield-solace-metrics",
    )
    assert data["match_count"] == 1
    assert data["matches"][0]["matched_signals"] == ["base_name"]


def test_base_name_matches_within_cover_letter_file_too(ndjson_file, run_json):
    path = ndjson_file([
        {"company": "Solace Metrics", "position_title": "Senior Software Engineer",
         "job_id": None, "resume_file": None,
         "cover_letter_file": "output/dana-whitfield-solace-metrics-cover-letter.pdf"},
    ])
    _, data = run_json(
        "find_tracking_row.py", "lookup",
        "--file", str(path), "--base-name", "dana-whitfield-solace-metrics",
    )
    assert data["match_count"] == 1
    assert data["matches"][0]["matched_signals"] == ["base_name"]


def test_multi_signal_convergence_lists_all_matched_signals(ndjson_file, run_json):
    path = ndjson_file([
        {"company": "Solace Metrics", "position_title": "Senior Software Engineer",
         "job_id": "REQ-1234", "resume_file": "output/dana-whitfield-solace-metrics.pdf",
         "cover_letter_file": None},
    ])
    _, data = run_json(
        "find_tracking_row.py", "lookup",
        "--file", str(path),
        "--base-name", "dana-whitfield-solace-metrics",
        "--job-id", "REQ-1234",
        "--company", "Solace Metrics",
        "--position-title", "Senior Software Engineer",
    )
    assert data["match_count"] == 1
    assert sorted(data["matches"][0]["matched_signals"]) == ["base_name", "company_title", "job_id"]


def test_ambiguous_multiple_matches_for_reapply(ndjson_file, run_json):
    path = ndjson_file([
        {"company": "Solace Metrics", "position_title": "Senior Software Engineer",
         "job_id": None, "resume_file": None, "cover_letter_file": None, "date_applied": "2026-01-01"},
        {"company": "Solace Metrics", "position_title": "Senior Software Engineer",
         "job_id": None, "resume_file": None, "cover_letter_file": None, "date_applied": "2026-06-01"},
    ])
    _, data = run_json(
        "find_tracking_row.py", "lookup",
        "--file", str(path), "--company", "Solace Metrics", "--position-title", "Senior Software Engineer",
    )
    assert data["match_count"] == 2
    assert {m["row"]["date_applied"] for m in data["matches"]} == {"2026-01-01", "2026-06-01"}


def test_job_id_type_coercion_int_vs_string(ndjson_file, run_json):
    path = ndjson_file([
        {"company": "Harborline Logistics", "position_title": "Software Engineer II",
         "job_id": 12345, "resume_file": None, "cover_letter_file": None},
    ])
    _, data = run_json(
        "find_tracking_row.py", "lookup",
        "--file", str(path), "--job-id", "12345",
    )
    assert data["match_count"] == 1
    assert data["matches"][0]["matched_signals"] == ["job_id"]


def test_company_title_matching_is_case_insensitive(ndjson_file, run_json):
    path = ndjson_file([
        {"company": "SOLACE METRICS", "position_title": "senior software engineer",
         "job_id": None, "resume_file": None, "cover_letter_file": None},
    ])
    _, data = run_json(
        "find_tracking_row.py", "lookup",
        "--file", str(path), "--company", "Solace Metrics", "--position-title", "Senior Software Engineer",
    )
    assert data["match_count"] == 1


def test_blank_lines_are_skipped(tmp_path, run_json):
    path = tmp_path / "applications.ndjson"
    path.write_text(
        '{"company": "Solace Metrics", "position_title": "Senior Software Engineer", '
        '"job_id": null, "resume_file": null, "cover_letter_file": null}\n'
        "\n"
        "   \n"
    )
    _, data = run_json(
        "find_tracking_row.py", "lookup",
        "--file", str(path), "--company", "Solace Metrics", "--position-title", "Senior Software Engineer",
    )
    assert data["match_count"] == 1


def test_malformed_json_line_currently_raises_uncaught(tmp_path, run_script):
    # Locks in CURRENT behavior: a malformed line is not skipped like a blank
    # line is -- json.loads raises uncaught, producing a nonzero exit and a
    # traceback on stderr. If a defensive skip-malformed-lines fix is added
    # later, this test should flip to assert the new behavior in that change.
    path = tmp_path / "applications.ndjson"
    path.write_text("{not valid json\n")
    result = run_script(
        "find_tracking_row.py", "lookup",
        "--file", str(path), "--company", "Solace Metrics", "--position-title", "Senior Software Engineer",
    )
    assert result.returncode != 0
    assert "JSONDecodeError" in result.stderr


def test_no_signal_provided_exits_with_code_2(tmp_path, run_script):
    path = tmp_path / "applications.ndjson"
    path.write_text("")
    result = run_script("find_tracking_row.py", "lookup", "--file", str(path))
    assert result.returncode == 2
    assert "At least one of" in result.stderr
