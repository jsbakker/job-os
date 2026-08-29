---
name: test-fixtures
description: Run this repo's LLM-based test fixtures (fixtures/scoring and fixtures/commands) end to end and report pass/fail, with automatic backup and restore of any real tracking data touched
---

Run the fixture set(s) selected by: $ARGUMENTS

You are running this project's manual, periodic calibration checks for real — copying fixture inputs into place, invoking the actual `/tailor-resume`, `/update-status`, `/prep-interview`, and `/import-applications` command logic inline (there is no subprocess/API mechanism for one command file to literally call another — invoking a command's documented steps inline, right now, is this project's established composition pattern, per `find-job-descriptions.md` Step 1's self-bootstrap of `/learn-preferences`), comparing actual results against each fixture's `expected.md`, and cleaning up every scratch file and every mutated tracking file afterward — regardless of whether a check passed, failed, or errored partway through.

---

## Help Check

If `$ARGUMENTS`, trimmed of whitespace, equals `help` (case-insensitive), print the block below and stop. Do not run any other step.

```
/test-fixtures — Runs this repo's documented LLM-based fixture checks (fixtures/scoring and fixtures/commands) by invoking the real commands inline, compares results against each fixture's expected.md, and cleans up all scratch files and mutated tracking data afterward.

Usage:
  /test-fixtures [all|scoring|tailor-resume|tracking|import-applications]

Fixture sets:
  scoring              - the three fixtures/scoring/* rubric-calibration checks
  tailor-resume        - fixtures/commands/tailor-resume (stale-check / pipeline mechanics)
  tracking             - fixtures/commands/applied-update-status-prep-interview
                         (find_tracking_row.py lookup mechanics via /update-status, /prep-interview)
  import-applications  - fixtures/commands/import-applications (date-convention mechanics)
  all (default)        - every fixture above, run sequentially in that order

Gotchas:
  - Backs up tracking/applications.ndjson (and tracking/learned-preferences.md +
    .learned-preferences.hash, defensively) to a location outside the repo before the
    "tracking" fixture set touches them, and restores/deletes them exactly afterward —
    this happens even if a check fails or errors partway through.
  - Never appends fabricated rows to tracking/applications.ndjson permanently — the
    import-applications fixture is always canceled at its confirmation step.
  - Skips the optional /applied exercise inside the "tracking" fixture set by default
    (see that fixture's own expected.md) — its coverage is already in tests/test_base_name.py.
  - Should be run from main (or this branch) with template/ unmodified — every fixture
    is calibrated against Dana Whitfield's example data; on a personalized fork the
    scoring-sensitive checks will report as uncalibrated rather than pass/fail.

Examples:
  /test-fixtures
  /test-fixtures scoring
  /test-fixtures tracking
```

---

## Step 1 — Parse the Fixture Selector

Trim `$ARGUMENTS`. If it is empty or case-insensitively equals `all`, the run scope is **every fixture set**, in this fixed order: `scoring`, `tailor-resume`, `tracking`, `import-applications`. **This order is load-bearing, not arbitrary** — see Step 5's note on `fixture-01-strong-match`'s posting being reused by both `scoring` and `tailor-resume` at the identical destination filename. Never run those two concurrently or interleaved.

Otherwise, match the trimmed argument case-insensitively against exactly one of: `scoring`, `tailor-resume`, `tracking`, `import-applications`. If it matches, the run scope is that single fixture set.

If it matches none of those, print:
```
Unknown fixture set: "<argument as given>"

Usage:
  /test-fixtures [all|scoring|tailor-resume|tracking|import-applications]

Run `/test-fixtures help` for full usage.
```
and stop. Do not run any other step.

---

## Step 2 — Preflight: Confirm Calibration Baseline

Every fixture's `expected.md` states its ranges are only valid against **Dana Whitfield's example `template/` data**, unmodified. Check:

```bash
grep '^name:' template/contact-info.txt | sed 's/name: *//'
```

If this is not `Dana Whitfield`, warn prominently before continuing:
```
⚠ template/contact-info.txt's name is "<name found>", not "Dana Whitfield".
  Every fixture's expected.md range is calibrated against Dana Whitfield's example
  data — results from a personalized template/ will not be comparable to those
  ranges, and any "out of range" verdict below would say nothing about rubric drift.
```
Ask the user whether to proceed anyway (report scoring-sensitive checks as `N/A (uncalibrated template/)` rather than pass/fail if they say yes), or stop here. This does not block the `tracking`/`import-applications` mechanics checks the same way — row-matching and date-convention parsing aren't score-sensitive — but note the mismatch in the final report regardless of scope.

---

## Step 3 — Safety Backup (only if `tracking` is in scope)

Skip this step entirely if the run scope from Step 1 does not include `tracking`.

**Do this before touching any of the three files below, and do not proceed to Step 6 until it succeeds.**

```bash
python3 scripts/tracking_backup.py backup
```

This copies each of `tracking/applications.ndjson`, `tracking/learned-preferences.md`, and `tracking/.learned-preferences.hash` to a fixed location outside the repository tree, and reports per file whether it `"existed"` (backed up — must be restored byte-for-byte afterward) or was `"absent"` (nothing to restore — must be deleted afterward if the fixture creates it). Record this JSON output for use in Step 7.

If the command exits non-zero with `"error": "backup_dir_already_exists"`, a prior run's backup was never cleaned up — inspect `tracking_backup.py`'s reported backup path yourself before deciding whether it's safe to proceed, then stop here rather than guessing.

---

## Step 4 — Run: `scoring` (if in scope)

For each of `fixture-01-strong-match`, `fixture-02-stretch`, `fixture-03-ambiguous-middle`, in order, run this full sequence and **fully clean up before moving to the next fixture** — never batch cleanup at the end of this step:

1. Confirm `variable-input/job-descriptions/<slug>.md` does not already exist (`fixture-01-strong-match.md`, `fixture-02-stretch.md`, `fixture-03-ambiguous-middle.md` respectively — matching each directory's name). If it does, warn that this looks like a leftover from a prior interrupted run, ask whether it's safe to overwrite, and only proceed on confirmation.
2. Read `fixtures/scoring/<dir>/job-description.md` and write its content, unchanged, to `variable-input/job-descriptions/<slug>.md` via the Write tool.
3. Run `.claude/commands/tailor-resume.md`'s Steps 0-11 inline, right now, with `$ARGUMENTS` set to `<slug>.md`.
4. From the Step 11 report, extract the `job_match` total, all four sub-scores, and the interpretation label. Compare each against that fixture's expected ranges:

   | Fixture | Total | Skill Overlap | Experience Relevance | Seniority Match | Transferable Skills | Interpretation |
   |---|---|---|---|---|---|---|
   | fixture-01-strong-match | 72–88 | 24–30 | 17–25 | 14–19 | 10–16 | "Strong match" or "Exceptional match" |
   | fixture-02-stretch | 28–48 | 8–18 | 3–11 | 5–12 | 7–14 | "Reach application" or "Stretch role" |
   | fixture-03-ambiguous-middle | 50–72 | 14–24 | 8–20 | 11–18 | 10–16 | "Solid match with notable gaps" or "Strong match" |

   Mark each dimension and the total `IN RANGE` or `OUT OF RANGE`; mark the interpretation `MATCH` or `UNEXPECTED (<label>)`.
5. **Regardless of the comparison outcome or any error above**, clean up now: delete `variable-input/job-descriptions/<slug>.md` and every `output/dana-whitfield-<slug>*` file (markdown, PDF, cover letter markdown/PDF, `.manifest`). Do not delete `output/resume-style.css` (shared, not fixture-specific). Never run `/applied` against any of these.

Record all three fixtures' results for the final report.

---

## Step 5 — Run: `tailor-resume` (if in scope)

This fixture reuses `fixture-01-strong-match`'s posting under the identical destination filename the `scoring` set uses (`fixture-01-strong-match.md`) — per `fixtures/commands/README.md`, deliberately, to avoid duplicating fabricated content. **This is only safe because Step 4 (if it also ran) fully cleaned up before this step started.** Never run this step's copy while a `scoring`-set copy of the same file is still present.

1. Confirm `variable-input/job-descriptions/fixture-01-strong-match.md` doesn't already exist (same leftover-check as Step 4.1).
2. Read `fixtures/scoring/fixture-01-strong-match/job-description.md` and write its content, unchanged, to `variable-input/job-descriptions/fixture-01-strong-match.md` via the Write tool.
3. Run `.claude/commands/tailor-resume.md`'s Steps 0-11 inline, right now, with `$ARGUMENTS` set to `fixture-01-strong-match.md`. This is **run 1**. Record: the base name, whether `output/dana-whitfield-fixture-01-strong-match.manifest` was created with an `inputs` block, the job-match total/interpretation (72–88, "Strong match" or "Exceptional match" — same fixture as Step 4's), that the Reconciliation subsection reported no prior manifest, and that both PDFs were produced and passed ATS checks. Note the modification times of all four output files.
4. Immediately run `.claude/commands/tailor-resume.md`'s Steps 0-11 inline again, with the same `$ARGUMENTS`, **making no changes to any input file in between**. This is **run 2 — the actual point of this fixture**. Verify:
   - Step 0 short-circuited: the report is exactly the "Output is already up to date" block naming all four output files.
   - None of the four output files' modification times changed from what was recorded after run 1.
   - No `WebSearch` calls occurred and no PDF was regenerated.

   If the second run instead regenerates the full pipeline, or any output file's mtime changed, mark this **REGRESSION** — per this fixture's own `expected.md`, this is unambiguous, not LLM variance, and should be reported as a real bug regardless of what run 1's score was.
5. **Regardless of outcome**, clean up now: delete `variable-input/job-descriptions/fixture-01-strong-match.md` and every `output/dana-whitfield-fixture-01-strong-match*` file. Never run `/applied` against this fixture.

---

## Step 6 — Run: `tracking` (if in scope)

Step 3's backup must have completed successfully before this step begins. Everything in this step must be followed by Step 7 (Restore) **no matter what happens here** — a failure, an unexpected error, or an out-of-range/regression result partway through must never skip Step 7.

1. Confirm none of the three destination filenames already exist in `variable-input/job-descriptions/` (`Meridian-Cloud-Systems-Senior-Software-Engineer.md`, `Vantage-Point-Analytics-Senior-Software-Engineer.md`, `Kestrel-Data-Systems-Staff-Software-Engineer.md`); warn and confirm before overwriting if they do, same as Step 4.1.
2. Read each of the three JD stubs from `fixtures/commands/applied-update-status-prep-interview/` and write each, unchanged, to the matching filename under `variable-input/job-descriptions/` via the Write tool.
3. Read `fixtures/commands/applied-update-status-prep-interview/fixture-applications.ndjson` and write its content, unchanged, to `tracking/applications.ndjson` via the Write tool — this is the one destructive overwrite in this entire command. It is only safe because Step 3 already backed up whatever was there.
4. Run `.claude/commands/update-status.md`'s Steps 1-5 inline, right now, with `$ARGUMENTS` set to `Meridian-Cloud-Systems-Senior-Software-Engineer.md Screening interview`. Verify `match_count` was 1 (unambiguous) and the proposed `application_status` reads `"Applied - Screening interview (<today's date>)"`. Approve the confirmation on the fixture's behalf (this is fabricated data that Step 7 will fully restore regardless) and let the write complete. Mark `PASS`/`FAIL`.
5. Run `.claude/commands/update-status.md`'s Steps 1-5 inline again, with `$ARGUMENTS` set to `Vantage-Point-Analytics-Senior-Software-Engineer.md Screening interview`. Verify `match_count` was 2 and that **both** candidate rows (the May 10 "Not Selected" row and the July 15 reapply) were shown with their `date_applied`/`application_status`, and that a question was asked rather than a silent pick. **The check is fully satisfied by confirming this disambiguation behavior — deliberately do not pick one and do not complete a write here**, since there is no canonical right answer and forcing one adds an arbitrary mutation with no corresponding regression-test value. If it instead silently picked one, mark this **REGRESSION** per the fixture's own `expected.md` ("a real bug, not variance").
6. Run `.claude/commands/prep-interview.md`'s Steps 1-10 inline, with `$ARGUMENTS` set to `Kestrel-Data-Systems-Staff-Software-Engineer.md`. Verify `match_count` was 0 and that this was **not** treated as an error — it should have continued into general early-stage prep. If it stopped with an error instead, mark **REGRESSION**. Note the output file path written for cleanup.
7. Run `.claude/commands/prep-interview.md`'s Steps 1-10 inline, with `$ARGUMENTS` set to `Meridian-Cloud-Systems-Senior-Software-Engineer.md`. Verify the row was found and that Step 3's "no signal / predict from most recent stage" path was used (not a future-dated-stage path) — this is expected whether or not Step 6.4 above already ran (either resulting `application_status` value is fine per the fixture's `expected.md`). Note its output file path for cleanup.
8. **Step 7's optional `/applied` exercise is skipped by default** — do not run it. State this explicitly in the report: `"Optional /applied exercise: skipped by design — not required to validate find_tracking_row.py's branches; tracking/learned-preferences.md was never touched."`

---

## Step 7 — Restore (mandatory if Step 3 ran, regardless of Step 6's outcome)

Run this even if Step 6 failed, errored, or reported a regression. Do not skip any part of it.

```bash
python3 scripts/tracking_backup.py restore
```

Its JSON output reports, per file, `"restored"` (copied back from the backup), `"removed"` (deleted because it didn't exist before Step 3's backup), or `"already_absent"` (didn't exist before and still doesn't — nothing to do). Cross-check this against Step 3's recorded `"existed"`/`"absent"` result for each file: every `"existed"` file should now read `"restored"`, and every `"absent"` file should now read `"removed"` or `"already_absent"`. If any file's outcome doesn't match what Step 3 recorded, stop and report the mismatch explicitly rather than assuming it's fine.

Then delete the scratch files Step 6 created, regardless of outcome: the three copied JD stubs under `variable-input/job-descriptions/`, and the two `output/*-interview-prep.md` files noted in Steps 6.6/6.7.

Confirm the restore worked: re-read `tracking/applications.ndjson` (if it should now exist) and spot-check its content looks right, or confirm it's now absent (if it didn't exist before). Report this confirmation explicitly — don't just assume the script succeeded silently.

---

## Step 8 — Run: `import-applications` (if in scope)

No backup is needed for this fixture set specifically — its own `expected.md` requires canceling before any write reaches `tracking/applications.ndjson`. (If `tracking` also ran in this invocation, Step 7 has already completed by the time this step runs, per the fixed order from Step 1.)

1. Run `.claude/commands/import-applications.md`'s Steps 1-10 inline, right now, with `$ARGUMENTS` set to `fixtures/commands/import-applications/fixture-legacy-tracker.csv`.
2. At Step 4 (field mapping confirmation), compare the inferred mapping against: `Date Applied`→`date_applied`, `Company`→`company`, `Position`→`position_title`, `Status`→`application_status`, `Notes`→`notes`. Mark `PASS`/`FAIL`, then approve so the run can continue to the actual check.
3. At Step 7 (import preview), compare the four normalized dates against: `03/04/2026`→`2026-04-03`, `22/06/2026`→`2026-06-22`, `05/02/2026`→`2026-02-05`, `11/07/2026`→`2026-07-11`, and confirm no per-row ambiguity question was asked (the file-wide convention should have resolved upfront from `22/06/2026`). Mark `PASS`/`FAIL`.
4. **Cancel at this preview — do not confirm.** Nothing is appended to `tracking/applications.ndjson`. This is mandatory per the fixture's own `expected.md`; treat a successful cancel as part of the passing criteria, not just an afterthought.
5. Supplementary check (the genuinely-ambiguous branch): read `fixtures/commands/import-applications/fixture-legacy-tracker.csv`, remove the `22/06/2026` row, and write the remaining rows via the Write tool to a fixed scratch path, `output/test-fixtures-ambiguous-scratch.csv`. Run `.claude/commands/import-applications.md`'s Steps 1-10 inline again against that scratch path. Verify `convention: "ambiguous"` is detected and Step 5 asks once, upfront, which convention to use, rather than guessing per row. Cancel here too. Delete `output/test-fixtures-ambiguous-scratch.csv` afterward regardless of outcome.

---

## Step 9 — Consolidated Report

Report every fixture that ran in this invocation:

```
Test Fixtures — <all|scoring|tailor-resume|tracking|import-applications> — <today's date>
[If Step 2 flagged a non-Dana-Whitfield template/: "⚠ Run against a non-default template/ — scoring ranges below are not calibrated for this data."]

## Scoring Fixtures
  fixture-01-strong-match    : <PASS/FAIL> — total <n>/100 (expected 72-88), "<label>"
    Skill Overlap        : <n>/30 (expected 24-30) <✓/⚠>
    Experience Relevance : <n>/30 (expected 17-25) <✓/⚠>
    Seniority Match      : <n>/20 (expected 14-19) <✓/⚠>
    Transferable Skills  : <n>/20 (expected 10-16) <✓/⚠>
  fixture-02-stretch          : <PASS/FAIL> — total <n>/100 (expected 28-48), "<label>"
  fixture-03-ambiguous-middle : <PASS/FAIL> — total <n>/100 (expected 50-72), "<label>"
  [If any single fixture is out of range: "Note: a single out-of-range result is often normal classification variance, not proof of a broken rubric — the same fixture landing outside range on two separate checks is the real signal (see fixtures/scoring/README.md)."]

## /tailor-resume Pipeline Mechanics
  Run 1: job-match <n>/100 "<label>" (expected 72-88) <✓/⚠>; manifest created; resume <n>pg / cover letter <n>pg
  Run 2: <"short-circuited correctly, no output files changed" / "REGRESSION — regenerated instead of short-circuiting">
  Result: <PASS/FAIL/REGRESSION>

## /applied /update-status /prep-interview Lookup Mechanics
  Step 4 (Meridian, match_count=1)      : <PASS/FAIL>
  Step 5 (Vantage Point, match_count=2) : <PASS/FAIL/REGRESSION> — asked rather than guessed, no write performed
  Step 6 (Kestrel, match_count=0)       : <PASS/FAIL/REGRESSION> — continued with general prep, not an error
  Step 7 (Meridian, row found)          : <PASS/FAIL>
  Optional /applied exercise            : skipped by design
  Tracking-file safety:
    tracking/applications.ndjson        : <"backed up, restored" / "backed up, did not exist before -- removed after">
    tracking/learned-preferences.md     : untouched (optional step skipped)
    tracking/.learned-preferences.hash  : untouched (optional step skipped)
  Scratch files removed: <list>

## /import-applications Date-Convention Mechanics
  Field mapping    : <PASS/FAIL>
  Normalized dates : <PASS/FAIL>
  Canceled at Step 7 preview (no rows appended) : <confirmed/NOT CONFIRMED -- see below>
  Ambiguous-file supplementary check : <PASS/FAIL>

## Overall
  <N> fixture checks run, <P> passed, <F> failed, <R> regressions.
  All scratch files confirmed removed: variable-input/job-descriptions/*, output/dana-whitfield-fixture-*, output/*-interview-prep.md, output/test-fixtures-ambiguous-scratch.csv.

git status:
<verbatim output of `git status`>
```

Always run `git status` for this final section, regardless of scope or outcome, so the user has direct confirmation that nothing fixture-related is left staged, modified, or untracked-and-forgotten.
