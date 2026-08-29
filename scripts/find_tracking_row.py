#!/usr/bin/env python3
"""Deterministic multi-signal row lookup in tracking/applications.ndjson.

/update-status, /prep-interview, and /import-applications all need to find
the row(s) in tracking/applications.ndjson that correspond to a given job,
matching on any of: the tailor-resume base name appearing in resume_file/
cover_letter_file, an exact job_id, or a case-insensitive company+title
match. Re-describing that predicate in prose in three different command
files is how it drifted (one caller ended up only checking a subset of the
signals it claimed to check) -- this script is the single implementation.

It only returns candidates; it never talks to the user. "Zero matches, stop"
and "more than one match, ask which one" stay as prose in each calling
command, the same way score_job_match.py never handles the user-facing
framing of a rescore itself -- matching stays deterministic, disambiguation
stays judgment.

Usage:
    python3 scripts/find_tracking_row.py lookup --file tracking/applications.ndjson \\
        --base-name jane-doe-acme-corp-staff-engineer
    python3 scripts/find_tracking_row.py lookup --file tracking/applications.ndjson \\
        --company "Acme Corp" --position-title "Staff Engineer"
"""
import argparse
import json
import sys
from pathlib import Path


def cmd_lookup(args) -> None:
    if not any([args.base_name, args.job_id, args.company and args.position_title]):
        print("At least one of --base-name, --job-id, or --company+--position-title is required.", file=sys.stderr)
        sys.exit(2)

    path = Path(args.file)
    matches = []
    if path.exists():
        for index, line in enumerate(path.read_text().splitlines()):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            signals = []

            if args.base_name:
                resume_file = row.get("resume_file") or ""
                cover_letter_file = row.get("cover_letter_file") or ""
                if args.base_name in resume_file or args.base_name in cover_letter_file:
                    signals.append("base_name")

            if args.job_id and row.get("job_id") is not None:
                if str(row["job_id"]) == str(args.job_id):
                    signals.append("job_id")

            if args.company and args.position_title:
                row_company = (row.get("company") or "").casefold()
                row_title = (row.get("position_title") or "").casefold()
                if row_company == args.company.casefold() and row_title == args.position_title.casefold():
                    signals.append("company_title")

            if signals:
                matches.append({"index": index, "row": row, "matched_signals": signals})

    result = {"match_count": len(matches), "matches": matches}
    print(json.dumps(result, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Deterministic multi-signal tracking-row lookup.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_lookup = sub.add_parser("lookup", help="Find rows matching any given signal.")
    p_lookup.add_argument("--file", required=True, help="Path to tracking/applications.ndjson.")
    p_lookup.add_argument("--base-name", default=None)
    p_lookup.add_argument("--job-id", default=None)
    p_lookup.add_argument("--company", default=None)
    p_lookup.add_argument("--position-title", default=None)
    p_lookup.set_defaults(func=cmd_lookup)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
