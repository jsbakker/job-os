# Scoring Fixtures

A manual, periodic calibration check for `/tailor-resume` Step 2b/2c's job-match rubric — not an automated test suite (this project has no CI to schedule one against), but a documented procedure so rubric drift is something you'd actually notice.

## What's here

Three fully fabricated job postings (fictional companies, fictional products — not copied from any real posting) as Markdown files, each calibrated against **the example applicant** (Dana Whitfield, the fictional profile shipped in `template/` on `main`), with an `expected.md` stating the score range a correct itemized classification should land in:

- `fixture-01-strong-match/` — a role with strong skill/domain/seniority overlap against Dana Whitfield's profile, expected to land in the "Strong match" band (72–88/100).
- `fixture-02-stretch/` — a role with a real domain and seniority gap (regulated finance, Staff-level), expected to sit right at the "Reach application" / "Stretch role" boundary (28–48/100).
- `fixture-03-ambiguous-middle/` — a role with partial stack overlap and two hard gaps, expected to sit mid-"Solid match" band, reaching toward "Strong match" (50–72/100) — the most useful fixture for catching rubric-wording drift, since that's exactly where banding judgment is hardest.

Each `expected.md` states *ranges*, not exact points — the itemized classification is still a fresh LLM read every time (only the arithmetic on top of it is deterministic, via `scripts/score_job_match.py`), so some run-to-run variance within a range is normal and not a problem.

**Why fabricated postings, calibrated against the example applicant:** the original version of this fixture set copied real job postings (downloaded PDFs from real companies' LinkedIn listings) and was calibrated against the repo owner's own real resume data. Neither is safe to keep in a shared repo — the postings are third-party content, and calibrating against personal data makes the fixtures meaningless (or misleading) to anyone else who forks this project. Every posting here is originally authored for this calibration set, and every `expected.md` range is derived from Dana Whitfield's fictional `template/` data, which ships with the project on `main`.

## How to run the check

1. Copy a fixture's `job-description.md` into `variable-input/job-descriptions/` (e.g. as `fixture-01-strong-match.md` — don't overwrite anything already there).
2. Run `/tailor-resume fixture-01-strong-match.md`.
3. Compare the reported `job_match` total, sub-scores, and interpretation label against that fixture's `expected.md`.
4. Delete the scratch job-description copy and its `output/fixture-*` files afterward — they aren't real applications and shouldn't clutter `tracking/applications.ndjson` (don't run `/applied` against them).

**Run this from `main`, with `template/` unmodified** (still holding Dana Whitfield's example data), not from a personal branch or fork with your own resume swapped into `template/`. The `expected.md` ranges are calibrated against Dana's specific skills and experience — scoring these postings against different `template/` data will produce different, not-comparable numbers, and an out-of-range result would say nothing about rubric drift.

## When to run it

- After editing Step 2b or Step 2c's wording in `.claude/commands/tailor-resume.md`.
- After editing `scripts/score_job_match.py`'s arithmetic.
- Periodically (every few months) as a sanity check even without an edit, since prompt behavior can drift across model versions.

## Interpreting a miss

A single out-of-range result on one fixture is often normal LLM classification variance (a defensible "adjacent" vs. "direct" call on one item can shift a sub-score by a few points) — don't treat one miss as proof something broke. **The same fixture landing outside its range on two separate checks** is the actual signal that rubric wording needs revisiting, either because it's become ambiguous or because a Step 2b edit changed its effective meaning.

## Hand-edit protection

None currently — `expected.md` files are meant to be edited deliberately when the rubric itself changes (update the range to match the new intended behavior), so there's no hash-sidecar guard here unlike `tracking/learned-preferences.md`. If these fixtures start being edited accidentally, add a `.fixtures.hash` sidecar following that same pattern.
