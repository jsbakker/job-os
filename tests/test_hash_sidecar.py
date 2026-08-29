"""Tests for scripts/hash_sidecar.py.

Used by /learn-preferences, /applied, and /import-applications to detect
hand-edits to tracking/learned-preferences.md before overwriting it.
"""
import hashlib
import json


def test_first_time_when_both_missing(tmp_path, run_json):
    _, data = run_json(
        "hash_sidecar.py", "check",
        "--file", str(tmp_path / "nope.md"),
        "--sidecar", str(tmp_path / "nope.hash"),
    )
    assert data == {"first_time": True, "hand_edited": False}


def test_first_time_when_only_file_exists(tmp_path, run_json):
    # Not just "never run" -- also covers "tracked file exists but the
    # sidecar was never written." Reports identically to genuinely-never-run;
    # this is real, intentional-looking current behavior, not a bug.
    tracked = tmp_path / "learned-preferences.md"
    tracked.write_text("some content\n")
    _, data = run_json(
        "hash_sidecar.py", "check",
        "--file", str(tracked),
        "--sidecar", str(tmp_path / "nope.hash"),
    )
    assert data == {"first_time": True, "hand_edited": False}


def test_first_time_when_only_sidecar_exists(tmp_path, run_json):
    # The inverse asymmetric case: sidecar present, tracked file missing
    # (e.g. deleted after being tracked).
    sidecar = tmp_path / "learned-preferences.hash"
    sidecar.write_text("deadbeef\n")
    _, data = run_json(
        "hash_sidecar.py", "check",
        "--file", str(tmp_path / "learned-preferences.md"),
        "--sidecar", str(sidecar),
    )
    assert data == {"first_time": True, "hand_edited": False}


def test_hand_edited_false_when_hash_matches(tmp_path, run_json):
    tracked = tmp_path / "learned-preferences.md"
    tracked.write_text("stable content\n")
    digest = hashlib.sha256(tracked.read_bytes()).hexdigest()
    sidecar = tmp_path / "learned-preferences.hash"
    sidecar.write_text(digest + "\n")

    _, data = run_json(
        "hash_sidecar.py", "check",
        "--file", str(tracked), "--sidecar", str(sidecar),
    )
    assert data == {"first_time": False, "hand_edited": False}


def test_hand_edited_true_when_hash_mismatches(tmp_path, run_json):
    tracked = tmp_path / "learned-preferences.md"
    tracked.write_text("content after a hand-edit\n")
    sidecar = tmp_path / "learned-preferences.hash"
    sidecar.write_text("not-the-real-hash\n")

    _, data = run_json(
        "hash_sidecar.py", "check",
        "--file", str(tracked), "--sidecar", str(sidecar),
    )
    assert data == {"first_time": False, "hand_edited": True}


def test_sidecar_without_trailing_newline_still_matches(tmp_path, run_json):
    # A manually-crafted sidecar with no trailing newline should still
    # compare equal, since check() strips whitespace before comparing.
    tracked = tmp_path / "learned-preferences.md"
    tracked.write_text("stable content\n")
    digest = hashlib.sha256(tracked.read_bytes()).hexdigest()
    sidecar = tmp_path / "learned-preferences.hash"
    sidecar.write_text(digest)  # no trailing newline

    _, data = run_json(
        "hash_sidecar.py", "check",
        "--file", str(tracked), "--sidecar", str(sidecar),
    )
    assert data == {"first_time": False, "hand_edited": False}


def test_write_produces_correct_sha256(tmp_path, run_json):
    tracked = tmp_path / "learned-preferences.md"
    tracked.write_text("some real content\n")
    sidecar = tmp_path / "learned-preferences.hash"

    _, data = run_json(
        "hash_sidecar.py", "write",
        "--file", str(tracked), "--sidecar", str(sidecar),
    )
    expected = hashlib.sha256(tracked.read_bytes()).hexdigest()
    assert data == {"hash": expected}
    assert sidecar.read_text().strip() == expected


def test_write_then_check_round_trip_reports_no_hand_edit(tmp_path, run_script, run_json):
    tracked = tmp_path / "learned-preferences.md"
    tracked.write_text("freshly generated content\n")
    sidecar = tmp_path / "learned-preferences.hash"

    write_result = run_script(
        "hash_sidecar.py", "write",
        "--file", str(tracked), "--sidecar", str(sidecar),
    )
    assert write_result.returncode == 0

    _, data = run_json(
        "hash_sidecar.py", "check",
        "--file", str(tracked), "--sidecar", str(sidecar),
    )
    assert data == {"first_time": False, "hand_edited": False}


def test_edit_after_write_is_detected(tmp_path, run_script, run_json):
    tracked = tmp_path / "learned-preferences.md"
    tracked.write_text("original content\n")
    sidecar = tmp_path / "learned-preferences.hash"
    run_script("hash_sidecar.py", "write", "--file", str(tracked), "--sidecar", str(sidecar))

    tracked.write_text("original content\nplus a hand-edit\n")

    _, data = run_json(
        "hash_sidecar.py", "check",
        "--file", str(tracked), "--sidecar", str(sidecar),
    )
    assert data == {"first_time": False, "hand_edited": True}
