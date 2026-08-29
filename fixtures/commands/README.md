# Command Fixtures

A manual, periodic calibration check for the pipeline *mechanics* introduced by the `refactor-commands` branch's Python scripts (`base_name.py`, `manifest_check.py`, `hash_sidecar.py`, `find_tracking_row.py`, `detect_date_convention.py`) as they're actually exercised through the real slash commands — not an automated test suite (that's what `tests/` and `pytest` are for; these commands need an LLM's judgment and can't run in CI). Sibling to `fixtures/scoring/`, which covers `/tailor-resume` Step 2b/2c's *scoring rubric* specifically — this directory covers different ground: does the stale-check actually skip a no-op run, does the tracking-row lookup actually ask when a reapply is ambiguous, does date-convention detection actually work through a real import.

## What's here

- `tailor-resume/` — reuses `fixtures/scoring/fixture-01-strong-match/`'s job posting to verify `manifest_check.py`'s stale-check short-circuits a genuine no-op second run, calibrated against **the example applicant** (Dana Whitfield, shipped in `template/` on `main`).
- `applied-update-status-prep-interview/` — a small fabricated `tracking/applications.ndjson` fixture plus three tiny fabricated job-description stubs, exercising `find_tracking_row.py`'s single-match, ambiguous-match, and zero-match branches through `/update-status` and `/prep-interview`.
- `import-applications/` — a small fabricated legacy-tracker CSV exercising `detect_date_convention.py`'s both branches (a disambiguating date and a genuinely ambiguous one) through `/import-applications`.

## Safety notes — read before running the second fixture

`variable-input/job-descriptions/` is gitignored, so copying a fixture JD into it is low-risk (delete it afterward). **`tracking/applications.ndjson` is not gitignored** on this branch. Before running the `applied-update-status-prep-interview/` fixture, back up any existing `tracking/applications.ndjson` (and, if you plan to live-run `/applied` per that fixture's optional step, `tracking/learned-preferences.md` and `tracking/.learned-preferences.hash` too) to somewhere *outside* the repo tree — not to a sibling path inside `tracking/`, which risks getting swept into a future `git add -A`. Restore afterward and re-check `git status` before doing anything else.

## Run this from `main` (or this branch), with `template/` unmodified

Same rule as `fixtures/scoring/`: these fixtures are calibrated against Dana Whitfield's specific profile. Running them against a personalized `template/` on a fork produces different, not-comparable results.

## When to run it

- After editing any of the five scripts named above, or the `.claude/skills/*/SKILL.md` steps that invoke them.
- Periodically as a sanity check, same as `fixtures/scoring/`.

## Cleanup

Every fixture run creates scratch files under `output/` and (for the first fixture) `variable-input/job-descriptions/`. Delete them afterward — they aren't real applications or resumes and shouldn't clutter your working tree. Never run `/applied` against the `tailor-resume/` fixture's job posting for real.
