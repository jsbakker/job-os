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

## Architecture

The system separates static career data (template) from variable inputs (job context), and compiles a tailored output through the rules in `blueprint.md`.

- **`blueprint.md`** — The core instruction set for the AI: role definition, step-by-step assembly rules, layout template, and output constraints (2 pages max, no fabrication, verbatim bullets unless rephrasing is critical).
- **`formatting.md`** — CSS class mapping and styles for all resume sections. This drives the visual output when pandoc+weasyprint renders the PDF.
- **`template/`** — The applicant's full career data, never edited per-job:
  - `experience/<YYYY-MM_YYYY-MM>.md` — one file per job, named by date range
  - `all-skills.md`, `education.md`, `certifications.md`, `publications.md`
- **`variable-input/career-goals/`** — One or more `.md` files describing the applicant's intended direction. Combined with the job description to guide relevance filtering.
- **`variable-input/job-descriptions/`** — Drop job posting files here before running.
- **`output/`** — Generated markdown and PDF files land here (not committed).

## Key Rules from blueprint.md

- Read all files under `template/` recursively before generating output.
- Bullet points from experience entries should stay verbatim unless rephrasing is essential.
- Experience older than 10 years gets lighter treatment unless directly relevant.
- Fact-check the markdown output against the template before producing the PDF.
- Final output must fit within 2 PDF pages.
- Save all outputs to the `output/` directory.
