---
name: update-status
description: Append a new stage to an existing job application's status in the tracking log
---

Append a new status stage to the tracking row for the following job: $ARGUMENTS

*(In Claude Code, `$ARGUMENTS` is what follows `/update-status` in the slash palette. In agents without slash syntax, treat this as the job description filename — and new status text — the user named in their request.)*

The **first whitespace-separated token** of the argument above is the job description filename (resolved against `variable-input/job-descriptions/`, same convention as `/tailor-resume` and `/applied`). **Everything after it** is the new status text to append (e.g. "Screening interview", "Not Selected", "Offer Received").

You are updating one field on an existing row in `tracking/applications.ndjson`. Rows are otherwise append-only (that's what `/applied` enforces) — this command is a deliberate, narrow exception scoped to exactly one field: `application_status`. Never create a new row here, and never touch any other field on the matched row.

---

## Help Check

(This exact-match escape hatch is for Claude Code's `/update-status help` slash syntax; other agents should just answer help questions about this skill conversationally using the Usage block below.)

Check this **before** applying the first-token/rest-of-string split described above. If `$ARGUMENTS`, trimmed of whitespace, equals `help` (case-insensitive) **in its entirety** — not just its first token — print the block below and stop. Do not run any other step.

```
/update-status — Appends a new stage to an existing application's status in tracking/applications.ndjson (e.g. turning "Applied" into "Applied\nScreening interview (Aug 12)", rendered by job-tracker.html as two bullets), after showing you the exact resulting text and getting confirmation.

Usage:
  /update-status <job-description-file> <new-status-text>

What it does:
  - Locates the matching row in tracking/applications.ndjson using the job-description file (matches on resume/cover-letter filename, req ID, or company+title — asks you to pick if more than one row matches, e.g. after a reapply)
  - Builds the new application_status string, adding today's date to the new stage if you didn't already include one
  - For "Not Selected" or "Rejected" (a dead end with no future date to track), auto-dates and writes without asking; for every other stage, shows you the exact string and waits for confirmation before writing anything
  - Updates only that one field on that one row

Gotchas:
  - Never writes without confirmation first, except for a dated "Not Selected"/"Rejected" stage — those write immediately since there's no date to get wrong on a dead end
  - Never guesses which row to update — if more than one matches, it asks; if none match, it stops rather than creating a new row (run /applied first)
  - Doesn't refresh tracking/learned-preferences.md — a status change carries no new title/language/seniority signal

Examples:
  /update-status Acme-Corp-Staff-Software-Engineer.md Screening interview
  /update-status Acme-Corp-Staff-Software-Engineer.md Not Selected
```

---

## Step 1 — Resolve the Job Description

Read `variable-input/job-descriptions/<filename>`. Extract, if present in the text: company name, position title, and a company-issued req/job ID.

---

## Step 2 — Locate the Tracking Row (unified, multi-signal)

Derive `<base-name>` via `python3 scripts/base_name.py applicant-job --applicant-name "<applicant name>" --job-filename "<filename>"`.

Look up matching rows:

```bash
python3 scripts/find_tracking_row.py lookup --file tracking/applications.ndjson \
  --base-name "<base-name>" --job-id "<req ID, if found>" \
  --company "<company>" --position-title "<title>"
```

**`match_count` is 0:** stop and tell the user. Suggest running `/applied` first if this job was never logged, or double-checking the filename. Do not create a row.

**`match_count` is more than 1:** this is expected, not just an edge case — reapplying to the same job after a rejection produces two rows that legitimately match on the same `<base-name>`. Show every candidate (`date_applied`, current `application_status`) and ask the user which one to update. Do not guess, and do not update more than one.

**`match_count` is exactly 1:** proceed to Step 3.

---

## Step 3 — Build and Confirm the Proposed Update

Never silently inject a date or write the field without the user seeing the exact result first — except the one narrow carve-out in step 3 below for an undated "Not Selected"/"Rejected" stage, where there is nothing left to confirm:

1. Take the new status text — everything in `$ARGUMENTS` after the filename token.
2. Append style: `job-tracker.html` splits `application_status` on newlines to render each stage as its own bullet (`statusSegments()` in `job-tracker.html`), stripping any leading `"- "` on each line but not otherwise treating inline `" - "` text as a separate stage. So the new stage must always be newline-separated from what's already there:
   - If `application_status` is currently `null` or empty, the new value is just `<text>`, no separator.
   - Otherwise append `"\n<text>"` (a leading `"- "` on the new line is optional — the tracker strips it either way — but never join with an inline `" - "` on the same line, since that would collapse into one bullet instead of two).
3. If `<text>` doesn't already look like it contains a date, decide how to add today's date as `" (Mon D)"` (e.g. `(Aug 21)`):
   - **Terminal outcome — no prompt.** If `<text>`'s leading word(s), case-insensitively, are "Not Selected" or "Rejected", auto-append today's date with no confirmation question about the date. A closed-out application has no future date left to track or get wrong: today is simply the day the outcome was recorded, backfilling it later is trivial if ever needed, and asking here is friction with no offsetting benefit.
   - **Everything else — suggest and confirm.** For any other stage text (e.g. "Screening interview", "Offer Received"), propose the same `" (Mon D)"` addition but treat it as a **suggestion to confirm, not a silent default**. Backfilling a stage that happened days ago is a normal use case here; silently stamping today's date would record wrong data with no visible sign it happened.
4. Show the user the **full resulting `application_status` string** (existing text plus the addition). For the terminal-outcome case above, this can be shown as the confirmed result already being written (no separate question needed) — mention it plainly in the Step 5 report. For every other case, ask the user to confirm, adjust the date, or cancel before writing. This confirmation step is also the idempotency check for non-terminal stages — if the proposed addition looks like a near-duplicate of the most recent stage already recorded, the user will see that before confirming and can cancel.

Do not proceed to Step 4 until the user confirms — except the terminal-outcome, auto-dated case in step 3.3/3.4, which proceeds straight to Step 4.

---

## Step 4 — Update the Row

Read every line of `tracking/applications.ndjson`, replace only the matched row's `application_status` field with the confirmed value from Step 3, and rewrite the entire file (same full-rewrite pattern used elsewhere in this pipeline — not a targeted line patch).

---

## Step 5 — Report

```
Status updated.

  Company        : <company>
  Position       : <position_title>
  Previous status: <old application_status, or "(none)">
  New status     : <new application_status>
```

Note: this command never refreshes `tracking/learned-preferences.md` — a status change carries no new company/title/seniority/language signal, so refreshing it here would be wasted work. Only `/applied` (a genuinely new application row) triggers that refresh.
