# Expected — /applied, /update-status, /prep-interview lookup mechanics

**Fixture data:** `fixture-applications.ndjson` (3 rows, all fictional companies) plus three matching fabricated job-description stubs in this directory. Calibrated against **the example applicant** (Dana Whitfield, `main`'s `template/`).

Verified directly against `scripts/find_tracking_row.py` while authoring this fixture:

| Target company | `match_count` |
|---|---|
| Meridian Cloud Systems | 1 |
| Vantage Point Analytics | 2 (the intentional ambiguous reapply pair) |
| Kestrel Data Systems | 0 (deliberately absent from the fixture — never applied to) |

## Procedure

**Back up first, outside the repo tree** (see this directory's parent README's safety note): `tracking/applications.ndjson` if it exists, and `tracking/learned-preferences.md` + `tracking/.learned-preferences.hash` if you intend to run the optional `/applied` step below.

1. Copy the three JD stubs into `variable-input/job-descriptions/`: `Meridian-Cloud-Systems-Senior-Software-Engineer.md`, `Vantage-Point-Analytics-Senior-Software-Engineer.md`, `Kestrel-Data-Systems-Staff-Software-Engineer.md`.
2. Copy `fixture-applications.ndjson` to `tracking/applications.ndjson`.
3. Run `/update-status Meridian-Cloud-Systems-Senior-Software-Engineer.md "Screening interview"`.
4. Run `/update-status Vantage-Point-Analytics-Senior-Software-Engineer.md "Screening interview"`.
5. Run `/prep-interview Kestrel-Data-Systems-Staff-Software-Engineer.md`.
6. Run `/prep-interview Meridian-Cloud-Systems-Senior-Software-Engineer.md`.
7. **Optional, only if you backed up `tracking/learned-preferences.md` in step 0:** run `/applied` against a fourth job description of your choosing (not one of the three above) to exercise `base_name.py` + the append + the `hash_sidecar.py`-gated learned-preferences refresh live. Skip this step entirely if you'd rather not touch `tracking/learned-preferences.md`, even temporarily — `base_name.py`'s row-creation shape is already fully covered by `tests/test_base_name.py`.
8. Restore all backed-up files (or delete them if they didn't exist before step 0) and confirm `git status` is clean.

## Expected

- **Step 3 (Meridian, `match_count: 1`):** locates the single row unambiguously, builds a proposed `application_status` of `"Applied - Screening interview (<today's date>)"`, shows it for confirmation before writing.
- **Step 4 (Vantage Point, `match_count: 2`):** does **not** guess — shows both candidate rows (the May 10 "Not Selected" one and the July 15 reapply) with their `date_applied`/`application_status`, and asks which one to update. This is the exact "reapplying after a rejection produces two legitimate rows" scenario `update-status.md` Step 2 describes.
- **Step 5 (Kestrel, `match_count: 0`):** unlike `/update-status`, this is explicitly **not an error** for `/prep-interview` — it should note no tracking row was found and continue with general early-stage prep (company/role research, narrative framing) rather than stage-specific coaching.
- **Step 6 (Meridian, row found):** `application_status` is just `"Applied"` (or `"Applied - Screening interview (...)"` if step 3 already ran) with no future-dated stage — falls to `/prep-interview` Step 3's "no signal / predict from most recent stage" path, not the future-dated-stage path.

## Interpreting a miss

If step 4 silently picks one of the two Vantage Point rows instead of asking, or if step 5 stops with an error instead of continuing, that's `find_tracking_row.py`'s multi-signal matching or one of its callers' branching logic regressing — treat it as a real bug, not variance (there's no LLM classification judgment in the matching itself, only in what to do with the result).
