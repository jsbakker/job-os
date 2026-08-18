# Agentic Resume Blueprint
A templated blueprint to tailor your resume to specific job descriptions. This project uses agentic AI to build a specialized version of your resume from the modularized template.


## Problem Statement
The modern job search requires tailoring a specialized resume for each individual job decription, if you don't want to be filtered out by ATS before any actual human sees your application.

Applicant Tracking Systems (ATS) can look for keywords for a role, and reject your application if your resume does not match. Even if a keyword is present, structure or formatting inconsistencies can disqualify it from being parsed correctly.

Manually tailoring your resume to optimize it for each job application can be very time-consuming - and it still may not be ATS-friendly. You can use AI to tailor your resue to a specific job description, but there will be hallucinations that need editing. In worse cases, the hallucinations can make the applicant look like a liar.


## Solution
The solution is to provide data that is the most relevant to the postion you're applying for. When you create a very detailed resume, the experience section can get too long, and you have to trade off between cutting one proud accomplishment over another.

If we provide all of the information and let AI filter out what is most relevant based on a job description, it makes the decisions a bit easier.

Why would I need this, if LinkedIn has built-in AI that already does it? I've seen what LinkedIn AI can do, and it was too flawed to feel comfortable letting it represent me on a professional level.

If we prescribe a structure, format and style, and instruct AI using agent skills, we can put our own standards and quality measures on it. We can control many elements of a resume to be deterministic.


## Requirements
- Text editor (preferably with Markdown support)
- pandoc
- weasyprint

`brew install pandoc weasyprint`


## Instructions
To generate a resume:

1. Populate your applicant information into the template as per the provided  "Project Structure" section below.
2. Populate the career goals with your intentions. See `career-goals/goals.md`.
3. Place a job descrption file in the `job-descriptions` folder. It can be markdown, plain text, or even a PDF — or let `/find-job-descriptions` (below) find and download one for you.
4. Open Claude Code in the root folder. E.g.:
```bash
cd <path-to-repo>
claude
```
5. Pass the job description to the tailor-resume Claude skill. E.g.:
```bash
/tailor-resume <name-of-job-desctiption-file>
```
6. Review the claude output for job match, suggested asking salary, and ATS validation.
7. View the output PDF in the resulting `output` folder.
8. Once you've submitted the application, record it:
```bash
/applied <name-of-job-desctiption-file>
```

### Finding jobs automatically

`/find-job-descriptions [min-match-percent]` searches for live local postings (via the free Adzuna API), scores them against your resume, and auto-downloads strong matches (65% by default) into `variable-input/job-descriptions/`, skipping anything already logged in `tracking/`:
```bash
/find-job-descriptions
/find-job-descriptions 60   # loosen the threshold
```
One-time setup: sign up for a free key at [developer.adzuna.com](https://developer.adzuna.com/), then create a `.env` file (git-ignored) in the repo root:
```
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
```
Edit `variable-input/job-search-preferences.md` to set your target title keywords and location.

The report is split into a main ranked list and an "outside your typical pattern" section, based on `tracking/learned-preferences.md` — a profile of what you actually apply for, learned from `tracking/applications.ndjson` and your career goals. It never changes the job-match score itself (that stays identical to what `/tailor-resume` would compute), it just keeps off-pattern reaches from cluttering the main list. Run it explicitly (or let it build itself automatically on first use):
```bash
/learn-preferences
```
It's safe to hand-edit `tracking/learned-preferences.md` afterward — the next refresh detects manual changes and asks before overwriting them.


## Project Structure
```
root
├─ blueprint.md
├─ CLAUDE.md
├─ formatting.md
├─ scripts
│  ├─ find_jobs.py
│  └─ import_numbers_tracking.py
├─ template
│  ├─ all-skills.md
│  ├─ certifications.md
│  ├─ contact-info.txt
│  ├─ education.md
│  ├─ experience/
│  |  └─ <YYYY-MM_YYYY-MM>.md
│  └─ publications.md
├─ tracking
│  ├─ applications.ndjson
│  ├─ applications.md
│  ├─ applications.tsv
│  ├─ learned-preferences.md
│  └─ .learned-preferences.hash
├─ variable-input
│  ├─ career-goals
│  ├─ job-descriptions
│  ├─ job-search-preferences.md
│  └─ salary-expectations.md
└─ README.md
```

### .claude (hidden)
Includes settings for permissions to `output` folder, and defintions for resume-building commands.

### blueprint.md
Includes the plan for building the resume from its modularized parts.

### CLAUDE.md
Instructions for Claude Code on how to use this project. Loaded into every new session.

### formatting.md
Includes the specifics for formatting.

### template/contact-info.txt
The applicant's name, title, phone, email, and web link (typically LinkedIn). Used to populate the resume header. LinkedIn URLs are labelled `li:` in the output; other web links use `w:`.

### template/all-skills.md
Includes a high-level list of all of the applicant's skills.

### template/certifications.md
Includes a list of certifications the applicant has. Optional.

### template/education.md
Includes a list of education that the applicant has.

### template/experience/*.md
Each file describes a single entry of work history.

### template/publications.md
Includes the names and links to any written work published by the applicant. Optional.

### variable-input/career-goals/*.md
One or many career goals, combined or as standalone career paths, should be specified.

### variable-input/job-descriptions/*
Place job descrptions here. They can be markdown, plain text, or a PDF.

Using a link to an online job posting is not recommended, as some sites block robots 

### variable-input/job-search-preferences.md
Used by `/find-job-descriptions`: title keywords to match (any one), target location(s), and optional exclusions. Edit freely; never overwritten by the command.

### scripts/find_jobs.py
Queries the Adzuna jobs API and maintains a seen-jobs ledger (`output/job-search-seen.json`) so repeated searches don't re-fetch or re-score the same posting. Invoked by `/find-job-descriptions`, not run directly.

### scripts/import_numbers_tracking.py
One-time migration tool that imports a legacy `JobApplicationTrackingLatest.numbers` spreadsheet into `tracking/applications.ndjson`. Requires the `numbers-parser` package — install it in an isolated virtualenv (`python3 -m venv .venv-tools && ./.venv-tools/bin/pip install numbers-parser`) rather than your main Python install.

### tracking/applications.ndjson, applications.md, applications.tsv
The job-application log is **one dataset in three files**, not three separately-maintained trackers:

- `applications.ndjson` — the only file `/applied` writes to directly. One JSON object per line, one row per application, append-only. This is the source of truth.
- `applications.tsv` — tab-separated export, fully regenerated from the ndjson on every `/applied` run. Opens directly in Excel/Numbers (File > Open), which is what makes the log usable outside Claude Code. Tab-delimited rather than CSV specifically because job titles can contain commas.
- `applications.md` — Markdown table, also fully regenerated on every run. For reading the log in Claude Code or on GitHub without opening a spreadsheet app.

Because `.md` and `.tsv` are always rewritten in full from `.ndjson` rather than edited incrementally, they can't drift out of sync with it — but this does mean every `/applied` call touches all three files.

Each row: `date_applied`, `company`, `position_title`, `job_id`, `application_status`, `apply_method`, `job_posting_url`, `recommended_ask` (the suggested ask from `/tailor-resume`'s Step 2c), `salary_range` (the job posting's own stated range, or a Glassdoor/researched estimate if the posting didn't state one — not the same figure as `recommended_ask`), `glassdoor_rating` (company's overall rating out of 5.0, looked up once per company and reused across repeat applications), `match_score`, `resume_file`, `cover_letter_file`, `source`. Fields `/applied` can't determine (no `/tailor-resume` run yet, no Glassdoor listing found, etc.) are left `null` rather than guessed.

### tracking/learned-preferences.md, .learned-preferences.hash
A profile of revealed job preferences, built by `/learn-preferences` from `applications.ndjson` + `variable-input/career-goals/*.md`, and consulted by `/find-job-descriptions` to decide what belongs in the main ranked report versus the "outside your typical pattern" section. It never adjusts the job-match score itself — only where a candidate is *displayed*, and a score of 70+ always lands in the main list regardless of pattern fit, so a strong rubric match can never be hidden by a behavioral guess. Confidence is weighted: patterns backed by `match_score`-scored applications outrank ones inferred from title text alone, and a single old instance is labeled a weak signal rather than a confirmed pattern. Refreshes automatically after every `/applied`, and self-bootstraps on first `/find-job-descriptions` run if it doesn't exist yet.

It's meant to be hand-edited if the AI's inferred pattern is wrong. `.learned-preferences.hash` is a small sidecar (the SHA-256 of the last auto-written content) that lets the next refresh detect manual edits and ask before overwriting, instead of silently clobbering them.

### variable-input/salary-expectations.md
Optional. Your current salary and/or minimum/target compensation, e.g.:
```
Current salary: $110,000
Minimum acceptable: $120,000
Target range: $130,000 - $150,000
Location: Remote (Canada)
Currency: CAD
```
If present, the skill treats "Minimum acceptable" as a floor the suggested asking salary won't go below, and "Currency" as the reporting currency. If absent, the skill infers currency from the job posting (if it states one) or the applicant's location, and never defaults to USD. The asking-salary suggestion itself is computed from the job posting, researched market data, and job-fit score.

### README.md
This current file.
