---
name: import-applications
description: Import a pre-existing external job-tracking file into tracking/applications.ndjson
---

Import a pre-existing job-tracking file into the tracking log: $ARGUMENTS

*(In Claude Code, `$ARGUMENTS` is what follows `/import-applications` in the slash palette. In agents without slash syntax, treat this as the file path the user named in their request.)*

You are bringing historical application data — from before this repo was adopted — into `tracking/applications.ndjson`. The source file can be anything: a spreadsheet, a Word document, an Apple Numbers file, a CSV, plain text, or Markdown, in any layout. Examine its actual structure yourself; do not assume a fixed column order or header set. Every row this command writes is genuinely new — it never edits or merges into an existing row (that remains `/update-status`'s job), and it never truncates or rewrites the file's existing content.

---

## Help Check

(This exact-match escape hatch is for Claude Code's `/import-applications help` slash syntax; other agents should just answer help questions about this skill conversationally using the Usage block below.)

If `$ARGUMENTS`, trimmed of whitespace, equals `help` (case-insensitive) — and only in that exact case, not as part of a real file path — print the block below and stop. Do not run any other step.

```
/import-applications — Imports a pre-existing external job-tracking file (Word, Excel, Apple Numbers, CSV, plain text, or Markdown) into tracking/applications.ndjson, mapping its columns/entries onto the 14-field schema by inspection rather than fixed per-format rules.

Usage:
  /import-applications <path-to-tracking-file>

What it does:
  - Detects the file's format (by extension, or by content-sniffing if the extension is missing or unreliable) and extracts its raw rows/entries
  - Infers which parts of each entry correspond to date_applied, company, position_title, job_id, application_status, apply_method, job_posting_url, recommended_ask, and notes — the fields a historical tracker plausibly has
  - Shows you the inferred column/field mapping and waits for confirmation before processing every row
  - Checks every parsed entry against tracking/applications.ndjson (by job_id, or by company+position_title) and skips anything that looks like an existing duplicate, rather than merging or overwriting it
  - Shows a full preview (counts, a sample of mapped rows, anything low-confidence or skipped) and waits for a second confirmation before appending anything
  - Appends only new rows to tracking/applications.ndjson (never truncates or rewrites existing rows) and refreshes tracking/learned-preferences.md afterward

Gotchas:
  - The other 6 fields (salary_range, glassdoor_rating, match_score, resume_file, cover_letter_file, source) are set to null unless your source file genuinely has equivalent data — nothing is fabricated to fill them in (source defaults to "manual" instead, since that provenance fact is always knowable)
  - A genuinely ambiguous numeric date convention (e.g. every date in the file has both components ≤12, so 01/02/2026 could be Jan 2 or Feb 1) triggers one upfront question about the file's convention, rather than a silent per-row guess
  - Legacy binary .xls or .doc files may need you to re-save as .xlsx/.docx/.csv first if extraction can't cleanly find row/column boundaries
  - Never merges into or overwrites an existing row — a match against an existing application is skipped and reported, not updated (that's /update-status's job)

Example:
  /import-applications ~/Desktop/JobSearchTracker.xlsx
```

---

## Step 1 — Resolve the Source File

If `$ARGUMENTS`, trimmed of whitespace, is empty, ask the user directly for the path to the file they want to import — it can be anywhere on disk, unlike job description files, which must live in `variable-input/job-descriptions/`. Otherwise treat the entirety of `$ARGUMENTS` as the file path; no flags are supported.

Confirm the file exists and is readable before doing anything else. If it doesn't, tell the user and stop — don't guess at a nearby filename, and don't touch `tracking/applications.ndjson`.

---

## Step 2 — Detect Format and Extract Raw Data

### Step 2a — Detect Format

Use the extension first: `.csv`, `.tsv`, `.txt`, `.md`/`.markdown`, `.pdf` → plain/structured text path (Step 2b). `.numbers` → Apple Numbers path (Step 2c). `.docx`, `.doc`, `.rtf` → Word/rich-text path (Step 2d). `.xlsx`, `.xlsm` → modern Excel path (Step 2e). `.xls` → legacy Excel path (Step 2e, xlrd branch).

If the extension is missing, unrecognized, or looks unreliable (e.g. a `.txt` file that's actually a renamed spreadsheet), sniff the real type first:
```bash
file "<path>"
```
Route based on what it reports (e.g. "Microsoft Excel 2007+" → the xlsx path, a zip archive with a `.numbers`-shaped internal layout → the Numbers path, "ASCII text"/"UTF-8 Unicode text" → the plain-text path).

### Step 2b — Plain/Structured Text (csv, tsv, txt, md, pdf)

Read the file directly — the same pattern `/tailor-resume` already uses for PDFs and text job descriptions, with no shell-out needed. For CSV/TSV, don't assume a comma delimiter: read a few lines first and infer the actual delimiter from what's consistently present.

### Step 2c — Apple Numbers (.numbers)

Bootstrap the isolated tool venv if it doesn't exist yet, and install only `numbers-parser` if it isn't already present:
```bash
test -d .venv-tools || python3 -m venv .venv-tools
./.venv-tools/bin/python -c "import numbers_parser" 2>/dev/null || ./.venv-tools/bin/pip install numbers-parser
```
Then dump every sheet/table's raw rows to stdout. This is a raw data-access step only — it does not decide what any column means, that happens in Step 3:
```bash
./.venv-tools/bin/python -c "
from numbers_parser import Document
doc = Document('<path>')
for si, sheet in enumerate(doc.sheets):
    for ti, table in enumerate(sheet.tables):
        print(f'--- Sheet {si} ({sheet.name}) / Table {ti} ({table.name}) ---')
        for row in table.rows(values_only=True):
            print(row)
"
```

### Step 2d — Word / Rich Text (.docx, .doc, .rtf)

Default to `textutil` (built into macOS, no install needed) — it's sufficient unless the source genuinely uses real Word table structure that collapses when flattened to plain text:
```bash
textutil -convert txt -stdout "<path>"
```
Only escalate — and only for `.docx` (`python-docx` cannot open the legacy binary `.doc` format at all) — if that flattened output makes column/field boundaries genuinely ambiguous, e.g. tab-separated values that ran together:
```bash
./.venv-tools/bin/python -c "import docx" 2>/dev/null || ./.venv-tools/bin/pip install python-docx
./.venv-tools/bin/python -c "
import docx
d = docx.Document('<path>')
for ti, table in enumerate(d.tables):
    print(f'--- Table {ti} ---')
    for row in table.rows:
        print([c.text for c in row.cells])
print('--- Paragraphs ---')
for p in d.paragraphs:
    if p.text.strip():
        print(p.text)
"
```
If the file is a legacy `.doc` and the `textutil` output is still ambiguous, don't attempt `python-docx` — tell the user and ask them to re-save it as `.docx` or `.csv` first.

### Step 2e — Excel (.xlsx, .xlsm, .xls)

For `.xlsx`/`.xlsm`:
```bash
test -d .venv-tools || python3 -m venv .venv-tools
./.venv-tools/bin/python -c "import openpyxl" 2>/dev/null || ./.venv-tools/bin/pip install openpyxl
./.venv-tools/bin/python -c "
import openpyxl
wb = openpyxl.load_workbook('<path>', data_only=True)
for ws in wb.worksheets:
    print(f'--- Sheet: {ws.title} ---')
    for row in ws.iter_rows(values_only=True):
        print(row)
"
```
For legacy `.xls` — `openpyxl` cannot open this format at all, it will raise on load:
```bash
./.venv-tools/bin/python -c "import xlrd" 2>/dev/null || ./.venv-tools/bin/pip install xlrd
./.venv-tools/bin/python -c "
import xlrd
wb = xlrd.open_workbook('<path>')
for sheet in wb.sheets():
    print(f'--- Sheet: {sheet.name} ---')
    for r in range(sheet.nrows):
        print(sheet.row_values(r))
"
```

If any of these invocations fails with `ModuleNotFoundError` for a package not anticipated above, install that specific package into `.venv-tools` the same way and retry once before giving up and reporting the error to the user. Never abandon extraction on the first missing-import error without attempting the install.

---

## Step 3 — Infer Entry Structure and Field Mapping

Look at the raw data extracted in Step 2 and determine its shape:

- **Header + data rows**: the first row's cells read as short labels (e.g. "Date", "Company", "Status") rather than data values. Use those labels as hints, but map by meaning, not exact string match — e.g. "Date"/"Date Applied"/"Applied On" all mean `date_applied`; "Co."/"Employer"/"Organization" mean `company`; "Role"/"Title"/"Position" mean `position_title`; "Req"/"Req #"/"Job ID"/"Reference" mean `job_id`; "Status"/"Stage"/"Outcome" mean `application_status`; "How"/"Method"/"Channel"/"Applied Via" mean `apply_method`; "URL"/"Link"/"Posting" mean `job_posting_url`; "Ask"/"Requested Salary"/"Desired Comp" mean `recommended_ask`; "Notes"/"Comments"/"Remarks"/"Recruiter"/"Contact" mean `notes`.
- **Data rows with no header**: infer field identity from content shape instead (a column of dates → `date_applied`; a column of URLs → `job_posting_url`; a column of short, non-repeating proper-noun-looking text → `company`, etc.).
- **Unstructured or semi-structured free text** (a narrative log, e.g. "Jan 5 — applied to Acme Corp for Staff Engineer via LinkedIn, req #1234"): treat each identifiable entry (paragraph, bullet, or dated line) as one record and extract fields via reading comprehension, using the same field meanings above.

For every one of the 9 plausibly-present fields (`date_applied`, `company`, `position_title`, `job_id`, `application_status`, `apply_method`, `job_posting_url`, `recommended_ask`, `notes`), a field genuinely absent on a *specific entry* becomes `null` for that entry — never fabricated, and never copied forward from a neighboring row. Only skip an entry entirely if every field on it is blank.

If the source has columns or content that don't correspond to any of the 9 fields above, don't silently discard them — flag them in Step 4 and ask whether to fold that text into `notes` (or `application_status`, if it's clearly status-related), or leave it out of the import.

---

## Step 4 — Confirm the Field Mapping

Before processing a single row in bulk, show the user the mapping inferred in Step 3, plus 2-3 sample entries run through it:

```
Inferred mapping for <source file>:

  Source column "Date"          -> date_applied
  Source column "Company Name"  -> company
  Source column "Job Title"     -> position_title
  Source column "Ref #"         -> job_id
  Source column "Stage"         -> application_status
  Source column "Notes"         -> notes

Sample (first 2 entries mapped):
  1. {"date_applied": "2024-03-11", "company": "Acme Corp", "position_title": "Staff Engineer", "job_id": "1234", "application_status": "Applied", "notes": "Referral from a friend", ...}
  2. {"date_applied": "2024-03-15", "company": "Globex", "position_title": "Senior SWE", "job_id": null, "application_status": "Applied - Rejected", "notes": null, ...}

Does this mapping look right? (yes / fix a specific field / cancel)
```

Do not proceed to Step 5 until the user confirms the mapping, or corrects it and re-confirms.

---

## Step 5 — Extract and Normalize All Rows

Apply the confirmed mapping to every entry in the source:

- **Dates**: normalize to `YYYY-MM-DD`. Collect every raw numeric-format date string found in the source (e.g. `01/02/2026`) into `{"dates": [...]}` and run `python3 scripts/detect_date_convention.py --input <file>` (or pipe on stdin). If `convention` is not `"ambiguous"`, use its `normalized` mapping verbatim for every date. If `convention` is `"ambiguous"` (no date in the file ever disambiguates it), ask the user once, upfront, which convention the file uses, rather than guessing per-row.
- **`job_id`**: coerce to a string. If it arrived as a numeric cell rendered as a float (e.g. `1234.0`), strip the trailing `.0` — the same normalization the old migration script applied; this is data hygiene, not a schema guess.
- **`notes`**: plain string, same handling as any other free-text field — trim whitespace, empty string becomes `null`. This is where "Notes"/"Comments"/"Remarks"/etc. source columns land now, not folded into `application_status`.
- **Blank entries**: skip entirely (don't append a row) only if every mapped field on that entry is empty. An entry with some fields present and others empty keeps the present fields and sets the rest to `null`.
- **The 5 fields with no plausible source equivalent** — `salary_range`, `glassdoor_rating`, `match_score`, `resume_file`, `cover_letter_file` — default to `null` for every imported row unless the source genuinely contains that specific data (e.g. an actual "Glassdoor Rating" column counts). Never fabricate a value for any of them.
- **`source`**: set to `"manual"` for every imported row, unless the user tells you a specific entry actually came through `/find-job-descriptions` (in which case it would already be logged and Step 6 would catch it as a duplicate). This isn't a guess — it's a knowable fact: history predating this repo's adoption was, by definition, tracked manually.

---

## Step 6 — Deduplicate Against Existing Tracking Log

For every entry parsed in Step 5, look it up against the existing log:

```bash
python3 scripts/find_tracking_row.py lookup --file tracking/applications.ndjson \
  --job-id "<job_id, if non-null>" --company "<company>" --position-title "<position_title>"
```

(This is the same script `/update-status` Step 2 uses, applied here with only the `job_id`/`company`/`position_title` signals — a parsed import entry has no `resume_file`/`cover_letter_file` yet, so `--base-name` never applies. Note `/applied` Step 1's own preflight duplicate check is a lighter, standalone `company`+`position_title` check, not this script — this step and `/update-status` Step 2 are the two callers using the full multi-signal lookup.)

Any `match_count` > 0 marks the parsed entry as a **likely duplicate**: skip it (don't append, and never merge into or overwrite the existing row's `application_status` — that's `/update-status`'s job) and record which existing row it matched, for the report.

Entries that share the same `company`+`position_title` as each other *within the source file itself* are not automatically duplicates — a genuine reapply produces two legitimate rows. Only flag those as suspicious if their dates are also suspiciously close or identical, and ask the user to confirm rather than silently importing or silently collapsing them.

Everything left over after this step is a new row headed for Step 7.

---

## Step 7 — Preview and Confirm the Import

Before writing anything, show the user:

```
Import preview for <source file>:

  Entries found in source      : <n>
  Skipped (fully blank)        : <n>
  Skipped (existing duplicate) : <n>
  New rows to import           : <n>

Sample of new rows (up to 5):
  1. <date_applied> — <company> — <position_title> — status: <application_status>
  2. ...

Flagged as low-confidence (review before proceeding):
  - <entry description>: <what's uncertain, e.g. "date '03/04/2025' — file-wide convention inferred as MM/DD/YYYY from other rows">
  [or "none"]

Skipped as likely duplicates:
  - <source entry> matches existing row <date_applied>/<company>/<position_title>
  [or "none"]

Proceed with appending the <n> new rows to tracking/applications.ndjson? (yes / exclude specific rows / cancel)
```

Do not proceed to Step 8 until the user confirms.

---

## Step 8 — Append to tracking/applications.ndjson

This is the step that fixes the historical migration script's worst bug: it must never truncate or overwrite the file.

1. If `tracking/applications.ndjson` doesn't exist yet, its new content is simply the newly-imported lines.
2. If it does exist, read it in full first, and construct the new file content as **the existing content, byte-for-byte, followed by the newly-imported lines** — never construct the new content from only the imported rows. This is the same read-then-write-whole-file pattern `/update-status` Step 4 uses; the difference here is every existing line is preserved unchanged and only new lines are added at the end.
3. Write the result to the file.

---

## Step 9 — Refresh Learned Preferences

A bulk import is a much bigger preference-signal event than a single `/applied` run, so refresh `tracking/learned-preferences.md` the same way `/applied` Step 8 does:

1. Run `python3 scripts/hash_sidecar.py check --file tracking/learned-preferences.md --sidecar tracking/.learned-preferences.hash`. If `hand_edited` is `true`, ask before overwriting.
2. Re-run `/learn-preferences` Steps 1-3 over the full log, including every row just imported, preserving existing wording and conclusions wherever the new rows don't materially change them.
3. Write the refreshed file, then run `python3 scripts/hash_sidecar.py write --file tracking/learned-preferences.md --sidecar tracking/.learned-preferences.hash`.
4. If nothing material changed, report that plainly instead of manufacturing a change.

---

## Step 10 — Report

```
Import complete.

  Source file                  : <path>
  Format detected               : <csv|xlsx|numbers|docx|...>
  Entries found in source       : <n>
  Skipped (fully blank)         : <n>
  Skipped (existing duplicate)  : <n>
  Rows imported                 : <n>
  Tracked in                    : tracking/applications.ndjson (<n> row(s) appended)
  Preferences                   : <"refreshed — <one-line summary>" or "no material change">

[if any imported rows were flagged low-confidence: "Review these for accuracy: <list>"]
[if the user excluded specific rows in Step 7: "Excluded at your request: <list>"]
```
