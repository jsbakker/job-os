# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

This is a resume tailoring system. It takes a modular template of an applicant's full career history and uses AI to produce a tailored, ATS-friendly resume PDF for a specific job posting — without hallucinating skills or experience.

## How to Generate a Resume

The primary entry point is the `/tailor-resume` skill invoked inside Claude Code:

```bash
/tailor-resume <name-of-job-description-file>
```

The job description file should be placed in `variable-input/job-descriptions/` beforehand (markdown, plain text, or PDF).

To convert a markdown resume to PDF manually:

```bash
pandoc output/<applicant-name>-<job-description>.md -o output/<applicant-name>-<job-description>.pdf --pdf-engine=weasyprint -c output/resume-style.css
```

Dependencies: `brew install pandoc weasyprint`

## How to Find & Track Jobs

`/find-job-descriptions [min-match-percent]` searches Adzuna for local Staff/Senior Software Development postings (per `variable-input/job-search-preferences.md`), scores them against the resume using the same rubric as `/tailor-resume`'s Step 2b (score math is never adjusted by learned preferences — see below), auto-downloads matches at or above the threshold (default 65%) into `variable-input/job-descriptions/`, and reports ranked results split into a main list and an "outside your typical pattern" section. Requires a free Adzuna API key (see the command's Step 0 for setup) in a root `.env` file (not committed).

`/applied <job-description-file>` records that the applicant applied to a job, appending one row to `tracking/applications.ndjson` (auto-filling match score and resume/cover-letter paths from `/tailor-resume`'s manifest when available), regenerating `tracking/applications.md` and `tracking/applications.tsv`, and refreshing the learned-preferences profile (below).

`/learn-preferences` analyzes `tracking/applications.ndjson` + `variable-input/career-goals/*.md` to build `tracking/learned-preferences.md` — a profile of revealed preferences (seniority, languages, platforms, and notably *absent* categories) that `/find-job-descriptions` uses to keep off-pattern reaches out of the main report without touching the scoring rubric. Self-bootstraps on first `/find-job-descriptions` run if it doesn't exist yet, and auto-refreshes after every `/applied`. Hand-edits are protected: a `tracking/.learned-preferences.hash` sidecar detects manual changes and asks before overwriting rather than clobbering them.

Dependencies: none for recurring use (stdlib-only Python). The one-time historical import (`scripts/import_numbers_tracking.py`) needs `numbers-parser`, installed in an isolated `.venv-tools/` virtualenv rather than the system Python — see that script's docstring.

## Architecture

The system separates static career data (template) from variable inputs (job context), and compiles a tailored output through the rules in `blueprint.md`.

- **`blueprint.md`** — The core instruction set for the AI: role definition, step-by-step assembly rules, layout template, and output constraints (2 pages max, no fabrication, verbatim bullets unless rephrasing is critical).
- **`formatting.md`** — CSS class mapping and styles for all resume sections. This drives the visual output when pandoc+weasyprint renders the PDF.
- **`template/`** — The applicant's full career data, never edited per-job:
  - `experience/<YYYY-MM_YYYY-MM>.md` — one file per job, named by date range
  - `all-skills.md`, `education.md`, `certifications.md`, `publications.md`
- **`variable-input/career-goals/`** — One or more `.md` files describing the applicant's intended direction. Combined with the job description to guide relevance filtering.
- **`variable-input/job-search-preferences.md`** — Title keywords, target location(s), and exclusions used by `/find-job-descriptions`.
- **`variable-input/job-descriptions/`** — Drop job posting files here before running (or let `/find-job-descriptions` download them for you).
- **`scripts/`** — Standalone Python helpers invoked by slash commands: `find_jobs.py` (Adzuna search + seen-jobs ledger) and `import_numbers_tracking.py` (one-time legacy tracker migration).
- **`tracking/`** — Job application log: `applications.ndjson` (source of truth, one JSON object per row), plus generated `applications.md`/`applications.tsv` views, plus `learned-preferences.md` (revealed preferences, derived from the log + career goals) and its `.learned-preferences.hash` hand-edit-detection sidecar. Committed (unlike `output/`) since it's small, durable, personal history worth version-controlling.
- **`output/`** — Generated markdown and PDF files, plus job-search working state (`job-search-candidates.json`, `job-search-seen.json`), land here (not committed).

## Key Rules from blueprint.md

- Read all files under `template/` recursively before generating output.
- Bullet points from experience entries should stay verbatim unless rephrasing is essential.
- Experience older than 10 years gets lighter treatment unless directly relevant.
- Fact-check the markdown output against the template before producing the PDF.
- Final output must fit within 2 PDF pages.
- Save all outputs to the `output/` directory.
