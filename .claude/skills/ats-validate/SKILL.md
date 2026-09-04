---
name: ats-validate
description: Score a generated resume PDF against ATS screening criteria with a detailed findings report
---

Perform a deep ATS validation of the resume: $ARGUMENTS

*(In Claude Code, `$ARGUMENTS` is what follows `/ats-validate` in the slash palette. In agents without slash syntax, treat this as the resume base name or PDF path the user named in their request.)*

You are evaluating how well this resume will perform against Applicant Tracking Systems — both legacy keyword-matchers and modern LLM-based parsers. Be rigorous and honest. Over-scoring helps no one.

---

## Step 1 — Locate Files

Resolve the PDF path from the argument:
- If `$ARGUMENTS` ends in `.pdf`, use it as-is (try it as a relative path from the project root, or under `output/` if not found).
- Otherwise, treat it as a base name and look for `output/$ARGUMENTS.pdf`.

Derive the manifest path by replacing the `.pdf` extension with `.manifest` (same directory).

If the PDF does not exist, stop and tell the user:
```
File not found: <resolved path>
Usage: /ats-validate <base-name>  or  /ats-validate output/<base-name>.pdf
```

---

## Step 2 — Extract PDF Text

Read the PDF directly using native PDF extraction — do NOT use shell-based extraction (pdftotext, python subprocess, etc.).

Capture the full extracted text. If the output is empty or contains only whitespace and non-readable characters, record **Parseability = 0/25** and skip to Step 6 with the note: "PDF text extraction failed — PDF may be image-based or encrypted."

---

## Step 3 — Locate the Job Description

Read the manifest file (if it exists) and find the key under `"inputs"` whose path begins with `variable-input/job-descriptions/`. That is the job description file. Read it directly (it may be a PDF, markdown, or text file).

If no manifest exists, or no job description key is found in the manifest, ask the user:
```
No manifest found for this resume. Which job description should I compare against?
Provide the filename from variable-input/job-descriptions/ (e.g., Acme_Corp_Role.pdf)
```

Once the job description is read, extract:
- A ranked list of **required skills/qualifications** (those marked "required", "must have", "you must", or listed in mandatory sections)
- A ranked list of **preferred skills** (those marked "preferred", "nice to have", "bonus", "ideally")
- The **top 10 keywords** by prominence (frequency × position weight — title and requirements sections count more)

---

## Step 4 — Run Scored Checks

Evaluate each category against the extracted PDF text and the job description analysis. Start each category at full points and deduct per the criteria below. No category goes below 0.

---

### Category A: Parseability (25 pts)

Start at 25.

| Check | Deduct |
|---|---|
| PDF text extraction is empty or garbled | –25 (FAIL entire category; mark all sub-checks N/A) |
| Text reads out of order / columns appear interleaved (words from unrelated sections appear mid-line) | –8 |
| Any section header is not a plain recognized word (e.g., "Professional Journey" instead of "Experience", "Core Competencies" instead of "Skills") | –3 per header, max –9 |
| Non-ASCII characters appear at the start of bullet lines or within section header text (excluding bullet character • itself) | –3 |

**Notes to record:**
- List of detected section headers and whether each is standard.
- Any non-ASCII characters found and their locations.

---

### Category B: Keyword Coverage (35 pts)

Start at 35.

| Check | Deduct |
|---|---|
| Fewer than 5 of the top 10 job description keywords appear verbatim or near-verbatim in the Skills or Summary section of the PDF | –3 per missing keyword below 5, max –15 |
| Any of the top 3 **required** skills does not appear in any experience bullet in the PDF | –5 per skill, max –15 |
| The single highest-frequency required keyword appears only once in the entire PDF | –5 |

**Notes to record:**
- List each of the top 10 job description keywords and whether it was found (location: Skills, Summary, or experience bullets).
- Explicitly call out any required skill absent entirely from the PDF.

---

### Category C: Contact Completeness (15 pts)

Start at 15.

| Check | Deduct |
|---|---|
| No email address found in PDF text (pattern: `x@y.z`) | –8 |
| No phone number found in PDF text | –4 |
| No LinkedIn URL found in PDF text (pattern: `linkedin.com/in/`) | –3 |

---

### Category D: Chronological Integrity (15 pts)

Start at 15.

Extract all date ranges from the experience entries in the PDF text into `{"roles": [{"role", "start": "YYYY-MM", "end": "YYYY-MM"|"present"}, ...]}` and run `python3 scripts/check_gaps.py --input <file>` (or pipe the JSON on stdin). Use its `gaps` list (each with `gap_months`, `before_role`, `after_role`) verbatim — do not sort or diff dates by hand.

| Check | Deduct |
|---|---|
| Mixed date formats across entries (e.g., some spelled out "January 2021", others abbreviated "Jan 2021", others numeric "01/2021") | –3 |
| Any employment gap exceeds 24 months | –8 (apply once even if multiple gaps; note all of them) |
| Any employment gap is between 6 and 24 months | –2 per gap, max –4 |
| The most recent role's end date is not "Present", "Ongoing", "Current", or equivalent, yet appears to be the applicant's current role (infer from context) | –2 |

**Notes to record:**
- Full chronological list of experience entries with their date ranges and computed gaps.

---

### Category E: Content Quality (10 pts)

Start at 10.

| Check | Deduct |
|---|---|
| The applicant's most recent job title does not appear in the header/name line of the PDF | –4 |
| No bullet points contain a quantified achievement (a digit, percentage %, dollar sign $, or multiplier like "2x" or "3×") | –4 |
| No Summary section is present | –2 |

---

## Step 5 — Compute Total and Interpret

Sum all five category scores. Clamp to [0, 100].

| Score | Rating |
|---|---|
| 90–100 | Exceptional — top 10%; will pass virtually all ATS systems |
| 80–89 | Strong — top 25%; passes most systems with minor gaps |
| 70–79 | Good — top 40%; one or two categories to strengthen |
| 60–69 | Average — several gaps; competitive resumes will rank ahead |
| 50–59 | Below average — meaningful rework needed |
| < 50 | Poor — likely filtered out; significant issues to address |

---

## Step 6 — Report

Output the following report:

```
ATS Validation Report
  Resume  : <pdf-path>
  Job     : <job-description-file>
  Date    : <today's date>

Overall score: <total>/100 — <rating>

  Parseability           : <score>/25  <✓ or ⚠>
  Keyword Coverage       : <score>/35  <✓ or ⚠>
  Contact Completeness   : <score>/15  <✓ or ⚠>
  Chronological Integrity: <score>/15  <✓ or ⚠>
  Content Quality        : <score>/10  <✓ or ⚠>

--- Keyword Coverage Detail ---
  Top 10 job description keywords:
    ✓ <keyword> — found in Skills / Summary / experience bullets
    ✗ <keyword> — NOT FOUND in PDF
    ...

  Required skills distribution:
    ✓ <skill> — present in experience bullets
    ⚠ <skill> — Skills section only, not in experience bullets
    ✗ <skill> — ABSENT from PDF entirely
    ...

--- Chronological Detail ---
  <Role>, <Company>    <start> – <end>
  <Role>, <Company>    <start> – <end>    [gap: <N> months from prior role]
  ...

--- Findings ---
  [List every deduction taken, one line each, formatted as:]
  ⚠ <Category>: <what was found and why points were deducted>

--- Recommendations ---
  [For each ⚠ finding, one actionable recommendation. Number them. If a finding
   is not actionable without fabricating content (e.g., the applicant genuinely
   lacks a required skill), say so explicitly rather than suggesting they add it.]

  Estimated score after addressing recommendations: <N>/100 (<rating>)
```

Use ✓ for a category with full marks; ⚠ for any category with deductions. If there are no findings, omit the Findings and Recommendations sections and replace with:

```
  ✓ No findings — this resume is well-optimized for ATS screening.
```
