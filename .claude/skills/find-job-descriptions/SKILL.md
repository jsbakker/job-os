---
name: find-job-descriptions
description: Search for local job postings that match the applicant's resume, career goals, and revealed application preferences; auto-download strong matches and report ranked results
---

Search for job postings that match the applicant's resume, skills, and career goals. Minimum match percentage to auto-download: $ARGUMENTS (if blank or not a number 0-100, default to 65).

*(In Claude Code, `$ARGUMENTS` is what follows `/find-job-descriptions` in the slash palette. In agents without slash syntax, treat this as the minimum match percentage the user named, or default to 65.)*

You are an expert technical recruiter working on the applicant's behalf. Follow every step below in order.

---

## Help Check

(This exact-match escape hatch is for Claude Code's `/find-job-descriptions help` slash syntax; other agents should just answer help questions about this skill conversationally using the Usage block below.)

Check this **before** attempting to parse `$ARGUMENTS` as a number. If `$ARGUMENTS`, trimmed of whitespace, equals `help` (case-insensitive), print the block below and stop. Do not run any other step.

```
/find-job-descriptions — Searches Adzuna for live local job postings matching your preferences and resume, scores each one with the same rubric /tailor-resume uses, auto-downloads strong matches, and reports ranked results split by your revealed application preferences.

Usage:
  /find-job-descriptions [min-match-percent]

What it does:
  - Builds a search from variable-input/job-search-preferences.md (title keywords, location, exclusions)
  - Fetches candidates via scripts/find_jobs.py, fetches full posting text, and scores each against your template/ + career-goals using tailor-resume's job-match rubric
  - Auto-downloads full-text candidates scoring at or above the threshold into variable-input/job-descriptions/
  - Reports a "Main ranked matches" list plus a separate "Outside your typical pattern" section, grounded in tracking/learned-preferences.md

Gotchas:
  - Requires a free Adzuna API key in a root .env file — Step 0 explains setup if it's missing
  - min-match-percent defaults to 65 if omitted or not a number 0-100
  - Score math is never adjusted by learned preferences — only which section a candidate is displayed in changes; a score of 70+ always lands in the main list regardless
  - Never auto-saves a snippet-only posting (no full text fetched), no matter how high it scores

Examples:
  /find-job-descriptions
  /find-job-descriptions 50
```

---

## Step 0 — Setup Check

Confirm Adzuna credentials are configured without ever printing their values:

```bash
if [ -f .env ] && grep -q '^ADZUNA_APP_ID=' .env && grep -q '^ADZUNA_APP_KEY=' .env; then echo "ok"; else echo "missing"; fi
```

If it prints `missing`, stop and tell the user:
```
Adzuna API credentials not found. To set this up (one-time, free):
1. Sign up at https://developer.adzuna.com/ (instant approval).
2. Create a file named .env in the repo root containing:
   ADZUNA_APP_ID=your_app_id
   ADZUNA_APP_KEY=your_app_key
3. Re-run /find-job-descriptions.
```

---

## Step 1 — Read Inputs

Read the following before doing any matching:

1. `variable-input/job-search-preferences.md` — title keywords, target location(s), exclusions
2. Invoke the `load-career-profile` skill in `full` mode to load `template/` (full career data, including `contact-info.txt`'s current title/location) and `variable-input/career-goals/*.md` (career direction and target seniority).
3. `tracking/applications.ndjson` — if present, one JSON object per line; each row's `company` and `position_title` (and `job_posting_url` if set) identify jobs already applied to. Skip silently if the file doesn't exist yet (no applications tracked).
4. `tracking/learned-preferences.md` — revealed job preferences learned from application history. **If it doesn't exist yet**, run `.claude/skills/learn-preferences/SKILL.md`'s Steps 1-5 inline right now to build it before continuing (self-bootstrapping — the user shouldn't need to remember a separate skill for this to work the first time).

**Staleness advisory (non-blocking):** compare the `Last auto-generated` date in `tracking/learned-preferences.md`'s header to the most recent modification among `variable-input/career-goals/*.md` and `tracking/applications.ndjson`. If either is newer, note in the Step 9 report that the preference profile may be stale and suggest running `/learn-preferences` — don't block or auto-refresh it here.

---

## Step 2 — Derive Search Parameters

- Parse `variable-input/job-search-preferences.md`: the "Title keywords" line becomes a comma-separated `what_or` string; the "Location" line's primary place name becomes `--location`.
- Determine the match threshold: use `$ARGUMENTS` if it parses as an integer 0-100, otherwise default to **65**.

---

## Step 3 — Fetch Candidates

```bash
python3 scripts/find_jobs.py \
  --title-variants "<title keywords from Step 2>" \
  --location "<location from Step 2>" \
  --country ca \
  --max-days-old 21 \
  --pages 2 \
  --out output/job-search-candidates.json
```

If this fails because `python3` is missing, tell the user to install Python 3 (it ships with macOS by default — this would be unusual). If it fails for any other reason (network, credentials), surface the script's error message verbatim and stop.

Read `output/job-search-candidates.json` — an array of candidate objects: `id`, `dedupe_key`, `title`, `company`, `location`, `redirect_url`, `created`, `snippet`, `full_text`, `full_text_fetched`, `score` (nullable — non-null means a prior run already scored it), `saved`, `date_found`, and — once a candidate has been scored at least once — `skill_overlap`/`experience_relevance`/`seniority_match`/`transferable_skills`/`interpretation`/`formatted_report`/`confidence` (absent/null on a candidate that predates this schema or hasn't been scored yet).

---

## Step 4 — Prefilter & Dedupe

For each candidate, drop it from further processing (but still count it) if any of these are true:
- [ ] Title contains none of the configured title keywords even loosely (Adzuna's `what_or` is permissive; re-check here).
- [ ] Location is not in the target region and the posting isn't remote/Canada-remote.
- [ ] Title or company matches an "Exclude" entry from `job-search-preferences.md`.
- [ ] **Already applied:** the candidate's `company` + `title` (case-insensitive) or `redirect_url` matches an existing row in `tracking/applications.ndjson`. Mark these `already_applied: true` — they are excluded from scoring/saving and reported separately, never re-suggested.

---

## Step 5 — Full-Text Fallback (web fetch)

For each surviving candidate where `score` is `null` and `full_text_fetched` is `false` and `redirect_url` is set: fetch and read the page at the `redirect_url`, extracting the full job posting text (title, requirements, responsibilities, compensation if stated). Cap this at **15 fetch calls per run** — prioritize candidates with the strongest apparent title/keyword match first if the prefiltered list is longer than that.

- If the fetch returns substantial job-posting content, treat that as the candidate's full text and set `full_text_fetched: true`.
- If the fetch fails, times out, or returns only boilerplate/login-wall content, leave the candidate **snippet-only** (its Adzuna `snippet` is all that's available).

Candidates with `score` already non-null (reused from the ledger by the script) skip this step entirely — no network calls needed, their cached score is used directly in Step 6/7.

---

## Step 6 — Score

For every candidate that still needs a score (i.e., `score` is `null`), invoke the `score-job-match` skill (the same rubric `/tailor-resume` uses — Skill Overlap 0-30, Experience Relevance 0-30, Seniority Match 0-20, Transferable Skills 0-20) against:
- The candidate's full text if `full_text_fetched` is true, or its `snippet` otherwise (flag snippet-only scores as **low-confidence** — they're based on a truncated description and are for reporting only).
- The applicant's `template/` data and `variable-input/career-goals/` files read in Step 1.

Don't pass a prior-manifest path — these candidates don't have one, so `score-job-match` won't run reconciliation. Immediately after each invocation, read `/tmp/job-match-score.json` and copy `total`, `skill_overlap`, `experience_relevance`, `seniority_match`, `transferable_skills`, `interpretation`, and **`formatted_report`** — all of them, not just the numbers — verbatim onto that candidate's own object, before invoking `score-job-match` again for the next candidate. The scratch file is shared and gets overwritten on each invocation, so nothing from one candidate's result survives past the next invocation unless it's copied onto the candidate object first. Also record `confidence` (`full-text` or `snippet-only`) for each. These fields travel with the candidate object into Step 8's ledger write and Step 9's report — Step 9 must not reconstruct a candidate's rationale from memory when `formatted_report` is sitting right there on the object.

**The rubric and its point math stay exactly as defined in tailor-resume.md — do not adjust scores based on learned preferences.** This keeps `/find-job-descriptions` scores directly comparable to `/tailor-resume`'s. Separately, using `tracking/learned-preferences.md` as grounding evidence, attach a **preference-fit label** to every candidate as its own field, never blended into the score:
- `Matches your pattern` — aligns with one or more Confirmed Patterns from the profile.
- `Partial pattern match` — some alignment (e.g. right seniority, novel language/domain), or only backed by a Weaker Signal.
- `Outside your typical pattern` — aligns with a Notably Absent category, or has no supporting pattern at all.

This label is a display/grouping aid for Step 9, not a scoring input.

Candidates with a cached (already non-null) `score` are not re-scored — reuse the cached `total`/sub-scores/`interpretation`/`formatted_report`/`confidence` directly from the candidate object (carried forward by `find_jobs.py` from the ledger), but still compute the preference-fit label fresh each run (the learned-preferences profile can change between runs even when the score doesn't). A candidate cached from before this schema existed may have a `score` but no `formatted_report` — if so, treat it as needing a rescore for the report-fidelity fields specifically: re-invoke `score-job-match` for it despite the cached `score`, so Step 9 always has a real `formatted_report` to draw from rather than an unexplained gap.

---

## Step 7 — Save Matches

For each candidate where `full_text_fetched` is true (this run or cached) **and** total score ≥ the Step 2 threshold:

1. Compute the slug: `SLUG=$(python3 scripts/base_name.py company-title-slug --company "<Company>" --job-title "<Job Title>")` (matches the style of the existing example `variable-input/job-descriptions/City-of-Vancouver-Solutions-Architect.md`).
2. Write the full posting text to `variable-input/job-descriptions/<slug>.md`, prefixed with a short header:
   ```
   Source: <redirect_url>
   Found: <date_found>
   Auto-downloaded by /find-job-descriptions

   ---

   <full posting text>
   ```
3. Mark `saved: true` for that candidate.

**Never** save a snippet-only candidate, regardless of score — note it in the report as "needs manual open" with its URL instead.

---

## Step 8 — Update Ledger

Write `output/job-search-seen.json` (same shape the script wrote in Step 3) back with every evaluated candidate's final `score`, `saved`, `full_text_fetched`, `skill_overlap`, `experience_relevance`, `seniority_match`, `transferable_skills`, `interpretation`, `formatted_report`, and `confidence` values, so future runs reconcile against a threshold instead of re-fetching or re-scoring — and so a future run's Step 9 can report a real rationale for a cached candidate instead of having nothing to draw from.

---

## Step 9 — Report

Split evaluated candidates into two groups — **nothing is ever silently dropped from either the report or `output/job-search-candidates.json`**, this split only controls where each candidate is *displayed*:

- **Main ranked matches:** score ≥ 70 (regardless of preference-fit label — this is a deliberate safety valve so an objectively strong rubric score is never hidden by a behavioral prior), OR score < 70 but labeled `Matches your pattern` / `Partial pattern match`.
- **Outside your typical pattern:** score < 70 **and** labeled `Outside your typical pattern`. List every one of these, not just a couple of examples — the point is to keep them out of the way, not to make them invisible.

```
Job search complete — <N> candidates fetched, <M> already applied (skipped), <K> evaluated.
[If the staleness advisory from Step 1 applies: "Note: your learned-preferences profile may be stale — consider running /learn-preferences."]

Main ranked matches:

Rank  Title @ Company                          Location        Score       Pattern                    Status
----  ---------------------------------------  --------------  ----------  -------------------------  -----------------------
1     Staff Software Engineer @ Acme Corp       Vancouver, BC   88/100      Matches your pattern       Saved → variable-input/job-descriptions/Acme-Corp-Staff-Software-Engineer.md
2     ...

[repeat rationale per entry, one line each: drawn from that candidate's own `formatted_report` field on the candidate object — name the single most decisive matched or absent item it mentions, not a generic restatement of the score. Do not invent or recall a rationale from memory; if a candidate object somehow has no `formatted_report` at this point, say so explicitly rather than fabricating one.]

Outside your typical pattern (<N>):

Rank  Title @ Company                          Location        Score       Status
----  ---------------------------------------  --------------  ----------  -----------------------
1     Staff Front-End Developer (Angular) @ X   Burnaby, BC     42/100      Not saved
2     ...
[one-line reason each, tying back to the specific Notably Absent entry it matches]

Already applied (skipped): <list, if any>
Needs manual open (snippet-only, could not fetch full text): <list with URLs, if any>
```

---

## Step 10 — Next Step Prompt

List every job saved in Step 7 and ask the user which ones to tailor a resume for:
```
Ready to tailor resumes for the strong matches above. Run any of:
  /tailor-resume Acme-Corp-Staff-Software-Engineer.md
  /tailor-resume ...

Which would you like to run now?
```
