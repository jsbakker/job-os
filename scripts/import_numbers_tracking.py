#!/usr/bin/env python3
"""One-time migration: import output/JobApplicationTrackingLatest.numbers into
tracking/applications.ndjson.

This is NOT part of the recurring /applied or /find-job-descriptions flow — it's a
one-off tool to bring historical application data into the new tracking format.
Historical rows have no salary_range / glassdoor_rating / match_score / resume_file /
cover_letter_file / source data, since that pipeline didn't exist yet when those
applications were made.

Requires the `numbers-parser` package, which reads Apple's undocumented .numbers
binary format. Install it in an isolated environment rather than your main Python
install, to avoid dependency conflicts with unrelated projects:

    python3 -m venv .venv-tools
    ./.venv-tools/bin/pip install numbers-parser
    ./.venv-tools/bin/python scripts/import_numbers_tracking.py

Usage:
    python3 scripts/import_numbers_tracking.py \\
        [--source output/JobApplicationTrackingLatest.numbers] \\
        [--out tracking/applications.ndjson]
"""
import argparse
import json
import sys
from pathlib import Path

try:
    from numbers_parser import Document
except ImportError:
    print(
        "numbers-parser is not installed. Run this script from the isolated venv:\n"
        "  python3 -m venv .venv-tools\n"
        "  ./.venv-tools/bin/pip install numbers-parser\n"
        "  ./.venv-tools/bin/python scripts/import_numbers_tracking.py\n",
        file=sys.stderr,
    )
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parent.parent

EXPECTED_HEADER = [
    "Date Applied",
    "Company",
    "Position Title",
    "Job ID",
    "Application status",
    "Apply Method",
    "Job Posting URL",
    "Recommended Ask",
]


def normalize_job_id(value) -> str:
    if value is None or value == "":
        return None
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else str(value)
    return str(value)


def normalize_str(value) -> str:
    if value is None or value == "":
        return None
    return str(value).strip()


def normalize_date(value) -> str:
    if value is None:
        return None
    return value.strftime("%Y-%m-%d")


def row_to_record(row: dict) -> dict:
    return {
        "date_applied": normalize_date(row.get("Date Applied")),
        "company": normalize_str(row.get("Company")),
        "position_title": normalize_str(row.get("Position Title")),
        "job_id": normalize_job_id(row.get("Job ID")),
        "application_status": normalize_str(row.get("Application status")),
        "apply_method": normalize_str(row.get("Apply Method")),
        "job_posting_url": normalize_str(row.get("Job Posting URL")),
        "recommended_ask": normalize_str(row.get("Recommended Ask")),
        "salary_range": None,
        "glassdoor_rating": None,
        "match_score": None,
        "resume_file": None,
        "cover_letter_file": None,
        "source": None,
    }


def main():
    parser = argparse.ArgumentParser(description="Import the legacy .numbers tracking sheet into NDJSON.")
    parser.add_argument("--source", default="output/JobApplicationTrackingLatest.numbers")
    parser.add_argument("--out", default="tracking/applications.ndjson")
    args = parser.parse_args()

    source_path = REPO_ROOT / args.source
    if not source_path.exists():
        print(f"Source file not found: {source_path}", file=sys.stderr)
        return 1

    doc = Document(str(source_path))
    table = doc.sheets[0].tables[0]
    rows = table.rows(values_only=True)
    header, data_rows = rows[0], rows[1:]

    if header != EXPECTED_HEADER:
        print(
            f"Warning: header does not match expected columns.\n"
            f"  Expected: {EXPECTED_HEADER}\n"
            f"  Found:    {header}\n"
            "Proceeding by column position anyway.",
            file=sys.stderr,
        )

    records = []
    for raw_row in data_rows:
        row = dict(zip(header, raw_row))
        if not any(v not in (None, "") for v in row.values()):
            continue  # skip fully blank rows
        records.append(row_to_record(row))

    out_path = REPO_ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")

    print(f"Imported {len(records)} row(s) from {args.source} into {args.out}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
