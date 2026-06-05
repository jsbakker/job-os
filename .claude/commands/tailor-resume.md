---
name: tailor-resume
description: Tailor the applicant's resume for a specific job description file
---

Tailor the applicant's resume for the following job description file: $ARGUMENTS

You are an expert resume crafter and career coach. Follow every step below in order. Do not skip validation steps. If any validation fails, iterate until it passes before moving on.

---

## Step 0 — Stale Check

Derive the output base name from the applicant's name and the job description filename stem (same rule as Step 3). Check whether `output/<base-name>.manifest` exists.

If it does, rehash every file listed under `"inputs"` in the manifest:

```bash
shasum -a 256 blueprint.md formatting.md \
  template/contact-info.txt template/all-skills.md \
  template/certifications.md template/education.md template/publications.md \
  template/experience/*.md \
  variable-input/career-goals/*.md \
  "variable-input/job-descriptions/$ARGUMENTS"
```

Compare each hash to the manifest. If **all hashes match**, check whether the cover letter files also exist:

```bash
ls output/<base-name>-cover-letter.md output/<base-name>-cover-letter.pdf 2>/dev/null
```

- If all hashes match **and** both cover letter files exist — skip to Step 11 and report:
  ```
  Output is already up to date — no inputs have changed.
    Resume Markdown  : output/<base-name>.md
    Resume PDF       : output/<base-name>.pdf
    Cover Letter MD  : output/<base-name>-cover-letter.md
    Cover Letter PDF : output/<base-name>-cover-letter.pdf
  ```
- If all hashes match **but** cover letter files are missing — skip to Step 8b to generate the cover letter only, then update the manifest and report.

If **any hash differs** (or the manifest is absent), continue to Step 1.

---

## Step 1 — Read All Inputs

Read the following files before doing any writing:

1. `variable-input/job-descriptions/$ARGUMENTS` — the target job posting
2. All files under `variable-input/career-goals/` — the applicant's career intentions
3. All files recursively under `template/` — the applicant's full career data
4. `blueprint.md` — assembly rules, layout, and constraints
5. `formatting.md` — CSS class mapping and visual styles

Extract from the template:
- Applicant name, title, phone, email, and web/LinkedIn from `template/contact-info.txt`
- Full skills list (`template/all-skills.md`)
- All experience entries, noting date ranges from filenames (`YYYY-MM_YYYY-MM.md`)
- Education, certifications, publications

---

## Step 2 — Analyze and Select Content

Using the job description and career goals as filters:

- Write a 2–4 sentence summary that positions the applicant for this specific role. Avoid em dashes (—) entirely in the summary; use commas, colons, or periods to restructure instead. Zero em dashes preferred; one at most.
- Select skills from `template/all-skills.md` that match or complement keywords in the job description. Preserve exact terminology from the job posting where it matches reality.
- For each experience entry, decide whether to include it:
  - Work from the last 10 years: include with the most relevant highlights.
  - Try not to cut back on the recent experience if you're not running out of the 2-page space. Unless the experiece hurts for the job description.
  - Work older than 10 years: include only if directly relevant; reduce bullet count.
  - **Do not drop an entry entirely if doing so creates a chronological gap.** Instead, reduce its bullets to the 1–2 most transferable highlights.
  - If an entry has too many bullets, keep only those most aligned with the job description and career goals.
- Keep bullet point text verbatim from the template unless rephrasing is necessary to improve fit — and only rephrase what is already true.
- Include education, certifications, and publications if relevant to the role. Always include a References line: "Available upon request."

**Do not fabricate, embellish, or hallucinate any skill, title, date, or achievement.**

---

## Step 2b — Job Match Analysis

Score the applicant's fit for this role across four dimensions. Be honest — over-scoring a weak match wastes the applicant's time; under-scoring a strong one undersells them.

Record each dimension score and rationale. These will be reported in Step 11.

### Skill Overlap (0–30 points)
- List each required skill or qualification from the job posting and check whether it appears in `template/all-skills.md` or is demonstrated across the experience entries.
- Required skills that match: up to 20 pts (proportional to coverage).
- Preferred/bonus skills that match: up to 10 pts (proportional to coverage).
- Partial credit for near-matches (e.g., "XCTest" when the applicant has "Selenium" and iOS experience).

### Experience Relevance (0–30 points)
- How directly does the applicant's work history map to the role's responsibilities, domain, and technology stack?
- 25–30: Primary role or multiple recent roles are in the same domain and stack.
- 15–24: Significant overlap in domain or stack, with some gaps.
- 8–14: Adjacent domain; meaningful transferable work but notable gaps.
- 0–7: Tangential at best; role is a significant reach.

### Seniority Match (0–20 points)
- Compare the role's expected level (IC, Senior, Staff, Principal, etc.) to the applicant's demonstrated level based on title history, scope of ownership, cross-team impact, and mentorship.
- 17–20: Level is a direct match or one step below (room to grow).
- 10–16: Applicant is two levels below or one level above (overqualified).
- 0–9: Significant mismatch in either direction.

### Transferable Skills (0–20 points)
- Identify skills or experiences that aren't a direct match but meaningfully strengthen the application — adjacent technologies, domain knowledge, process leadership, or unique differentiators that address an unstated need.
- Score based on strength and specificity of the transferable value.

### Interpretation
- 85–100: Exceptional match — tailor hard and apply with confidence.
- 70–84: Strong match — a few gaps; cover letter should address them.
- 55–69: Solid match with notable gaps — worth applying; be transparent about growth areas.
- 40–54: Stretch role — apply only if genuinely interested; cover letter must compensate.
- Under 40: Reach application — significant gaps; apply selectively.

---

## Step 3 — Generate the Markdown Resume

Derive an output base name from the applicant's name and the job description filename (e.g., `jeffrey-bakker-<job-file-stem>`). All outputs go in the `output/` directory (create it if it does not exist).

Write the tailored resume to: `output/<base-name>.md`

**CSS class application:** pandoc preserves raw HTML, so apply `formatting.md` classes via inline HTML — not markdown headings. Use:
- `<span class="applicant-name">Name</span>` and `<span class="applicant-title">Title</span>` on the header line
- `<p class="contact-info">...</p>` for the contact line — omit any field not found in `contact-info.txt` (no placeholders); if the web link is a LinkedIn URL (`linkedin.com`), label it `li:` instead of `w:`
- `<p class="section-header">Skills</p>` for each section header
- `<p class="section-item-header">Role, Company</p>` for each experience/education entry header, then `<p>Date – Date (Location)</p>` on the line immediately following
- `<p><span class="job-skills-title">Key Skills:</span> <span class="job-skills">skill, skill, ...</span></p>` immediately after each experience entry header, using the Key Skills from that entry's template file verbatim
- Standard markdown list items (`-`) for bullet highlights (pandoc renders them as `<li>`)

Follow the layout defined in `blueprint.md`:
```
{applicant-name} | {applicant-title}
t: {phone} | e: {email} | w: {web}

Summary
{summary-paragraph}

Skills
{relevant skills, comma-separated or grouped}

Experience
{section-item-header} ({location}): {date-range}
• {highlight}
• {highlight}
[repeat per included role]

Education
{section-item-header} ({location}): {date-range}
• {highlight}

Certifications
[if applicable]

Publications
[if applicable]

References
Available upon request.
```

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

---

## Step 7 — Validate Page Count (≤ 2 pages)

Check the page count of the generated PDF:

```bash
pdfinfo output/<base-name>.pdf | grep "Pages:"
```

If `pdfinfo` is unavailable (common on macOS), use:
```bash
mdls -name kMDItemNumberOfPages output/<base-name>.pdf
```

**If the PDF exceeds 2 pages**, trim content in the markdown and regenerate:
1. First pass: reduce bullets in older or least-relevant experience entries (keep the 2 strongest per role).
2. Second pass: drop the least-relevant experience entry entirely.
3. Third pass: tighten the summary to 2 sentences; reduce skills to top 15–18 keywords.
4. After each trim, repeat Steps 4, 6, and 7 until the PDF is ≤ 2 pages.

Do not trim content that is load-bearing for the job description match.

---

## Step 8 — ATS Friendliness Check

Inspect the generated `output/<base-name>.md` for each of the following. Fix any failures and regenerate the PDF.

**Structure checks (must all pass):**
- [ ] No tables, text boxes, or multi-column layouts.
- [ ] No images or embedded graphics.
- [ ] Section headers use plain words: Summary, Skills, Experience, Education, Certifications, Publications, References.
- [ ] Dates use a consistent, parseable format (e.g., "October 2021 – April 2026" or "Oct 2021 – Apr 2026"). No abbreviations that differ between entries.
- [ ] Job titles, company names, and locations appear on or directly adjacent to their date range — not separated by unrelated content.
- [ ] Bullet points use a plain character (•) or a hyphen (-), not custom Unicode symbols.

**Keyword checks (must all pass):**
- [ ] At least 5 keywords from the job description appear verbatim (or near-verbatim) in the Skills or Summary section.
- [ ] The applicant's most recent job title appears in the header.

If any check fails, fix the markdown, re-run Step 4 (validation), Step 6 (PDF generation), Step 7 (page count), and Step 8 until all checks pass.

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

Check the page count:
```bash
mdls -name kMDItemNumberOfPages output/<base-name>-cover-letter.pdf
```

If the cover letter exceeds 1 page, tighten the prose and regenerate until it fits.

---

## Step 9 — Write Manifest

Hash every input file and write `output/<base-name>.manifest`:

```bash
shasum -a 256 blueprint.md formatting.md \
  template/contact-info.txt template/all-skills.md \
  template/certifications.md template/education.md template/publications.md \
  template/experience/*.md \
  variable-input/career-goals/*.md \
  "variable-input/job-descriptions/$ARGUMENTS"
```

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
  "inputs": {
    "<file-path>": "<sha256>",
    ...
  }
}
```

---

## Step 11 — Report Output

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
  ✓ ATS checks passed

Job match score: <total>/100 — <interpretation label>

  Skill Overlap      : <score>/30 — <one-line rationale>
  Experience Relevance: <score>/30 — <one-line rationale>
  Seniority Match    : <score>/20 — <one-line rationale>
  Transferable Skills: <score>/20 — <one-line rationale>

Keywords matched from job description: <list the matched keywords>
Experience entries included: <list the roles included>
Experience entries excluded: <list any roles omitted and why>
```
