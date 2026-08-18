---
name: applied
description: Record that the applicant has applied to a job, in the tracking log
---

Record a new job application in the tracking log for the following job description file: $ARGUMENTS

You are maintaining the applicant's job-application tracking log. Every application gets exactly **one row**, written once, at the time this command runs — never overwrite or merge into an existing row, even if `/applied` is run again later for the same job (ask the user to confirm if that looks like it might be happening, per Step 1).

---

## Step 1 — Resolve the Job Description

Read `variable-input/job-descriptions/$ARGUMENTS`. Extract, if present in the text: company name, job/position title, source URL, and a company-issued req/job ID.

Check `tracking/applications.ndjson` (if it exists) for an existing row with the same `company` + `position_title` (case-insensitive). If one exists, tell the user and confirm they want to log this as a **new, separate** application (e.g. re-applying after a rejection) before continuing — don't silently create a duplicate-looking row without asking.

---

## Step 2 — Pull Pipeline Data

Derive `<base-name>` using the exact same normalization rule as `tailor-resume.md` Step 0 (applicant name + job description filename stem).

Check whether `output/<base-name>.manifest` exists:
- If it exists, read `output.resume_pdf`, `output.cover_letter_pdf`, `job_match`, `suggested_asking_salary`, and `job_posting_salary_range` from it.
- If it doesn't exist, proceed anyway — those fields will be `null` — and mention to the user that `/tailor-resume $ARGUMENTS` hasn't been run yet for this job, so no resume/match-score/salary data is available to attach.

---

## Step 3 — Determine Source

Check `output/job-search-seen.json` (if it exists) for an entry whose `redirect_url` or `company`+`title` matches this job. If found, set `source` to `"Adzuna via /find-job-descriptions"`. Otherwise set `source` to `"manual"`.

---

## Step 4 — Determine Salary Range

This populates `salary_range` — the market/posting figure, not the recommended ask (that's `recommended_ask`, unchanged, sourced from `suggested_asking_salary`).

1. If Step 2 found a non-null `job_posting_salary_range` in the manifest, use it directly: `"<range> (<source>)"`, e.g. `"$120,000 - $150,000 CAD (posted)"`.
2. Otherwise, check the job description text read in Step 1 for an explicit stated salary/range. If found, use it verbatim with `(posted)`.
3. Otherwise, run a `WebSearch` for `"<company> <position_title> salary Glassdoor"` (include "Vancouver" or the job's stated location if relevant) and extract a range if a credible source surfaces. Label it `(Glassdoor)` or `(researched)` depending on the source found.
4. If nothing credible turns up, set `salary_range` to `null` — never fabricate a figure.

---

## Step 5 — Determine Glassdoor Rating

This populates `glassdoor_rating` — the company's overall Glassdoor rating out of 5.0, not tied to this specific posting.

1. First check `tracking/applications.ndjson` for any existing row with the same `company` (case-insensitive) that already has a non-null `glassdoor_rating`. If found, reuse that value — don't re-search for a company you've already looked up.
2. Otherwise, run a `WebSearch` for `"<company> Glassdoor rating reviews"` and extract the overall rating (e.g. `"3.8"` from "3.8 out of 5" or "3.8/5"). Store it as a plain number string, e.g. `"3.8"`.
3. If no credible rating is found, set `glassdoor_rating` to `null` — never fabricate a figure.

---

## Step 6 — Fill Remaining Fields

- `date_applied`: today's date, unless the user specifies otherwise.
- `apply_method`: if not obvious from the job description text (e.g. "apply on our careers site" vs. a recruiter contact), ask the user directly — don't guess. Free text, e.g. "Online - Company site", "Referral", "Recruiter appointment".
- `job_id`: use the req ID extracted in Step 1 if found; otherwise ask the user if they have one, or leave `null`.
- `application_status`: initialize to `"Applied"`.

---

## Step 7 — Append the Row

Append exactly one line to `tracking/applications.ndjson` (create the file if it doesn't exist) with this shape:

```json
{"date_applied": "<YYYY-MM-DD>", "company": "<company>", "position_title": "<title>", "job_id": "<id or null>", "application_status": "Applied", "apply_method": "<method>", "job_posting_url": "<url or null>", "recommended_ask": "<from suggested_asking_salary, or null>", "salary_range": "<from Step 4, or null>", "glassdoor_rating": "<from Step 5, or null>", "match_score": {"total": <n>, "skill_overlap": <n>, "experience_relevance": <n>, "seniority_match": <n>, "transferable_skills": <n>, "interpretation": "<label>"} or null, "resume_file": "<path or null>", "cover_letter_file": "<path or null>", "source": "<manual|Adzuna via /find-job-descriptions>"}
```

---

## Step 8 — Regenerate the Human-Readable Views

Read every line of `tracking/applications.ndjson` and regenerate both of these in full (don't append — always rewrite from the complete NDJSON so they never drift):

**`tracking/applications.md`** — a single Markdown table, most recent `date_applied` first:
```
| Date Applied | Company | Position Title | Job ID | Status | Apply Method | Match Score | Recommended Ask | Salary Range | Glassdoor | Resume | Cover Letter | Source | URL |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-08-16 | Acme Corp | Staff Software Engineer | 200630278 | Applied | Online - Company site | 82 (Strong match) | $150,000 - $165,000 CAD | $120,000 - $150,000 CAD (posted) | 3.8 | [PDF](../output/...) | [PDF](../output/...) | manual | [link](https://...) |
```
Use `—` for any `null`/missing field. Match Score column shows `<total> (<interpretation>)`, or `—` if `null`.

**`tracking/applications.tsv`** — tab-separated, one line per row, same column order as the Markdown table's header. Before writing, replace any literal tab or newline character inside a field value with a single space, so the file stays strictly one-row-per-line (this is what makes it safely reimportable into Excel/Numbers — unlike CSV, commas in job titles never need escaping since the delimiter is a tab).

---

## Step 10 — Refresh Learned Preferences

Silently refresh `tracking/learned-preferences.md` so it never goes stale without the user having to remember `/learn-preferences`:

1. If `tracking/learned-preferences.md` and `tracking/.learned-preferences.hash` both exist, check for hand-edits exactly like `/learn-preferences` Step 4:
   ```bash
   shasum -a 256 tracking/learned-preferences.md
   ```
   Compare to the contents of `tracking/.learned-preferences.hash`. On a mismatch, the user has hand-edited the file since the last auto-write — ask before overwriting, same as `/learn-preferences`.
2. Re-run the same analysis as `/learn-preferences` Steps 1-3 (all rows, including the one just appended, plus career-goals). **Preserve existing wording and conclusions wherever the new row doesn't materially change them** — don't reword stable sections just because the command ran again; only touch what the new evidence actually shifts. This keeps the file stable to read and diff over time.
3. Write the refreshed file and update `tracking/.learned-preferences.hash`, exactly as in `/learn-preferences` Step 5.
4. If nothing material changed, it's fine for the file's content to end up byte-identical — report that plainly rather than manufacturing a change.

---

## Step 11 — Report

```
Application recorded.

  Company        : <company>
  Position       : <position_title>
  Date applied   : <date_applied>
  Match score    : <total>/100 (<interpretation>) [or "not available — run /tailor-resume first"]
  Salary range   : <salary_range or "not found">
  Glassdoor      : <glassdoor_rating or "not found">/5.0
  Tracked in     : tracking/applications.ndjson (row appended)
  Views updated  : tracking/applications.md, tracking/applications.tsv
  Preferences    : <"refreshed — <one-line summary of what changed>" or "no material change">
```
