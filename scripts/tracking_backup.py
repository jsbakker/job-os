#!/usr/bin/env python3
"""Deterministic backup/restore of tracking/ files for /test-fixtures.

The "tracking" fixture set in /test-fixtures has to safely stash the user's
real tracking/applications.ndjson (and its learned-preferences companions)
before overwriting them with fabricated fixture data, then put everything
back exactly afterward -- regardless of whether the fixture run in between
succeeded, failed, or errored. Doing that with mktemp -d + a shell cp/rm loop
works, but a randomized directory name makes the invocation different every
run, which means it can never be allowlisted in .claude/settings.json -- only
a fixed, static command string can be. This script owns the same backup/
restore logic against a single fixed location outside the repo tree instead,
so `python3 scripts/tracking_backup.py backup` and `... restore` are each one
static string, regardless of what's actually being backed up.

Usage:
    python3 scripts/tracking_backup.py backup
    python3 scripts/tracking_backup.py restore
"""
import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TARGET_FILES = [
    "tracking/applications.ndjson",
    "tracking/learned-preferences.md",
    "tracking/.learned-preferences.hash",
]
BACKUP_DIR = Path(tempfile.gettempdir()) / "job-os-test-fixtures-backup"


def cmd_backup(args) -> None:
    if BACKUP_DIR.exists():
        if not args.force:
            print(json.dumps({
                "error": "backup_dir_already_exists",
                "backup_dir": str(BACKUP_DIR),
                "detail": "Looks like a leftover from an interrupted prior run. "
                          "Inspect it, then remove it yourself before backing up again "
                          "(or pass --force to overwrite it).",
            }, indent=2))
            sys.exit(1)
        shutil.rmtree(BACKUP_DIR)

    BACKUP_DIR.mkdir(parents=True)
    result = {}
    for relpath in TARGET_FILES:
        src = REPO_ROOT / relpath
        if src.exists():
            shutil.copy2(src, BACKUP_DIR / src.name)
            result[relpath] = "existed"
        else:
            result[relpath] = "absent"
    print(json.dumps(result, indent=2))


def cmd_restore(args) -> None:
    if not BACKUP_DIR.exists():
        print(json.dumps({
            "error": "no_backup_found",
            "backup_dir": str(BACKUP_DIR),
            "detail": "Nothing to restore -- was `backup` run first?",
        }, indent=2))
        sys.exit(1)

    result = {}
    for relpath in TARGET_FILES:
        dest = REPO_ROOT / relpath
        backup_copy = BACKUP_DIR / dest.name
        if backup_copy.exists():
            shutil.copy2(backup_copy, dest)
            result[relpath] = "restored"
        else:
            if dest.exists():
                dest.unlink()
                result[relpath] = "removed"
            else:
                result[relpath] = "already_absent"
    shutil.rmtree(BACKUP_DIR)
    print(json.dumps(result, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Backup/restore tracking/ files for /test-fixtures.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_backup = sub.add_parser("backup", help="Back up the fixed set of tracking/ files.")
    p_backup.add_argument("--force", action="store_true", help="Overwrite an existing (leftover) backup.")
    p_backup.set_defaults(func=cmd_backup)

    p_restore = sub.add_parser("restore", help="Restore the fixed set of tracking/ files from backup.")
    p_restore.set_defaults(func=cmd_restore)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
