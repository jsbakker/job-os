#!/usr/bin/env python3
"""Deterministic PDF page-count check with the mdimport/mdls retry dance.

Spotlight indexing is asynchronous even after `mdimport`. The obvious failure
mode is `mdls` returning `(null)` on the first try -- but live testing turned
up a worse one: when a PDF at a given path is regenerated (same filename,
new content), a fast-following `mdls` call can return a stale *valid* page
count left over from the previous version of the file at that path, not
`(null)`. A bare "retry on null" loop never catches that, because a stale
number still matches. So this only trusts a page count once two consecutive
reads agree; if they keep disagreeing it returns the last reading after
exhausting retries rather than looping forever. This flaky-environment
workaround is exactly the kind of thing that's error-prone for an LLM to
reproduce correctly every single run, so it's scripted here. Uses `pdfinfo`
directly (one-shot, no retry, no staleness risk) when it's on PATH, since
this project's dependency set doesn't guarantee poppler is installed but
checks for it opportunistically.

Usage:
    python3 scripts/pdf_page_count.py output/jane-doe-acme-corp-role.pdf
    python3 scripts/pdf_page_count.py output/jane-doe-acme-corp-role.pdf --json
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import time


def _via_pdfinfo(pdf_path: str) -> int:
    output = subprocess.run(
        ["pdfinfo", pdf_path], capture_output=True, text=True, check=True
    ).stdout
    match = re.search(r"^Pages:\s*(\d+)", output, re.MULTILINE)
    if not match:
        raise RuntimeError("pdfinfo output did not contain a Pages: line")
    return int(match.group(1))


def _read_mdls(pdf_path: str) -> int | None:
    output = subprocess.run(
        ["mdls", "-name", "kMDItemNumberOfPages", pdf_path],
        capture_output=True, text=True,
    ).stdout
    match = re.search(r"=\s*(\d+)", output)
    return int(match.group(1)) if match else None


def _via_mdls(pdf_path: str, retries: int, retry_delay: float) -> int:
    subprocess.run(["mdimport", pdf_path], capture_output=True, text=True)
    time.sleep(retry_delay)

    previous = None
    for attempt in range(retries + 1):
        current = _read_mdls(pdf_path)
        if current is not None and current == previous:
            return current
        previous = current
        if attempt < retries:
            time.sleep(retry_delay)

    if previous is not None:
        return previous

    raise RuntimeError(f"mdls returned no page count for {pdf_path} after {retries + 1} attempt(s)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Deterministic PDF page count with retry.")
    parser.add_argument("pdf_path")
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--retry-delay", type=float, default=0.5)
    parser.add_argument("--json", action="store_true", help="Emit {\"pages\": n, \"method\": ...} instead of a bare integer.")
    args = parser.parse_args()

    try:
        if shutil.which("pdfinfo"):
            pages = _via_pdfinfo(args.pdf_path)
            method = "pdfinfo"
        else:
            pages = _via_mdls(args.pdf_path, args.retries, args.retry_delay)
            method = "mdls"
    except (subprocess.CalledProcessError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps({"pages": pages, "method": method}))
    else:
        print(pages)


if __name__ == "__main__":
    main()
