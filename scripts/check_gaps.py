#!/usr/bin/env python3
"""Deterministic employment-gap chronology math.

Sorting date ranges and computing the gap in months between adjacent roles
is pure date arithmetic. This script returns the raw gap data only -- it
does not decide what counts as a FAIL or a warning, since /tailor-resume
Step 8 (a boolean gate: >24mo FAILs) and /ats-validate Category D (a point
deduction: -8 once for any >24mo gap, -2 per 6-24mo gap up to -4) apply two
different policies on top of the same underlying gaps. The LLM extracts and
normalizes messy resume date-range text into the input shape below; the
script does the sort/diff.

Usage:
    python3 scripts/check_gaps.py --input /tmp/roles.json
    # or pipe JSON on stdin

Input shape:
    {"roles": [{"role": "Senior Engineer, Acme", "start": "2019-03", "end": "2021-06"},
               {"role": "Staff Engineer, Globex", "start": "2022-01", "end": "present"}]}
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

PRESENT_WORDS = {"present", "current", "ongoing", "now"}


def _parse_month(value: str) -> date:
    value = value.strip().lower()
    if value in PRESENT_WORDS:
        today = date.today()
        return date(today.year, today.month, 1)
    year, month = value.split("-")
    return date(int(year), int(month), 1)


def _months_between(earlier: date, later: date) -> int:
    return (later.year - earlier.year) * 12 + (later.month - earlier.month)


def _read_json(path: str | None) -> dict:
    if path:
        return json.loads(Path(path).read_text())
    return json.loads(sys.stdin.read())


def cmd_check(args) -> None:
    payload = _read_json(args.input)
    roles = payload.get("roles", [])

    parsed = [
        {
            "role": r["role"],
            "start": _parse_month(r["start"]),
            "end": _parse_month(r["end"]),
            "start_raw": r["start"],
            "end_raw": r["end"],
        }
        for r in roles
    ]
    parsed.sort(key=lambda r: r["start"])

    gaps = []
    for before, after in zip(parsed, parsed[1:]):
        gap_months = _months_between(before["end"], after["start"])
        if gap_months > 0:
            gaps.append({
                "gap_months": gap_months,
                "before_role": before["role"],
                "before_end": before["end_raw"],
                "after_role": after["role"],
                "after_start": after["start_raw"],
            })

    result = {
        "gaps": gaps,
        "chronological_order": [r["role"] for r in parsed],
    }
    print(json.dumps(result, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Deterministic employment-gap chronology math.")
    parser.add_argument("--input", help="Path to roles JSON. Reads stdin if omitted.")
    parser.set_defaults(func=cmd_check)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
