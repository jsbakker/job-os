#!/usr/bin/env python3
"""Fetch candidate job postings from the Adzuna API and maintain a seen-jobs ledger.

Usage:
    python3 scripts/find_jobs.py --title-variants "Staff Software Engineer,Senior Software Engineer" \\
        --location "Vancouver, BC" --country ca --max-days-old 21 --pages 2 \\
        --out output/job-search-candidates.json

Reads ADZUNA_APP_ID / ADZUNA_APP_KEY from a .env file at the repo root (or from
the environment, which takes precedence). Never prints the credential values.
"""
import argparse
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ADZUNA_BASE = "https://api.adzuna.com/v1/api/jobs"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) find-jobs-script/1.0"


def load_env(env_path: Path) -> dict:
    values = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def get_credentials() -> tuple:
    env_file_values = load_env(REPO_ROOT / ".env")
    app_id = os.environ.get("ADZUNA_APP_ID") or env_file_values.get("ADZUNA_APP_ID")
    app_key = os.environ.get("ADZUNA_APP_KEY") or env_file_values.get("ADZUNA_APP_KEY")
    return app_id, app_key


def http_get_json(url: str, params: dict) -> dict:
    query = "&".join(f"{k}={urllib.request.quote(str(v))}" for k, v in params.items())
    full_url = f"{url}?{query}"
    request = urllib.request.Request(full_url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def strip_html(raw: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def fetch_full_text(url: str) -> str:
    """Best-effort plain GET + tag-strip. Returns '' on any failure."""
    try:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read().decode("utf-8", errors="replace")
        text = strip_html(raw)
        # Heuristic: bot-walls / JS-only shells produce very little real text.
        if len(text) < 400:
            return ""
        return text
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
        return ""


def load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            return default
    return default


def normalize_key(company: str, title: str, location: str) -> str:
    parts = [re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-") for s in (company, title, location)]
    return "|".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Fetch job candidates from Adzuna.")
    parser.add_argument("--title-variants", required=True, help="Comma-separated title keywords, OR'd together")
    parser.add_argument("--location", required=True, help="Location to search, e.g. 'Vancouver, BC'")
    parser.add_argument("--country", default="ca", help="Adzuna country code (default: ca)")
    parser.add_argument("--max-days-old", type=int, default=21)
    parser.add_argument("--pages", type=int, default=2)
    parser.add_argument("--results-per-page", type=int, default=50)
    parser.add_argument("--out", required=True, help="Path to write the candidates JSON array")
    parser.add_argument("--ledger", default="output/job-search-seen.json", help="Path to the seen-jobs ledger")
    args = parser.parse_args()

    app_id, app_key = get_credentials()
    if not app_id or not app_key:
        print(
            "Missing Adzuna credentials.\n"
            "1. Sign up for a free app_id/app_key at https://developer.adzuna.com/\n"
            "2. Create a .env file at the repo root containing:\n"
            "   ADZUNA_APP_ID=your_app_id\n"
            "   ADZUNA_APP_KEY=your_app_key\n",
            file=sys.stderr,
        )
        return 1

    ledger_path = REPO_ROOT / args.ledger
    ledger = load_json(ledger_path, {})

    what_or = args.title_variants

    raw_results = []
    try:
        for page in range(1, args.pages + 1):
            data = http_get_json(
                f"{ADZUNA_BASE}/{args.country}/search/{page}",
                {
                    "app_id": app_id,
                    "app_key": app_key,
                    "what_or": what_or,
                    "where": args.location,
                    "results_per_page": args.results_per_page,
                    "max_days_old": args.max_days_old,
                    "content-type": "application/json",
                },
            )
            page_results = data.get("results", [])
            if not page_results:
                break
            raw_results.extend(page_results)
    except (urllib.error.URLError, urllib.error.HTTPError) as exc:
        print(f"Adzuna API request failed: {exc}", file=sys.stderr)
        return 1

    candidates = []
    new_fetch_count = 0
    for item in raw_results:
        job_id = str(item.get("id", ""))
        title = item.get("title", "")
        company = (item.get("company") or {}).get("display_name", "")
        location = (item.get("location") or {}).get("display_name", "")
        redirect_url = item.get("redirect_url", "")
        snippet = item.get("description", "")
        created = item.get("created", "")
        dedupe_key = normalize_key(company, title, location)

        existing = ledger.get(job_id)
        if existing is None:
            # Also check the secondary dedupe key in case Adzuna assigned a new id
            # to a cross-posted listing we already evaluated.
            existing = next(
                (v for v in ledger.values() if v.get("dedupe_key") == dedupe_key),
                None,
            )

        if existing is not None:
            # Already evaluated in a prior run: reuse cached data, no network calls.
            candidate = dict(existing)
            candidate["id"] = job_id
            candidates.append(candidate)
            continue

        full_text = fetch_full_text(redirect_url) if redirect_url else ""
        new_fetch_count += 1
        candidate = {
            "id": job_id,
            "dedupe_key": dedupe_key,
            "title": title,
            "company": company,
            "location": location,
            "redirect_url": redirect_url,
            "created": created,
            "snippet": snippet,
            "full_text": full_text,
            "full_text_fetched": bool(full_text),
            "score": None,
            "saved": False,
            "date_found": created[:10] if created else "",
        }
        ledger[job_id] = {k: v for k, v in candidate.items() if k != "full_text"}
        candidates.append(candidate)

    out_path = REPO_ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(candidates, indent=2))

    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(json.dumps(ledger, indent=2))

    needs_webfetch = sum(1 for c in candidates if not c.get("full_text_fetched") and c.get("redirect_url"))
    print(
        f"Fetched {len(candidates)} candidate(s) ({new_fetch_count} new). "
        f"{needs_webfetch} need a WebFetch fallback for full text. "
        f"Written to {args.out}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
