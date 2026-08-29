#!/usr/bin/env python3
"""Deterministic input-file hashing for /tailor-resume's staleness check.

The set of files that determine whether a tailored resume needs regenerating
is fixed (blueprint.md, formatting.md, the static template/ files, every
template/experience/*.md, every career-goals file, the job description, and
the optional salary-expectations.md) -- the LLM only ever supplies the one
variable input, the job description filename. Hashing and comparing that
list by hand (via shasum + string comparison) is pure mechanics; this script
owns it so tailor-resume.md Step 0's rehash and Step 9's write always agree
on exactly which files matter and how "changed" is defined.

Usage:
    python3 scripts/manifest_check.py hash --job-description Acme-Corp-Role.pdf
    python3 scripts/manifest_check.py compare --job-description Acme-Corp-Role.pdf \\
        --manifest output/jane-doe-acme-corp-role.manifest
"""
import argparse
import glob
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _input_files(job_description: str) -> list[str]:
    files: list[str] = ["blueprint.md", "formatting.md"]
    files += [
        "template/contact-info.txt",
        "template/all-skills.md",
        "template/certifications.md",
        "template/education.md",
        "template/publications.md",
    ]
    files += sorted(glob.glob("template/experience/*.md", root_dir=REPO_ROOT))
    files += sorted(glob.glob("variable-input/career-goals/*.md", root_dir=REPO_ROOT))
    files.append(f"variable-input/job-descriptions/{job_description}")
    if (REPO_ROOT / "variable-input/salary-expectations.md").exists():
        files.append("variable-input/salary-expectations.md")
    return files


def _hash_file(relpath: str) -> str | None:
    path = REPO_ROOT / relpath
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compute_hashes(job_description: str) -> dict[str, str]:
    result = {}
    for relpath in _input_files(job_description):
        digest = _hash_file(relpath)
        if digest is not None:
            result[relpath] = digest
    return result


def cmd_hash(args) -> None:
    print(json.dumps(compute_hashes(args.job_description), indent=2))


def cmd_compare(args) -> None:
    current = compute_hashes(args.job_description)

    manifest_raw = json.loads(Path(args.manifest).read_text())
    prior = manifest_raw.get("inputs", {})

    changed = sorted(f for f in current if f in prior and current[f] != prior[f])
    new_files = sorted(f for f in current if f not in prior)
    removed_files = sorted(f for f in prior if f not in current)

    result = {
        "all_match": not (changed or new_files or removed_files),
        "changed_files": changed,
        "new_files": new_files,
        "removed_files": removed_files,
    }
    print(json.dumps(result, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Deterministic input-file hashing for /tailor-resume.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_hash = sub.add_parser("hash", help="Compute sha256 hashes for every tailor-resume input file.")
    p_hash.add_argument("--job-description", required=True, help="Filename under variable-input/job-descriptions/.")
    p_hash.set_defaults(func=cmd_hash)

    p_compare = sub.add_parser("compare", help="Compare current input hashes against a prior manifest.")
    p_compare.add_argument("--job-description", required=True)
    p_compare.add_argument("--manifest", required=True, help="Path to the prior output/<base-name>.manifest file.")
    p_compare.set_defaults(func=cmd_compare)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
