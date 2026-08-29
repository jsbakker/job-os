# Expected — /import-applications date-convention mechanics

**Fixture data:** `fixture-legacy-tracker.csv` — 4 rows, all fictional companies, standard header row (`Date Applied,Company,Position,Status,Notes`). One row's date (`22/06/2026`, day component 22 > 12) unambiguously disambiguates the whole file as `DD/MM/YYYY`; the other three rows are individually ambiguous (both components ≤ 12) and only resolve correctly once the file-wide convention is known.

Verified directly against `scripts/detect_date_convention.py` while authoring this fixture:

```json
{
  "convention": "DD/MM/YYYY",
  "disambiguating_date": "22/06/2026",
  "normalized": {
    "03/04/2026": "2026-04-03",
    "22/06/2026": "2026-06-22",
    "05/02/2026": "2026-02-05",
    "11/07/2026": "2026-07-11"
  }
}
```

## Procedure

1. Run `/import-applications fixtures/commands/import-applications/fixture-legacy-tracker.csv` (an arbitrary path outside `variable-input/job-descriptions/` is fine — `/import-applications` accepts a source file from anywhere).
2. Confirm the inferred field mapping at Step 4 (`Date Applied` → `date_applied`, `Company` → `company`, `Position` → `position_title`, `Status` → `application_status`, `Notes` → `notes`).
3. At the import preview (Step 7), check the normalized dates match the table above exactly — no per-row ambiguity question should be asked, since `22/06/2026` resolves the whole file upfront.
4. **Cancel at the Step 7 preview rather than confirming** — this fixture is for validating the mapping/normalization mechanics, not for actually appending fictional Dana Whitfield application history to your real tracking log.

## A second run worth doing: force the genuinely ambiguous case

Copy `fixture-legacy-tracker.csv` to a scratch file and delete the `22/06/2026` row (leaving only individually-ambiguous dates), then re-run against that scratch copy. Expect `convention: "ambiguous"` this time, and `/import-applications` Step 5 asking you once, upfront, which convention the file uses — rather than silently guessing per row. Delete the scratch file afterward.

## Interpreting a miss

If the normalized dates come out wrong (e.g. `03/04/2026` interpreted as `2026-03-04` instead of `2026-04-03`), or if the ambiguous-file case doesn't trigger the upfront question, that's `detect_date_convention.py`'s disambiguation logic regressing — a real bug, not LLM variance, since date-string parsing has no judgment involved. If the *field mapping* at Step 4 comes out wrong (e.g. `Notes` mapped to `application_status`), that's a `/import-applications` prose issue, unrelated to this script.
