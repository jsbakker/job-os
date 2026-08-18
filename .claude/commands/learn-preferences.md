---
name: learn-preferences
description: Analyze application history and career goals to build a learned preference profile that sharpens job matching
---

Analyze the applicant's job-application history and career goals to build (or refresh) `tracking/learned-preferences.md` — a profile of revealed job preferences used by `/find-job-descriptions` to cut noise without touching its scoring rubric.

---

## Step 1 — Read Inputs

1. `tracking/applications.ndjson` — every row (create nothing if it doesn't exist yet; report that there's no history to learn from and stop).
2. All files under `variable-input/career-goals/`.

---

## Step 2 — Classify Career Goals

For each career-goals file, judge whether its content is a literal statement of intent or clearly non-literal (humor, hyperbole, a joke framing). Flag any non-literal file explicitly — it must not feed literal inference in Step 3, but note it was seen and excluded, rather than silently ignoring it.

---

## Step 3 — Derive Patterns

Read every row's `company`, `position_title`, `application_status`, `date_applied`, `match_score`, and `source`. Weight evidence by confidence, not just frequency:

- **Highest confidence:** rows with a non-null `match_score` (an actual rubric-scored fit assessment from `/tailor-resume`, not just a title-text guess).
- **Medium confidence:** recent rows (roughly the last 6 months of `date_applied`) without a `match_score`.
- **Lowest confidence:** older, title-only rows imported from the legacy spreadsheet — real signal, but weaker; a single old instance should not be reported as a "confirmed" pattern.

From this, and from the literal career-goals files, derive:

1. **Confirmed patterns** — seniority level(s), languages, platforms/domains, and role-shape (IC vs. management, testing/CI-CD-adjacent, etc.) that recur across multiple recent and/or `match_score`-backed rows, cross-referenced with what the career-goals files literally say.
2. **Weaker signals** — patterns backed only by a single instance or by old title-only rows. Label these explicitly as weak — don't present them with the same confidence as confirmed patterns.
3. **Notably absent** — categories of role that plausibly had real opportunity volume in the source data (reason about this from the roles actually seen, e.g. if many generic "Software Engineer" postings exist in a domain he never applied to) but drew ~zero applications despite that. This is the section that actually reduces report noise in `/find-job-descriptions` — be specific (name the category, e.g. "frontend web framework roles (Angular/React)", "CRM/Salesforce platform roles", "ML research roles", "pure cloud/distributed-backend roles"), not vague.

Do not treat this as a strict filter rulebook — it's evidence for judgment calls elsewhere, not a hard yes/no gate in itself.

---

## Step 4 — Check for Hand-Edits Before Overwriting

If both `tracking/learned-preferences.md` and `tracking/.learned-preferences.hash` already exist:

```bash
shasum -a 256 tracking/learned-preferences.md
```

Compare the resulting hash to the contents of `tracking/.learned-preferences.hash`.
- **Match:** no hand-edits since the last auto-write — proceed to Step 5 normally.
- **Mismatch:** the user has edited the file since it was last generated. Show them a brief summary of what Step 3 would write instead, and ask whether to overwrite, merge (fold their edits' intent into the new version), or leave the file untouched this run. Do not silently overwrite hand-edited content.

If either file is missing, this is a first-time generation — proceed directly to Step 5.

---

## Step 5 — Write the Profile

Write `tracking/learned-preferences.md`:

```markdown
_Last auto-generated: <YYYY-MM-DD> from <N> application(s) and <M> career-goal file(s). Hand-edits are detected and protected on the next refresh._

## Confirmed Patterns
- <seniority levels, languages, platforms, role-shape, each with a one-line evidence citation, e.g. "Staff/Senior IC titles — 41 of 43 title-bearing rows since 2026-01, e.g. 'Staff Mobile Engineer, iOS' (Mozilla), 'Senior Software Engineer' (Microsoft)">

## Weaker Signals
- <single-instance or old-only patterns, clearly labeled low-confidence>

## Notably Absent
- <categories with real opportunity volume but ~zero applications, e.g. "Frontend web-framework roles (Angular/React) — none applied to despite postings existing in every /find-job-descriptions run so far">

## From Career Goals
- <literal goals tied back to the patterns above>
- Excluded as non-literal: <file>.md (reason)

---
Hand-edit this file freely — the next `/learn-preferences` or `/applied` run will detect changes via `tracking/.learned-preferences.hash` and ask before overwriting rather than clobbering them.
```

Then write the hash sidecar:
```bash
shasum -a 256 tracking/learned-preferences.md | awk '{print $1}' > tracking/.learned-preferences.hash
```

---

## Step 6 — Report

```
Learned-preferences profile <generated|refreshed>.

Confirmed patterns:
  - <one line each>

Notably absent:
  - <one line each>

[If a hand-edit conflict was resolved:]
  <how it was resolved>

Written to: tracking/learned-preferences.md
```
