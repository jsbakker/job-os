---
name: tailor-resume
description: Tailor the applicant's resume for a specific job description file
---

Tailor the applicant's resume for the following job description file: $ARGUMENTS

*(In Claude Code, `$ARGUMENTS` is what follows `/tailor-resume` in the slash palette — e.g. `/tailor-resume Acme-Corp-Staff-Software-Engineer.md`. In agents without slash syntax, treat this as the job description filename the user named in their request.)*

You are an expert resume crafter and career coach. Follow every step below in order. Do not skip validation steps. If any validation fails, iterate until it passes before moving on.

---

## Help Check

(This exact-match escape hatch is for Claude Code's `/tailor-resume help` slash syntax; other agents should just answer help questions about this skill conversationally using the Usage block below.)

If `$ARGUMENTS`, trimmed of whitespace, equals `help` (case-insensitive) — and only in that exact case, not as part of a real filename — print the block below and stop. Do not run any other step.

```
/tailor-resume — Builds a tailored, ATS-friendly resume and cover letter (as Markdown + PDF) for one specific job posting, using only facts already present in template/, and reports a 0-100 job-match score plus a suggested asking salary.

Usage:
  /tailor-resume <job-description-file>

What it does:
  - Reads the job description from variable-input/job-descriptions/, plus your full template/ career data and career-goals
  - Selects and lightly reorders (never fabricates) skills, experience bullets, and education to fit the posting
  - Renders output/<base-name>.md/.pdf and a matching cover letter, and writes a .manifest with the job-match score and salary analysis
  - Runs ATS structure/keyword checks against the rendered PDF before reporting success

Gotchas:
  - Output is hard-capped at 2 pages — it auto-trims content (oldest/least-relevant first) until it fits
  - Never invents a skill, title, date, or achievement not already in template/ — a real gap stays a gap
  - If none of the inputs changed since the last run for this job, it skips straight to reporting the existing output instead of regenerating

Example:
  /tailor-resume Acme-Corp-Staff-Software-Engineer.md
```

---

## Step 0 — Stale Check

Derive the output base name (the applicant's name comes from `template/contact-info.txt`'s `name:` field):

```bash
APPLICANT=$(grep '^name:' template/contact-info.txt | sed 's/name: *//')
BASE_NAME=$(python3 scripts/base_name.py applicant-job --applicant-name "$APPLICANT" --job-filename "$ARGUMENTS")
echo "$BASE_NAME"
```

Check whether `output/<base-name>.manifest` exists.

If it does, compare current input hashes against it:

```bash
python3 scripts/manifest_check.py compare --job-description "$ARGUMENTS" --manifest "output/$BASE_NAME.manifest"
```

Use its `all_match` field directly — do not hand-compare hashes. `variable-input/salary-expectations.md` is optional and handled internally by the script; its absence never breaks the comparison.

If `all_match` is `true`, check whether the cover letter files also exist:

```bash
ls output/<base-name>-cover-letter.md output/<base-name>-cover-letter.pdf 2>/dev/null
```

- If `all_match` is `true` **and** both cover letter files exist — skip to Step 11 and report:
  ```
  Output is already up to date — no inputs have changed.
    Resume Markdown  : output/<base-name>.md
    Resume PDF       : output/<base-name>.pdf
    Cover Letter MD  : output/<base-name>-cover-letter.md
    Cover Letter PDF : output/<base-name>-cover-letter.pdf
  ```
- If `all_match` is `true` **but** cover letter files are missing — skip to Step 8b to generate the cover letter only, then update the manifest and report.

If `all_match` is `false` (or the manifest is absent), note whether the existing manifest (if any) has a `job_match` block, and its path (`output/<base-name>.manifest`) — Step 2b will need to pass this path to the `score-job-match` skill for reconciliation, even when the reason a rerun was triggered is unrelated to scoring (e.g. only `blueprint.md` changed). Then continue to Step 1.

---

## Step 1 — Read All Inputs

Read the following files before doing any writing:

1. `variable-input/job-descriptions/$ARGUMENTS` — the target job posting. **Read the file directly using native text/PDF extraction — do not shell out to a separate extraction utility such as pdftotext or a subprocess-based parser.** PDF files can be read directly; coding agents extract PDF text natively, and shell-based PDF utilities are not reliably installed.
2. Invoke the `load-career-profile` skill in `full` mode to load `template/` (full career data — contact info, skills, experience with date ranges from filenames, education, certifications, publications) and `variable-input/career-goals/*.md`.
3. `formatting.md` — CSS class mapping and visual styles
4. `variable-input/salary-expectations.md` — if present, the applicant's current salary and/or minimum/target compensation. Optional; skip silently if absent. Freeform, e.g.:
   ```
   Current salary: $110,000
   Minimum acceptable: $120,000
   Target range: $130,000 - $150,000
   Location: Remote (Canada)
   Currency: CAD
   ```
   The `Currency` field, if present, takes priority for all salary figures in Step 2c (see that step's currency rule below).

---

## Step 2 — Analyze and Select Content

Using the job description and career goals as filters:

- Write a 2-3 sentence summary. Each sentence must be short and independently scannable — no run-on sentences. The summary is a value statement, not a narrative: it should read like a tight professional hook, not a mini cover letter. Save storytelling and role-specific context for the cover letter. Write in **first person** ("I have…", "My background…", "I bring…") — never refer to the applicant by name or in the third person. Avoid em dashes (—) entirely; use commas, colons, or periods instead. Zero em dashes preferred; one at most. Do not overqualify the candidate by emphasizing "18 years of experience" when the JD is asking for 5.
- **Before making any claim about years or depth in a specific technology**, verify it against the experience entries. A language counts toward experience only in roles where it appears in that entry's Key Skills. Do not aggregate loosely — check each role.
- Select skills from `template/all-skills.md` that match or complement keywords in the job description. Preserve exact terminology from the job posting where it matches reality.
- For each experience entry, decide whether to include it:
  - Work from the last 12 years: include with the most relevant highlights.
  - Try not to cut back on the recent experience if you're not running out of the 2-page space. Unless the experiece hurts for the job description.
  - Work older than 12 years: include only if directly relevant; reduce bullet count.
  - **Do not drop an entry entirely if doing so creates a chronological gap.** Instead, reduce its bullets to the 1–2 most transferable highlights.
  - If an entry has too many bullets, keep only those most aligned with the job description and career goals.
- Keep bullet point text close to verbatim from the template unless rephrasing or extra context is necessary to improve the job fit — and only rephrase what is already true.
- Include education, certifications, and publications if relevant to the role. Always include a References line: "Available upon request."

**Do not fabricate, embellish, or hallucinate any skill, title, date, or achievement.**

---

## Step 2b — Job Match Analysis

Invoke the `score-job-match` skill, passing it: the job description text (Step 1), the loaded career profile (Step 1), and — if Step 0 found an existing manifest with a prior `job_match` block — that manifest's path, so `score-job-match` can run reconciliation against it.

It writes the full scored result to `/tmp/job-match-score.json`. If it ran reconciliation, note whether `material_rescore` came back `true` (and, if so, keep its `dimensions_needing_explanation`/`report_text` on hand) — Step 9 and Step 11 need this later, but **read `/tmp/job-match-score.json` fresh at those steps rather than recalling its contents from here.**

---

## Step 2c — Asking Salary Analysis

Invoke the `analyze-salary` skill, passing it: the job description text (Step 1), the loaded career profile (Step 1), `variable-input/salary-expectations.md`'s contents if present (also Step 1), and the `total`/`transferable_skills` values from `/tmp/job-match-score.json` (just written in Step 2b).

It writes the full result to `/tmp/salary-analysis.json`. **Read that file fresh at Step 9 and Step 11 rather than recalling its contents from here** — this step produces a report-only recommendation (it does not appear on the resume or cover letter), and nothing about it should be reconstructed from memory several steps later.

---

## Step 3 — Generate the Markdown Resume

The base name was computed in Step 0 via `scripts/base_name.py applicant-job` — reuse it, do not recompute by hand. All outputs go in the `output/` directory (create it if it does not exist).

Write the tailored resume to: `output/<base-name>.md`

**CSS class application:** pandoc preserves raw HTML, so apply `formatting.md` classes via inline HTML — not markdown headings. Use:
- `<span class="applicant-name">Name</span>` and `<span class="applicant-title">Title</span>` on the header line
- `<p class="contact-info">...</p>` for the contact line, following `blueprint.md`'s Layout section verbatim: `t:` and `e:` fields as plain text, then `[LinkedIn](url)`, `[GitHub](url)`, `[Medium](url)` as markdown links (pandoc renders these as clickable text, not raw URLs) — omit any of the three link fields not found in `contact-info.txt` (no placeholders)
- `<p class="section-header">Skills</p>` for each section header
- `<p class="section-item-header">Role, Company</p>` for each experience/education entry header, then `<p class="date-location"><span>Date - Date</span><span>Location</span></p>` on the line immediately following — no parentheses around the location text. **Use a plain hyphen (`-`) in date ranges — never an en dash (–) or em dash (—).**
- `<p><span class="job-skills-title">Key Skills:</span> <span class="job-skills">skill, skill, ...</span></p>` immediately after each experience entry header, using the Key Skills from that entry's template file verbatim
- Standard markdown list items (`-`) for bullet highlights (pandoc renders them as `<li>`)

Assemble sections in the order and structure defined in `blueprint.md`'s Layout section — that file is the single source of truth for section order (currently Summary, Skills, Experience, Education, Certifications, Publications, References). If `/match-resume-style` has customized it, follow the customized order, not the example above.

---

## Step 4 — Validate the Markdown

Check the generated markdown against the template before producing any PDF. Fail this step (and return to Step 2/3) if any of the following are true:

- [ ] Any skill, title, company, date, or achievement appears in the output that is NOT present in the template files.
- [ ] Any skill in the Skills section was sourced from an experience entry's "Key Skills" subsection rather than from `template/all-skills.md`. Skills must come exclusively from `all-skills.md`; Key Skills in experience entries are context metadata, not the canonical skills list.
- [ ] Any bullet point is materially changed beyond what is needed for relevance or grammar.
- [ ] A required section (Summary, Skills, Experience, References) is missing.
- [ ] The layout deviates from the structure defined in `blueprint.md`.

If validation fails, correct the markdown and re-run this checklist until all items pass.

---

## Step 5 — Generate the CSS File

Write the resume stylesheet to `output/resume-style.css` using the exact CSS from `formatting.md`. Do not alter the styles.

---

## Step 6 — Generate the PDF

Run the following command:

```bash
pandoc output/<base-name>.md -o output/<base-name>.pdf --pdf-engine=weasyprint -c output/resume-style.css
```

If pandoc or weasyprint is not installed, stop and tell the user:
```
Missing dependency. Install with: brew install pandoc weasyprint
```

A `WARNING: Ignored overflow-x: auto at ...` line from weasyprint is expected and harmless — it comes from pandoc's own default template CSS, not from `formatting.md` or `resume-style.css`. Do not investigate or try to fix it.

---

## Step 7 — Validate Page Count (≤ 2 pages)

Check the page count of the generated PDF:

```bash
python3 scripts/pdf_page_count.py output/<base-name>.pdf
```

This handles the `mdimport`/`mdls` retry dance (and uses `pdfinfo` directly if it happens to be installed) internally — use its stdout integer directly.

**If the PDF exceeds 2 pages**, trim content in the markdown and regenerate:
1. First pass: reduce bullets in older or least-relevant experience entries (keep the 2 strongest per role).
2. Second pass: drop the least-relevant experience entry entirely.
3. Third pass: tighten the summary to 2 sentences; reduce skills to top 15–18 keywords.
4. After each trim, repeat Steps 4, 6, and 7 until the PDF is ≤ 2 pages.

Do not trim content that is load-bearing for the job description match.

---

## Step 8 — ATS Friendliness Check

ATS systems receive the **PDF**, not the markdown. Run all checks against the rendered PDF output. Start by extracting the PDF text directly from `output/<base-name>.pdf` using native PDF extraction — do NOT use shell-based extraction (pdftotext, python subprocess, etc.).

**Structure checks — verify in both the extracted PDF text and the markdown source (must all pass):**
- [ ] Direct PDF text extraction produces non-empty, readable text from the PDF (empty or garbled output means the PDF is image-based or encrypted — FAIL).
- [ ] No tables, text boxes, or multi-column layouts in the markdown source.
- [ ] No images or embedded graphics in the markdown source.
- [ ] Section headers use plain words only: Summary, Skills, Experience, Education, Certifications, Publications, References.
- [ ] Dates use a consistent, parseable format (e.g., "October 2021 - April 2026" or "Oct 2021 - Apr 2026") with a plain hyphen (`-`), not an en dash (–) or em dash (—). No abbreviations that differ between entries.
- [ ] Job titles, company names, and locations appear on or directly adjacent to their date range — not separated by unrelated content.
- [ ] Bullet points use a plain character (•) or a hyphen (-), not custom Unicode symbols.
- [ ] The extracted PDF text contains at least one email address (format: `x@y.z`) and at least one phone number. Check the contact line.
- [ ] No employment gap exceeds 2 years between adjacent experience entries. Build `{"roles": [{"role", "start": "YYYY-MM", "end": "YYYY-MM"|"present"}, ...]}` from all included experience entries and run `python3 scripts/check_gaps.py --input <file>` (or pipe the JSON on stdin) — use its `gaps` list verbatim, do not sort or diff dates by hand. If any `gap_months` exceeds 24, FAIL and identify the specific gap (e.g., "30-month gap between Role A end Apr 2020 and Role B start Oct 2022").
- [ ] If the job posting explicitly states a required degree or certification (using language like "required", "must have", "Bachelor's required"), that credential appears in the extracted PDF text under Education or Certifications.

**Keyword checks — verify in extracted PDF text (must all pass):**
- [ ] At least 5 keywords from the job description appear verbatim (or near-verbatim) in the Skills or Summary section of the PDF text.
- [ ] The applicant's most recent job title appears in the header.

**Warnings — evaluate and record but do not block generation:**

Collect all applicable warnings; they will surface in the Step 11 report.

- ⚠ **Employment gap 6–24 months:** If any gap between adjacent experience entries is between 6 and 24 months, note it: e.g., "14-month gap between Role A (end Apr 2020) and Role B (start Jun 2021)." Not a disqualifier but visible to recruiters.
- ⚠ **Keyword distribution:** Identify the top 3–5 required skills from the job description. If any appear only in the Skills or Summary section and not in any experience bullet in the PDF text, flag each one: e.g., "\"Terraform\" appears in Skills only — not in any experience bullet."
- ⚠ **En dashes in date ranges:** If date ranges use en dashes (–) rather than plain hyphens (-), flag as advisory — legacy ATS systems may misparse them.
- ⚠ **LinkedIn URL absent:** If no LinkedIn URL is present in the contact line of the PDF text, flag it — increasingly expected; absence reduces reach-back rate.
- ⚠ **No quantified achievements:** If no bullet points in the PDF text contain a number, percentage (%), dollar amount ($), or multiplier (e.g., "2x", "3×"), flag it — LLM-era ATS systems weight evidence-backed claims more heavily.

If any FAIL check does not pass, fix the markdown, re-run Step 4 (validation), Step 6 (PDF generation), Step 7 (page count), and Step 8 until all checks pass. Warnings do not require re-generation.

---

## Step 8b — Generate Cover Letter

Write a tailored cover letter to `output/<base-name>-cover-letter.md`. The resume must be fully validated before writing the cover letter.

**Content rules:**
- Address to "Dear Hiring Manager," unless the job posting names a specific contact.
- Open with a compelling hook: the single strongest reason the applicant is the right person for this specific role. Do not open with "I am applying for…"
- Body paragraph 1: Reference 1–2 specific, verifiable experiences from the resume that directly address the role's core requirements. Tie them to the company's stated mission, product, or pain point.
- Body paragraph 2: Connect 1–2 of the applicant's career goals (from `variable-input/career-goals/`) to what this role offers — make it mutual, not just what the applicant wants.
- Closing: Express genuine enthusiasm, invite next steps, and sign off. One short paragraph.
- Total length: 3–4 paragraphs, strictly 1 page when rendered as PDF.
- Tone: confident, specific, human. No buzzwords, no filler phrases ("I am a passionate team player who thrives in…").
- Avoid repeating the same sentence template (e.g., "That [X] is the kind of [Y]…", "Not just [X], but [Y]…") more than once in the letter — reusing a construction across paragraphs is a tell that the letter is AI-generated. Vary sentence structure paragraph to paragraph.
- Voice: **first person throughout** — "I built…", "My work on…", "I am looking for…". Never refer to the applicant by name or in the third person.
- Avoid em dashes (—) throughout the letter. Restructure sentences to use commas, colons, semicolons, or periods instead. Zero em dashes preferred; one at most.

**Do not fabricate any experience, skill, or achievement not present in the template files.**

**Format the letter using the same header style as the resume, then plain markdown for the body:**
```
<p><span class="applicant-name">[Name]</span> | <span class="applicant-title">[Title]</span></p>
<p class="contact-info">t: [phone] | e: [email] | li: [linkedin url]</p>

[Today's date]

Dear Hiring Manager,

[Opening hook paragraph]

[Body paragraph 1 — specific experience → role requirement]

[Body paragraph 2 — career goals ↔ role opportunity]

[Closing paragraph]

Sincerely,
[Applicant Name]
```

Use the same CSS classes and field rules as the resume header: omit any field not in `contact-info.txt`, use `li:` for LinkedIn URLs.

Then generate the PDF:
```bash
pandoc output/<base-name>-cover-letter.md -o output/<base-name>-cover-letter.pdf --pdf-engine=weasyprint -c output/resume-style.css
```

Check the page count using the same script as Step 7:
```bash
python3 scripts/pdf_page_count.py output/<base-name>-cover-letter.pdf
```

If the cover letter exceeds 1 page, tighten the prose and regenerate until it fits.

---

## Step 9 — Write Manifest

Hash every input file:

```bash
python3 scripts/manifest_check.py hash --job-description "$ARGUMENTS"
```

Use its JSON output verbatim as the `"inputs"` field below.

For `job_match` and the two salary fields, **do not retype or reconstruct any value from memory.** Read `/tmp/job-match-score.json` (written in Step 2b) and copy its `total`/`skill_overlap`/`experience_relevance`/`seniority_match`/`transferable_skills`/`interpretation`/`checklist` fields verbatim into `job_match` below (its shape already matches this schema exactly — this is a straight copy, not a transform). Read `/tmp/salary-analysis.json` (written in Step 2c) and copy its `suggested_asking_salary` and `job_posting_salary_range` fields verbatim.

Write the result as JSON to `output/<base-name>.manifest`:
```json
{
  "generated": "<YYYY-MM-DD>",
  "output": {
    "resume_markdown": "output/<base-name>.md",
    "resume_pdf": "output/<base-name>.pdf",
    "cover_letter_markdown": "output/<base-name>-cover-letter.md",
    "cover_letter_pdf": "output/<base-name>-cover-letter.pdf"
  },
  "job_match": <copied verbatim from /tmp/job-match-score.json — total/skill_overlap/experience_relevance/seniority_match/transferable_skills/interpretation/checklist, plus formatted_report>,
  "suggested_asking_salary": "<copied verbatim from /tmp/salary-analysis.json, e.g. '$130,000 - $145,000 CAD', or null if that file found no usable data>",
  "job_posting_salary_range": {
    "range": "<copied verbatim from /tmp/salary-analysis.json, e.g. '$120,000 - $150,000 CAD', or null>",
    "source": "<copied verbatim: 'posted' | 'researched' | 'contractor-multiplier', or null>"
  },
  "inputs": {
    "<file-path>": "<sha256>",
    ...
  }
}
```
The `job_match`, `suggested_asking_salary`, and `job_posting_salary_range` fields persist the Step 2b/2c results computed earlier in this run — they are not recomputed here, just carried into the manifest so other commands (e.g. `/applied`) can read them without re-deriving. `job_posting_salary_range` is the raw anchor (what the market/posting says); `suggested_asking_salary` is the recommendation positioned within it — they are not the same number.

---

## Step 11 — Report Output

Before writing anything below, read `output/<base-name>.manifest` (just written in Step 9) and `/tmp/salary-analysis.json` (written in Step 2c). **Every value in the score and salary blocks below comes from those two files, verbatim — none of it is reconstructed from memory of Step 2b/2c.**

When all validations pass, report:

```
Resume tailored successfully.

Output files:
  Resume Markdown  : output/<base-name>.md
  Resume PDF       : output/<base-name>.pdf
  Cover Letter MD  : output/<base-name>-cover-letter.md
  Cover Letter PDF : output/<base-name>-cover-letter.pdf

Validation summary:
  ✓ No hallucinations detected
  ✓ Resume PDF page count: <N> page(s)
  ✓ Cover letter PDF page count: 1 page(s)
  ✓ ATS checks passed[, <N> warning(s) — see below]

Job match score: <manifest job_match.total>/100 — <manifest job_match.interpretation>

<manifest job_match.formatted_report, verbatim — already the four "Skill Overlap"/"Experience Relevance"/"Seniority Match"/"Transferable Skills" lines with rationale, do not rewrite or re-summarize it>
[If Step 2b's `score-job-match` invocation ran reconciliation, AND `material_rescore` was true:]

<the script's report_text verbatim, e.g.:>
⚠ Score changed since last run (was <prior total>/100 "<prior label>", now <new total>/100 "<new label>"):
  Skill Overlap       : <prior> → <new>  (<delta>)
  Experience Relevance: <prior> → <new>  (<delta>) — <your one-line explanation, only on dimensions moving 3+ points>
  Seniority Match      : <prior> → <new>  (<delta>)
  Transferable Skills : <prior> → <new>  (<delta>)

Keywords matched from job description: <list the matched keywords>
Experience entries included: <list the roles included>
Experience entries excluded: <list any roles omitted and why>

Suggested asking salary: <manifest suggested_asking_salary, verbatim> [or: "Not enough data to suggest a range — see flags below" if that field is null]
  Anchor        : </tmp/salary-analysis.json's anchor_citation, verbatim>
  Market worth  : <market_worth> (source: <market_worth_citation>) — both from /tmp/salary-analysis.json, verbatim
  Rationale     : <rationale from /tmp/salary-analysis.json, verbatim>
[If salary-expectations.md was found:]
  Applicant floor respected: <applicant_floor_respected from /tmp/salary-analysis.json>
[If /tmp/salary-analysis.json has a net_pay_comparison object:]
  Net pay comparison (<jurisdiction_label>): current $<current_net> net vs. proposed $<proposed_net> net (<share_of_raise_kept as a percent> of the raise kept after tax/CPP/EI)
[If /tmp/salary-analysis.json's flags list is non-empty:]
  ⚠ <flag 1>
  ⚠ <flag 2>
  ...
[If any ATS warnings exist:]

ATS warnings (<N>):
  ⚠ <warning 1>
  ⚠ <warning 2>
  ...
```

Omit the "ATS warnings" block entirely if there are no warnings. Replace ", <N> warning(s) — see below" in the validation summary with nothing if there are no warnings. Omit the "Applicant floor respected" line if no `salary-expectations.md` was found. Omit the "Net pay comparison" line if `/tmp/salary-analysis.json` has no `net_pay_comparison` object. Omit salary flag lines if `/tmp/salary-analysis.json`'s `flags` list is empty. Omit the "⚠ Score changed since last run" block entirely unless Step 2b's `score-job-match` invocation ran reconciliation and got `material_rescore: true`.
