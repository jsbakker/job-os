#!/usr/bin/env python3
"""Deterministic slug/base-name derivation for output filenames.

Two unrelated slug conventions live here because two different commands each
need one:

    applicant-job        tailor-resume.md Step 0's output base name
                          ("<applicant>-<job-slug>"), reused by /applied,
                          /update-status, and /prep-interview to locate the
                          same output/manifest/tracking files.

    company-title-slug    find-job-descriptions.md Step 7's filename for an
                          auto-downloaded job posting ("<Company>-<Title>",
                          title-cased, no applicant name involved).

Both are pure string transforms -- no judgment involved -- so they live in
one script instead of being re-typed as inline bash or re-described in prose
in four different command files.

Usage:
    python3 scripts/base_name.py applicant-job --applicant-name "Jane Doe" \\
        --job-filename "Acme_Corp_-_Senior_iOS_Developer.pdf"
    # -> jane-doe-acme-corp-senior-ios-developer

    python3 scripts/base_name.py company-title-slug --company "City of Vancouver" \\
        --job-title "Solutions Architect"
    # -> City-of-Vancouver-Solutions-Architect
"""
import argparse
import re
import sys


def _slugify_lower(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text)
    return text.strip("-")


def cmd_applicant_job(args) -> None:
    job_stem = re.sub(r"\.[^.]*$", "", args.job_filename)
    applicant = _slugify_lower(args.applicant_name)
    job_slug = _slugify_lower(job_stem)
    print(f"{applicant}-{job_slug}")


MINOR_WORDS = {"of", "the", "and", "a", "an", "in", "on", "for", "to", "at", "or"}


def cmd_company_title_slug(args) -> None:
    raw = f"{args.company.strip()}-{args.job_title.strip()}"
    words = re.split(r"[^A-Za-z0-9]+", raw)
    words = [w for w in words if w]
    titled_words = []
    for i, w in enumerate(words):
        if i > 0 and w.lower() in MINOR_WORDS:
            titled_words.append(w.lower())
        else:
            titled_words.append(w[:1].upper() + w[1:])
    print("-".join(titled_words))


def main() -> None:
    parser = argparse.ArgumentParser(description="Deterministic slug/base-name derivation.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_app = sub.add_parser("applicant-job", help="Derive the tailor-resume output base name.")
    p_app.add_argument("--applicant-name", required=True)
    p_app.add_argument("--job-filename", required=True)
    p_app.set_defaults(func=cmd_applicant_job)

    p_slug = sub.add_parser("company-title-slug", help="Derive a title-cased company-title slug.")
    p_slug.add_argument("--company", required=True)
    p_slug.add_argument("--job-title", required=True)
    p_slug.set_defaults(func=cmd_company_title_slug)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
