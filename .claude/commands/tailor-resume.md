---
name: tailor-resume
description: Tailor the applicant's resume for a specific job description file
---

Tailor the applicant's resume for the following job description file: $ARGUMENTS

You are an expert resume crafter and career coach. Follow every step below in order. Do not skip validation steps. If any validation fails, iterate until it passes before moving on.

---

## Help Check

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

If `all_match` is `false` (or the manifest is absent), note whether the existing manifest (if any) has a `job_match` block, and its path (`output/<base-name>.manifest`) — Step 2b's Reconciliation subsection will need it later, even when the reason a rerun was triggered is unrelated to scoring (e.g. only `blueprint.md` changed). Then continue to Step 1.

---

## Step 1 — Read All Inputs

Read the following files before doing any writing:

1. `variable-input/job-descriptions/$ARGUMENTS` — the target job posting. **Use the `Read` tool directly on the file path — do NOT attempt shell-based extraction (pdftotext, python subprocess, etc.).** The Read tool handles PDFs natively; shell tools are not reliably installed.
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

Score the applicant's fit for this role across four dimensions. Be honest — over-scoring a weak match wastes the applicant's time; under-scoring a strong one undersells them.

**Do not compute or estimate a dimension score yourself.** Your job is the itemized classification below — build it, write it to a temp JSON file (e.g. `/tmp/job-match-input.json`), then run:

```bash
python3 scripts/score_job_match.py score --input /tmp/job-match-input.json
```

That command returns the actual `total`, all four sub-scores, and the `interpretation` label — use its output verbatim. If a result looks wrong given the list you built, the itemization was wrong (a bad classification, or too many/few items extracted) — fix the classification and re-run the script. Never override its output by hand.

Build this JSON payload:

```json
{
  "skill_overlap": {
    "required": [{"skill": "<from JD>", "status": "match|partial|absent", "evidence": "<citation to all-skills.md or an experience bullet, or omit if absent>"}],
    "preferred": [{"skill": "<from JD>", "status": "match|partial|absent", "evidence": "..."}]
  },
  "experience_relevance": {
    "items": [{"item": "<a specific JD responsibility/domain/stack element>", "status": "direct|adjacent|absent", "evidence": "<citation to a specific template/experience/*.md entry>"}]
  },
  "seniority_match": {
    "title_level": {"score": <0-8>, "note": "<role's expected level vs. applicant's title history>"},
    "scope": {"score": <0-8>, "note": "<ownership/cross-team impact/mentorship evidence>"},
    "years": {"score": <0-4>, "note": "<years of relevant experience vs. what the role expects>"}
  },
  "transferable_skills": {
    "items": [{"item": "<adjacent tech, domain knowledge, process leadership, unique differentiator>", "score": <0-5>, "evidence": "<citation>"}]
  }
}
```

Guidance for building each section (the judgment work — this is what you're actually doing):

### Skill Overlap
- List **every** required skill/qualification from the job posting as its own `required` item, and every preferred/bonus skill as its own `preferred` item. Check each against `template/all-skills.md` and the experience entries.
- `match` = clearly demonstrated. `partial` = a credible near-match (e.g. "XCTest" when the applicant has "Selenium" and iOS experience) — cite why it's a reasonable partial credit, not a stretch. `absent` = no evidence.
- If the JD states no preferred/bonus skills at all, leave `preferred` as an empty list — the script awards full credit for that case.

### Experience Relevance
- Extract 4–8 specific responsibility/domain/stack items from the JD (not every bullet — the load-bearing ones). For each, classify how directly the applicant's work history maps to it: `direct` (same domain and stack, recent), `adjacent` (transferable but not a clean match), `absent` (no real evidence). Cite the specific `template/experience/*.md` entry backing each `direct` or `adjacent` call.

### Seniority Match
- `title_level` (0–8): how the role's expected level (IC, Senior, Staff, Principal, etc.) compares to the applicant's title history. `scope` (0–8): ownership, cross-team impact, mentorship evidence from the experience entries. `years` (0–4): years of relevant experience vs. what the role expects. Note the reasoning for each — these notes are what make a future rescore auditable.

### Transferable Skills
- Identify up to 5 items that aren't a direct requirement match but meaningfully strengthen the application — adjacent technologies, domain knowledge, process leadership, or a differentiator addressing an unstated need. Score each 0–5 based on strength/specificity; cite the evidence.

### Interpretation

Use the `interpretation` label from `scripts/score_job_match.py score`'s output verbatim — it's derived from `INTERPRETATION_BANDS`, the single source of truth for the band boundaries. Do not restate or eyeball the bands here, especially near a boundary.

### Reconciliation

If Step 0 noted an existing manifest with a prior `job_match` block, run:

```bash
python3 scripts/score_job_match.py compare --new <path-to-this-run's-score-output.json> --prior output/<base-name>.manifest
```

(Save this run's `score` output to a file first if you haven't already, so `--new` can point at it.)

If the result's `material_rescore` is `true` (total moved 8+ points, or the interpretation label changed):
1. Show the script's before/after table (`report_text`) to the user in Step 11 (see that step's report block).
2. For each dimension listed in `dimensions_needing_explanation` (moved 3+ points), state a specific one-line reason: either a genuine input change (cite the changed file/content), or — if the inputs are unchanged — an honest note naming which checklist item(s) were classified differently this time versus what the prior manifest's `job_match.checklist` recorded (if present).

If `material_rescore` is `false`, no reconciliation note is needed in Step 11 — proceed normally. If Step 0 found no prior manifest, skip this subsection entirely.

---

## Step 2c — Asking Salary Analysis

This step produces a report-only recommendation — it does not appear on the resume or cover letter. Never fabricate a precise, unsourced number; every figure must trace back to either the job posting, a cited web search, or the applicant's own stated expectations.

1. **Determine the reporting currency.** Never assume USD or any other currency by default — derive it:
   - If `variable-input/salary-expectations.md` has a `Currency` field, that's the applicant's currency for all figures the applicant side of this analysis.
   - Otherwise, infer the applicant's local currency from their location (`contact-info.txt`'s location if stated, otherwise infer from the job posting's stated location/remote policy and flag the assumption).
   - Use the job posting's own stated currency for the job's compensation anchor when it states one explicitly (look for an explicit code like USD/CAD/EUR, or contextual clues — company HQ, job location, "USD"/"CAD" in the text — since a bare "$" is ambiguous).
   - Every dollar figure recorded in this step and reported in Step 11 must carry an explicit currency code (e.g., "$130,000 CAD"), never a bare "$".
   - If the job's anchor currency differs from the applicant's local currency, flag it (see step 5) rather than silently converting — do not fabricate an exchange-rate conversion.

2. **Read the applicant's floor, if provided.** If `variable-input/salary-expectations.md` exists, note the current salary, minimum acceptable, and/or target range (in the currency from step 1). This is a hard floor: the suggested range's low end must never be recommended below the applicant's stated minimum. If the file doesn't exist, there is no floor to enforce — proceed on computed value alone.

3. **Establish the applicant's general market worth.** Independent of this specific job posting, determine what a candidate with this applicant's title, years of experience, seniority (reuse the Seniority Match reasoning from Step 2b), and core skills typically commands. Use `WebSearch` to find current data (prefer sources like levels.fyi, Glassdoor, Payscale, Bureau of Labor Statistics, or recent salary-survey aggregators; prefer results from the last ~2 years) for the applicant's location. Record this as the applicant's market-worth range, labeled with its currency code, with a cited source.

4. **Establish the job's compensation anchor.**
   - If the job posting states a salary or range explicitly, use it verbatim (currency and all) as the primary anchor — this is always preferred over research.
   - If it doesn't, use `WebSearch` to find a market range for this specific title/level/location/company as posted, using the same sourcing standard as step 3, in the currency established in step 1. Label this anchor as "researched" (not "posted") in the report so the applicant knows it isn't from the employer.

5. **Position the ask within the anchor range.** Do not hand-pick a percentage yourself — run:
   ```bash
   python3 scripts/score_job_match.py salary-position --anchor-low <low> --anchor-high <high> \
     --total-score <Step 2b total> --transferable-score <Step 2b Transferable Skills sub-score> \
     [--market-worth-high <applicant's market-worth range high, if step 3 found one>]
   ```
   This applies the same fixed bands the old prose described (85–100 → top of range, or up to 10% above it if market-worth-high exceeds the anchor high and transferable-score is strong; 70–84 → upper-middle; 55–69 → middle; under 55 → lower-middle to low end) — use its `suggested_low`/`suggested_high` output verbatim.
   - Do not inflate the number to force it up to the applicant's market worth if the job's anchor range is simply lower across the board — surface that as a flag instead (next step), don't mask it.
   - If a floor from `salary-expectations.md` exists and the script's `suggested_low` falls below it, use the floor as the suggested low end instead and flag the conflict.
   - If the job anchor and the applicant's market-worth figure ended up in different currencies (step 1 flagged a mismatch), position within the job anchor's own currency and range — don't pass a market-worth-high from a different currency into the script.

6. **Flag mismatches explicitly — do not smooth them over:**
   - ⚠ **Pay cut risk:** the job's anchor range sits meaningfully (~10%+) below the applicant's market-worth range (only compare when both are in the same currency, or note that a currency difference makes the comparison approximate). State it plainly, especially if paired with a borderline Step 2b score.
   - ⚠ **Below stated floor:** the job's anchor range can't support the minimum in `salary-expectations.md`.
   - ⚠ **No salary data found:** neither the posting nor web search produced usable compensation data (ambiguous location, obscure title, etc.) — say so rather than inventing a number, and omit the suggested range from Step 11.
   - ⚠ **Location assumed:** the applicant's location wasn't stated in `contact-info.txt` and had to be inferred.
   - ⚠ **Currency mismatch:** the job's anchor currency differs from the applicant's local currency — note both currencies explicitly and that the comparison is approximate absent a real conversion.

7. Record: the suggested asking range (with currency code), the anchor source (posted vs. researched, with citation), the applicant's market-worth range (with currency code and citation), the positioning rationale, and any flags. These are reported in Step 11 — do not write them into the resume or cover letter.

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

ATS systems receive the **PDF**, not the markdown. Run all checks against the rendered PDF output. Start by extracting the PDF text using the `Read` tool directly on `output/<base-name>.pdf` — the Read tool handles PDFs natively; do NOT use shell-based extraction (pdftotext, python subprocess, etc.).

**Structure checks — verify in both the extracted PDF text and the markdown source (must all pass):**
- [ ] The `Read` tool produces non-empty, readable text from the PDF (empty or garbled output means the PDF is image-based or encrypted — FAIL).
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

Use its JSON output verbatim as the `"inputs"` field below. Write the result as JSON to `output/<base-name>.manifest`:
```json
{
  "generated": "<YYYY-MM-DD>",
  "output": {
    "resume_markdown": "output/<base-name>.md",
    "resume_pdf": "output/<base-name>.pdf",
    "cover_letter_markdown": "output/<base-name>-cover-letter.md",
    "cover_letter_pdf": "output/<base-name>-cover-letter.pdf"
  },
  "job_match": {
    "total": <Step 2b total score, integer, from score_job_match.py's output>,
    "skill_overlap": <Step 2b Skill Overlap score>,
    "experience_relevance": <Step 2b Experience Relevance score>,
    "seniority_match": <Step 2b Seniority Match score>,
    "transferable_skills": <Step 2b Transferable Skills score>,
    "interpretation": "<Step 2b interpretation label, e.g. 'Strong match'>",
    "checklist": <the "checklist" object echoed back by `score_job_match.py score` — the full itemized classification (skill_overlap/experience_relevance/seniority_match/transferable_skills sub-objects with every item's status and citation), carried verbatim so a future rescore's Reconciliation subsection can diff against exactly what was classified this run>
  },
  "suggested_asking_salary": "<Step 2c suggested asking range with currency code, e.g. '$130,000 - $145,000 CAD', or null if Step 2c found no usable data>",
  "job_posting_salary_range": {
    "range": "<Step 2c's compensation anchor from its step 4, e.g. '$120,000 - $150,000 CAD', or null>",
    "source": "<'posted' if the job listing itself stated it, 'researched' if Step 2c had to look it up, or null>"
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

Job match score: <total>/100 — <interpretation label>

  Skill Overlap      : <score>/30 — <one-line rationale>
  Experience Relevance: <score>/30 — <one-line rationale>
  Seniority Match    : <score>/20 — <one-line rationale>
  Transferable Skills: <score>/20 — <one-line rationale>
[If Step 2b's Reconciliation subsection found a prior manifest and ran `compare`, AND `material_rescore` was true:]

<the script's report_text verbatim, e.g.:>
⚠ Score changed since last run (was <prior total>/100 "<prior label>", now <new total>/100 "<new label>"):
  Skill Overlap       : <prior> → <new>  (<delta>)
  Experience Relevance: <prior> → <new>  (<delta>) — <your one-line explanation, only on dimensions moving 3+ points>
  Seniority Match      : <prior> → <new>  (<delta>)
  Transferable Skills : <prior> → <new>  (<delta>)

Keywords matched from job description: <list the matched keywords>
Experience entries included: <list the roles included>
Experience entries excluded: <list any roles omitted and why>

Suggested asking salary: <range with currency code from Step 2c, e.g. "$130,000 - $145,000 CAD"> [or: "Not enough data to suggest a range — see flags below" if step 2c found no usable data]
  Anchor        : <"Posted range: $X - $Y <currency>" or "Researched range for <title/level/location>: $X - $Y <currency> (source: <cite>)">
  Market worth  : <applicant's general market-worth range, with currency code> (source: <cite>)
  Rationale     : <one line tying the position within the range to the fit score and transferable skills>
[If salary-expectations.md was found:]
  Applicant floor respected: <minimum from variable-input/salary-expectations.md>
[If any salary flags exist:]
  ⚠ <salary flag 1>
  ⚠ <salary flag 2>
  ...
[If any ATS warnings exist:]

ATS warnings (<N>):
  ⚠ <warning 1>
  ⚠ <warning 2>
  ...
```

Omit the "ATS warnings" block entirely if there are no warnings. Replace ", <N> warning(s) — see below" in the validation summary with nothing if there are no warnings. Omit the "Applicant floor respected" line if no `salary-expectations.md` was found. Omit salary flag lines if step 2c raised none. Omit the "⚠ Score changed since last run" block entirely unless Step 2b's Reconciliation subsection ran `compare` and got `material_rescore: true`.
