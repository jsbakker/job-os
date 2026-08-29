#!/usr/bin/env python3
"""Deterministic MM/DD/YYYY vs DD/MM/YYYY convention detection.

/import-applications needs to normalize dates from an arbitrary external
tracker to YYYY-MM-DD. Numeric dates are ambiguous per se (01/02/2026 could
be Jan 2 or Feb 1), but if any date anywhere in the file has a component
>12, that single date unambiguously reveals which convention the whole file
uses. Scanning for that disambiguating date and applying it file-wide is
pure logic -- no judgment -- so it's scripted here instead of re-run by hand
per file.

Usage:
    python3 scripts/detect_date_convention.py --input /tmp/dates.json
    # or pipe JSON on stdin

Input shape:
    {"dates": ["01/02/2026", "13/05/2025", "03/04/2025"]}
"""
import argparse
import json
import re
import sys
from pathlib import Path

DATE_RE = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})$")


def _read_json(path: str | None) -> dict:
    if path:
        return json.loads(Path(path).read_text())
    return json.loads(sys.stdin.read())


def _normalize(date_str: str, convention: str) -> str | None:
    match = DATE_RE.match(date_str.strip())
    if not match:
        return None
    first, second, year = match.groups()
    if convention == "MM/DD/YYYY":
        month, day = first, second
    else:
        day, month = first, second
    return f"{year}-{int(month):02d}-{int(day):02d}"


def cmd_detect(args) -> None:
    payload = _read_json(args.input)
    dates = payload.get("dates", [])

    convention = "ambiguous"
    disambiguating_date = None

    for date_str in dates:
        match = DATE_RE.match(date_str.strip())
        if not match:
            continue
        first, second, _year = (int(g) for g in match.groups())
        if first > 12:
            convention = "DD/MM/YYYY"
            disambiguating_date = date_str
            break
        if second > 12:
            convention = "MM/DD/YYYY"
            disambiguating_date = date_str
            break

    normalized = {}
    for date_str in dates:
        normalized[date_str] = None if convention == "ambiguous" else _normalize(date_str, convention)

    result = {
        "convention": convention,
        "disambiguating_date": disambiguating_date,
        "normalized": normalized,
    }
    print(json.dumps(result, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Deterministic date-convention detection.")
    parser.add_argument("--input", help="Path to dates JSON. Reads stdin if omitted.")
    parser.set_defaults(func=cmd_detect)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
