# AGENTS.md

This file provides guidance to AI coding agents (Claude Code, OpenAI Codex CLI, Google Gemini CLI, GitHub Copilot CLI, OpenCode, and others) working with code in this repository.

Throughout this document, `/skill-name <args>` is shorthand for "the skill named skill-name, given args" — exactly how you invoke it in Claude Code's slash palette. Other supported agents have no slash syntax; make the equivalent request in natural language (e.g. "tailor my resume for `Acme-Corp-Staff-Software-Engineer.md`") and the agent matches it against the skill's description and loads it automatically.

## What This Project Does

This is a resume tailoring system. It takes a modular template of an applicant's full career history and uses AI to produce a tailored, ATS-friendly resume PDF for a specific job posting — without hallucinating skills or experience.

## Supported AI Coding Agents

| Tool | Reads this file | Skill invocation |
|---|---|---|
| Claude Code | via `@AGENTS.md` import in `CLAUDE.md` (Claude Code doesn't read `AGENTS.md` natively) | `/skill-name <args>` |
| OpenAI Codex CLI | natively | natural-language request |
| Google Gemini CLI | natively (Agent Skills support landed ~Jan 2026 — confirm your installed version includes it) | natural-language request |
| GitHub Copilot CLI | natively | natural-language request |
| OpenCode | natively | natural-language request |
| OpenCode + local Ollama (offline) | natively | natural-language request |

All skills live in `.claude/skills/*/SKILL.md` — the [Agent Skills](https://code.claude.com/docs/en/agent-sdk/skills) open format, which works unmodified across every tool above. A `.agents/skills` symlink alongside it points at the same folder, since some tools scan that neutral path instead of `.claude/skills/` directly.

### Running fully offline with OpenCode + Ollama

Install [Ollama](https://ollama.com), pull a capable instruct model, then point OpenCode's provider config at your local Ollama endpoint instead of a cloud API — OpenCode reads this file and `.claude/skills/`/`.agents/skills/` regardless of which model backend it's using. Two skills depend on capabilities not every local model has: `tailor-resume` and `ats-validate` need native PDF text extraction, and `match-resume-style` needs visual PDF rendering. Spot-check these against whatever local model you use before relying on them offline. See [setup-opencode.md](setup-opencode.md) for a full walkthrough — model sizing by RAM, the default-context-window gotcha, and a verification step.

### What does NOT port across tools

`.claude/settings.json` and `.claude/settings.local.json` (permission allowlists for this repo's scripts, `Write`/`Edit` path scoping, web-search/fetch access) are Claude-Code-specific. Every other tool has its own separate permission/approval model (Codex's approval modes, Copilot CLI's allow-list, OpenCode's permission config) — configure it independently per tool if you want to avoid confirmation prompts.

### Authoring convention for skill files

Skill bodies avoid naming Claude-Code-specific tools (`Read`, `Write`, `WebSearch`, `WebFetch`) so the instructions read correctly in any agent. Use plain prose instead: "read the file directly using native text/PDF extraction," "search the web for X," "fetch and read the page at X," "write/save to X." Preserve any specific behavioral guarantee the original wording encoded (e.g. "do not shell out to pdftotext") — only the tool name is generic, not the constraint.

## How to Generate a Resume

The primary entry point is the `tailor-resume` skill. In Claude Code, invoke it via:

```bash
/tailor-resume <name-of-job-description-file>
```

In other supported agents, just ask in natural language (e.g. "tailor my resume for `<file>`") — they match your request against the skill's description and load it automatically.

The job description file should be placed in `variable-input/job-descriptions/` beforehand (markdown, plain text, or PDF).

To convert a markdown resume to PDF manually:

```bash
pandoc output/<applicant-name>-<job-description>.md -o output/<applicant-name>-<job-description>.pdf --pdf-engine=weasyprint -c output/resume-style.css
```

Dependencies: `brew install pandoc weasyprint`

### Validating ATS Friendliness

`/ats-validate <base-name-or-pdf-path>` scores an already-generated resume PDF against ATS screening criteria (parseability, keyword coverage, contact completeness, chronological integrity, content quality) with a detailed findings report and per-finding recommendations — useful for a deeper look than `/tailor-resume`'s own built-in ATS check, or for re-checking a PDF you've hand-edited since it was generated.

## How to Find & Track Jobs

`/find-job-descriptions [min-match-percent]` searches Adzuna for local Staff/Senior Software Development postings (per `variable-input/job-search-preferences.md`), scores them against the resume using the same rubric as `/tailor-resume`'s Step 2b (score math is never adjusted by learned preferences — see below), auto-downloads matches at or above the threshold (default 65%) into `variable-input/job-descriptions/`, and reports ranked results split into a main list and an "outside your typical pattern" section. Requires a free Adzuna API key (see the skill's Step 0 for setup) in a root `.env` file (not committed).

`/applied <job-description-file>` records that the applicant applied to a job, appending one row to `tracking/applications.ndjson` (auto-filling match score and resume/cover-letter paths from `/tailor-resume`'s manifest when available), and refreshing the learned-preferences profile (below).

`/import-applications <path-to-existing-tracking-file>` is a one-time-per-adopter onboarding skill: it reads an arbitrary pre-existing tracker (Word, Excel, Apple Numbers, CSV, plain text, or Markdown) by inspecting its actual structure rather than assuming a fixed layout, maps whatever fields it finds onto the 14-field `applications.ndjson` schema (defaulting anything absent to `null` rather than guessing), shows the inferred mapping and a full preview for confirmation before writing anything, skips entries that already look logged (matched by `job_id` or `company`+`position_title`), and always appends — it never truncates or rewrites existing rows.

`/update-status <job-description-file> <new-status-text>` appends a stage to that same application's `application_status` (e.g. turning `"Applied"` into `"Applied - Screening interview (Aug 12) - Not Selected (Aug 21)"`). It's the one narrow exception to `applications.ndjson` being append-only — only that one field on the matched row is touched, and only additively; nothing is ever removed. It always shows the exact resulting string (including any date it's proposing to add) and asks for confirmation before writing, rather than guessing or silently dating things "today." Doesn't refresh the learned-preferences profile — a status change carries no new title/language/seniority signal.

### Viewing the Tracking Log

`job-tracker.html` (repo root) is a self-contained, dependency-free viewer for `tracking/applications.ndjson` — a sortable table of all applications with a click-to-expand detail view showing every tracked field, including full match-score breakdowns and status history. It reads the ndjson at runtime, so it never needs to be regenerated when the log changes — just refresh the page, or wait up to 30s for it to auto-detect updates. It replaces the `tracking/applications.md`/`tracking/applications.tsv` views that earlier versions of this project generated — those are no longer created. Requires a local HTTP server (fetch won't work over `file://`):

```bash
python3 -m http.server 8000
```

Then open `http://localhost:8000/job-tracker.html`. Run the server from the repo root so relative paths to `tracking/applications.ndjson` and any linked resume/cover-letter PDFs in `output/` resolve correctly.

`/prep-interview <job-description-file> [stage-override]` produces genuine interview coaching, not a cheat sheet: honest skill gaps and real stories to have ready, weighted to the applicant's current interview stage. It prefers a future-dated stage already logged via `/update-status` (e.g. `"Technical screen (Aug 26)"` logged ahead of time); failing that it predicts the likely next stage and says so explicitly rather than guessing silently. Fails fast with no output if the tracked status is already closed (`"Not Selected"`, `"Position Filled"`) or `"Offer Received"`. Unlike `/tailor-resume`, it's explicitly allowed to draw on each experience entry's `# Side Notes` section (tagged as off-resume background when it does) since spoken conversation isn't space-constrained the way a resume is. Writes `output/<base-name>-interview-prep.md`.

Dependencies: none for recurring use (stdlib-only Python). `/import-applications` may install optional packages (`numbers-parser`, `openpyxl`, `xlrd`, or `python-docx`, depending on the source file's format) into an isolated `.venv-tools/` virtualenv on demand — never into the system Python.

## Getting Career Coaching

`/career-coach [freeform question]` answers a specific career question, or with no argument runs a general "what should I work on next" check-in. It reads the full picture before answering: `template/` (career history, skills, education), `variable-input/career-goals/*.md`, `variable-input/salary-expectations.md`, `variable-input/job-search-preferences.md`, all of `tracking/applications.ndjson` (including rubric sub-scores on any scored application), and `tracking/learned-preferences.md`. It also searches the web for current market/skill-demand data so advice stays grounded rather than generic. Tone is a fixed, non-negotiable contract in the skill itself: an ally, not a yes-man and not a cynic — every claim must trace to specific evidence from the applicant's own history, real gaps get named plainly alongside a next step, and the applicant gets pushed toward more ambition only as far as their own evidence and local market actually support. Writes nothing to disk; it's advisory only.

## Customizing Resume Style

`/match-resume-style <path-to-reference-resume>` regenerates `formatting.md` and `blueprint.md` to match the visual style of any resume file (PDF, image, or Word doc) instead of this repo's default look — so third-party adopters aren't stuck with the original owner's design. It visually inspects the reference (colors, font character, header treatment, spacing, bullet style, section order), screens every element against the same ATS rules `/tailor-resume` Step 8 already enforces, and adapts anything ATS-risky (multi-column/sidebar layouts, icons, photos, custom bullet glyphs) to a safe equivalent rather than adopting or silently dropping it. Shows the proposed style and every adaptation made, then renders a preview PDF from real `template/` data, before writing anything. Both target files are git-tracked, so `git checkout -- formatting.md blueprint.md` reverts a change.

## Testing

`/test-fixtures [all|scoring|tailor-resume|tracking|import-applications]` runs this repo's LLM-based test fixtures (`fixtures/scoring/` and `fixtures/commands/`) end to end by invoking the real skills inline, comparing results against each fixture's `expected.md`, and cleaning up every scratch file and mutated tracking file afterward — regardless of outcome. Covers what `pytest` can't: the actual rubric scoring and real skill flows (stale-check, ambiguous-reapply handling, date-convention detection) that need an LLM's judgment. See `fixtures/scoring/README.md` and `fixtures/commands/README.md` for what each fixture checks.

## Architecture

The system separates static career data (template) from variable inputs (job context), and compiles a tailored output through the rules in `blueprint.md`.

- **`blueprint.md`** — Defines the resume's section layout and order only (a token template); pure visual/structural layout, not the assembly logic. The step-by-step assembly rules, content-selection logic, and output constraints (2 pages max, no fabrication, verbatim bullets unless rephrasing is critical) live in `.claude/skills/tailor-resume/SKILL.md`, which reads `blueprint.md`'s Layout section as its single source of truth for section order.
- **`formatting.md`** — CSS class mapping and styles for all resume sections. This drives the visual output when pandoc+weasyprint renders the PDF.
- **`template/`** — The applicant's full career data, never edited per-job:
  - `experience/<YYYY-MM_YYYY-MM>.md` — one file per job, named by date range
  - `all-skills.md`, `education.md`, `certifications.md`, `publications.md`
- **`variable-input/career-goals/`** — One or more `.md` files describing the applicant's intended direction. Combined with the job description to guide relevance filtering.
- **`variable-input/job-search-preferences.md`** — Title keywords, target location(s), and exclusions used by `/find-job-descriptions`.
- **`variable-input/job-descriptions/`** — Drop job posting files here before running (or let `/find-job-descriptions` download them for you).
- **`scripts/`** — Standalone Python helpers invoked by skills: `find_jobs.py` (Adzuna search + seen-jobs ledger), and others listed in `README.md`.
- **`tracking/`** — Job application log: `applications.ndjson` (source of truth, one JSON object per row, browsable live via `job-tracker.html`) is committed — it's small, durable, personal history worth version-controlling, and every row is a discrete, meaningful, append-only fact. `learned-preferences.md` (revealed preferences, derived from the log + career goals) and its `.learned-preferences.hash` hand-edit-detection sidecar are gitignored instead: they're fully regenerable from `applications.ndjson` + career-goals via `/learn-preferences` (or self-bootstrap automatically on the next `/find-job-descriptions`/`/applied` run if missing), and committing a file that gets rewritten after nearly every `/applied` run would just add prose-diff noise to the history for no lasting benefit.
- **`.claude/skills/*/SKILL.md`** — The skill definitions themselves (Agent Skills format — see "Supported AI Coding Agents" above). `.claude/skills/load-career-profile/SKILL.md` is an internal helper skill (loads `template/` data) invoked by several of the others; it's not meant for direct end-user invocation.
- **`output/`** — Generated markdown and PDF files, plus job-search working state (`job-search-candidates.json`, `job-search-seen.json`), land here (not committed).

## Key Rules from blueprint.md

- Read all files under `template/` recursively before generating output.
- Bullet points from experience entries should stay verbatim unless rephrasing is essential.
- Experience older than 10 years gets lighter treatment unless directly relevant.
- Fact-check the markdown output against the template before producing the PDF.
- Final output must fit within 2 PDF pages.
- Save all outputs to the `output/` directory.
