# Expected — /tailor-resume pipeline mechanics

**Source posting:** reuses `fixtures/scoring/fixture-01-strong-match/job-description.md` (the fabricated "Northgate Fleet Systems" posting) rather than duplicating fabricated content. This fixture isn't about scoring accuracy — `fixtures/scoring/` already covers that — it's about whether the refactored *pipeline mechanics* (base-name derivation, manifest structure, and especially the stale-check short-circuit) work correctly end to end through the real command.

## Procedure

1. Copy the posting in: `cp fixtures/scoring/fixture-01-strong-match/job-description.md variable-input/job-descriptions/fixture-01-strong-match.md`
2. Run `/tailor-resume fixture-01-strong-match.md`.
3. Immediately run `/tailor-resume fixture-01-strong-match.md` again, with no changes to any input file in between.
4. Clean up: delete `variable-input/job-descriptions/fixture-01-strong-match.md` and every `output/dana-whitfield-fixture-01-strong-match*` file. Do not run `/applied` against this fixture.

## Expected — first run

- **Base name:** `dana-whitfield-fixture-01-strong-match`, derived from `template/contact-info.txt`'s `name: Dana Whitfield` and the copied filename's stem — this is `scripts/base_name.py applicant-job`'s job, exercised for real here rather than in isolation.
- **Manifest:** `output/dana-whitfield-fixture-01-strong-match.manifest` is created, with an `"inputs"` block whose keys match `scripts/manifest_check.py hash`'s fixed file list (verifiable by running that script directly against the same job-description filename and diffing key sets).
- **Job match:** total in the 72–88 range, interpretation "Strong match" or "Exceptional match" — per `fixtures/scoring/fixture-01-strong-match/expected.md`'s calibration. This run's Reconciliation subsection should report no prior manifest found (first run) and skip that subsection entirely.
- **Output:** a 2-page resume PDF and a 1-page cover letter PDF, both passing ATS checks.

## Expected — second run (the actual point of this fixture)

Since nothing changed between the two runs, Step 0's stale-check should short-circuit entirely:

```
Output is already up to date — no inputs have changed.
  Resume Markdown  : output/dana-whitfield-fixture-01-strong-match.md
  Resume PDF       : output/dana-whitfield-fixture-01-strong-match.pdf
  Cover Letter MD  : output/dana-whitfield-fixture-01-strong-match-cover-letter.md
  Cover Letter PDF : output/dana-whitfield-fixture-01-strong-match-cover-letter.pdf
```

No re-read of `template/`, no `WebSearch` calls, no regenerated PDF — the second run should be fast and should not touch any output file's modification time. This is `scripts/manifest_check.py compare` reporting `all_match: true` and both cover-letter files existing, driving Step 0's skip-to-Step-11 branch. If the second run instead re-runs the full pipeline, that's the actual regression this fixture exists to catch.

## Interpreting a miss

If the first run's score falls outside 72–88, that's the same "not necessarily broken, but watch for it happening twice" signal `fixtures/scoring/README.md` describes — it's LLM classification variance in Step 2b, not this fixture's concern. If the **second run regenerates instead of short-circuiting**, that's unambiguous: something in the stale-check chain (`base_name.py`, `manifest_check.py`, or Step 0's own wiring in `tailor-resume.md`) has broken and should be treated as a real bug, not variance.
