---
name: prep-interview
description: Produce genuine interview-prep guidance (skills to brush up on, experience to highlight) tailored to the applicant's current interview stage for a specific job
---

Prepare interview guidance for the following job: $ARGUMENTS

The **first whitespace-separated token** of the argument above is the job description filename (resolved against `variable-input/job-descriptions/`, same convention as `/tailor-resume`, `/applied`, and `/update-status`). **Everything after it** is an optional stage override (e.g. "coding exercise", "onsite panel") — if present, it always wins over any stage detected from the tracking log.

You are a career coach, not a script-writer. This command produces genuine, honest guidance grounded entirely in the applicant's real work history — never a cheat sheet of answers to memorize. Follow every step below in order.

---

## Help Check

If `$ARGUMENTS`, trimmed of whitespace, equals `help` (case-insensitive) — and only in that exact case, not as part of a real filename — print the block below and stop. Do not run any other step.

```
/prep-interview — Analyzes the job description and your full chronological work history to produce genuine interview-prep guidance: skills to brush up on and experience to highlight, tailored to your current interview stage. Not a cheat sheet — no sample answers, no scripts.

Usage:
  /prep-interview <job-description-file> [stage-override]

What it does:
  - Looks up the job's tracking row and reads its full application_status to find your interview stage: prefers a future-dated stage you've already logged via /update-status, otherwise predicts the likely next stage and says so explicitly
  - Reads your complete template/ history (including Side Notes, not just resume-safe Highlights) plus the job description and career goals
  - Produces a genuine gap analysis (what to study, weighted by what this stage actually tests) and a list of real stories to have ready, clearly labeled where content isn't on your actual resume
  - Writes output/<base-name>-interview-prep.md

Gotchas:
  - Fails fast with no output if the application is already closed ("Not Selected", "Position Filled", etc.) or has an "Offer Received" status — prep isn't the relevant next step either way
  - Stage detection is a best-effort guess when nothing's logged yet — always states which stage it targeted and why, so you can correct it
  - Never fabricates a skill, story, or company detail not already grounded in template/ or a live search result

Examples:
  /prep-interview Acme-Corp-Staff-Software-Engineer.md
  /prep-interview Acme-Corp-Staff-Software-Engineer.md coding exercise
```

---

## Step 1 — Resolve the Job Description + Locate the Tracking Row

Read `variable-input/job-descriptions/<filename>`. Extract company, position title, req/job ID, and (uncommon but check) any explicit description of the interview process/stages the posting itself states.

Derive `<base-name>` using the identical normalization rule embedded in `tailor-resume.md` Step 0. Locate the matching row in `tracking/applications.ndjson` using the same unified multi-signal lookup `update-status.md` Step 2 uses (`resume_file`/`cover_letter_file` containing `<base-name>`, `job_id` match, or company+title match, deduped). If more than one row matches, ask which one, same as `/update-status`.

**Unlike `/update-status`, a zero-match result here is not an error** — it just means no interview is scheduled or logged yet. Continue to Step 2 with no row; Step 3 will fall back to general early-stage prep.

---

## Step 2 — Fail-Fast Check

If a tracking row was found, read its full `application_status` string and check whether this application is already resolved:

- **Closed or rejected** ("Not Selected", "Position Filled", "Position Closed", "Rejected", "Withdrawn", or equivalent, as the most recent/current state): stop immediately. Report that this application appears closed and interview prep isn't applicable. Do not write an output file.
- **Offer Received** (or equivalent): stop immediately. Report that an offer is already on the table, so prep isn't the relevant next step here (salary/negotiation is a separate conversation — see `/tailor-resume`'s Step 2c analysis if that's what's needed). Do not write an output file.
- Otherwise, continue to Step 3.

---

## Step 3 — Determine and Confirm the Target Stage

Work through this priority order and stop at the first that applies:

1. **Explicit override** — if `$ARGUMENTS` included stage text beyond the filename, use it directly.
2. **Future-dated logged stage** — scan the row's `application_status` for a stage segment whose parenthetical date is *after* today (e.g. "Technical screen (Aug 26)" logged ahead of time via `/update-status`). If found, target that stage directly.
3. **Prediction** — if no future-dated stage exists, predict the likely next stage from (a) the most recent *past* stage already logged (e.g. a completed "Screening interview" with nothing after it typically precedes a technical round) and (b) any interview-process description the job posting itself stated (from Step 1). Label this explicitly as a prediction, not a fact.
4. **No signal at all** — no tracking row, or `application_status` is just "Applied"/null: general early-stage prep (company/role research, narrative framing) rather than forcing stage-specific coaching that doesn't apply yet.

**State which path was used and what stage was targeted before generating any content** — e.g. "Using your logged upcoming stage: Technical screen (Aug 26)" or "No upcoming stage logged — predicting Technical interview as the likely next step after your completed screening call. Let me know if that's wrong." This matters most for path 3, since a prediction is inherently uncertain.

---

## Step 4 — Read Full Inputs

Read, in full:
- The job description (already read in Step 1)
- **All** of `template/experience/*.md` — including the `# Side Notes (for context)` section of each entry. `/tailor-resume` is forbidden from using Side Notes as resume content, but this command explicitly may use them as spoken-conversation material (see Step 6).
- `template/all-skills.md`
- All `variable-input/career-goals/*.md` (flag and skip any clearly non-literal/joke file, same as `/learn-preferences` does)
- If `output/<base-name>.manifest` exists, its `job_match` block — **as optional background color only**. It answers "does the resume match this JD," not "what should this candidate study or highlight for this stage" — mention it in passing if relevant, but the gap analysis in Step 5 is always computed fresh against the full experience data (which the resume rubric never even looked at, since it excludes Side Notes).

---

## Step 5 — Skill Gap Analysis

Compare the job description's requirements against what the applicant can actually, honestly demonstrate (from `all-skills.md` + experience Highlights + Side Notes for depth/recency context), weighted by what the **target stage** from Step 3 actually tests:
- Coding exercise / technical assessment: specific languages, algorithms, tooling likely to come up.
- Screening call: much less deep technical recall, much more narrative clarity and culture/role fit.
- Technical/onsite/panel interview: system-design depth, behavioral stories, cross-team impact.
- General/early-stage: broad readiness across the above, since the specific format isn't known yet.

Organize by genuine urgency:
- **Real gap, no coverage** — be honest about it, and give guidance on how to address it if asked directly (transferable-skill framing), never implying expertise that isn't there.
- **Rusty but real** — experience exists but hasn't been exercised recently; name what to refresh.
- **Solid already** — brief acknowledgment, not the focus.

**Never fabricate a skill or depth not evidenced in `template/`.**

---

## Step 6 — Experience & Story Selection

Identify specific, real stories from Highlights and Side Notes that map to what the job description emphasizes and to the applicant's stated career-goals narrative (why this role, why now). **Any material sourced from Side Notes must be explicitly tagged**, e.g. "*(background only — not on your resume)*", so the applicant never mistakes it for something already on record with whatever resume copy the interviewer has.

---

## Step 7 — Stage Context (optional, best-effort `WebSearch`)

Research what this specific stage at this specific company tends to look like: format, likely interviewer/panel structure, recent public engineering content. This is a clearly secondary subsection that feeds *only* the "What to Expect" framing — it must never influence the skill-gap list (Step 5) or story selection (Step 6), which stay 100% template-grounded. Skip gracefully and say so if nothing useful surfaces. Never fabricate a company detail that a search doesn't actually support.

---

## Step 8 — Structural Self-Check

Before writing anything, verify the drafted content against these rules — rewrite any section that violates them:

- [ ] The only headings present are "Gaps to Address," "Stories & Themes to Be Ready to Discuss," and optionally "What to Expect." No "Sample Answers," "Talking Points," or any Q&A-formatted section.
- [ ] No single first-person narrative excerpt exceeds 2-3 sentences — long enough to jog memory, too short to function as a memorizable script.
- [ ] No question-and-answer pairing anywhere in the draft, and no passage reads like a rehearsed, verbatim script rather than a prompt/theme.

---

## Step 9 — Write Output

Write `output/<base-name>-interview-prep.md` (plain Markdown only — this is for the applicant's own reading, never submitted anywhere, so no PDF/pandoc step). Always regenerate fresh on every run; there is no staleness/skip check here, since the target stage and gaps can genuinely change between runs.

Structure:
```
# Interview Prep — <Position Title> @ <Company>

Target stage: <stage> (<how it was determined: logged upcoming / predicted / general>)

## Gaps to Address
<organized by urgency, per Step 5>

## Stories & Themes to Be Ready to Discuss
<per Step 6, Side-Notes-sourced items tagged>

## What to Expect
<only if Step 7 found something worth including>
```

---

## Step 10 — Report

```
Interview prep ready.

  Job            : <position title> @ <company>
  Target stage   : <stage> (<detection path>)

  Top gaps:
    - <1-3 lines>

  Top stories to have ready:
    - <1-3 lines>

  Written to: output/<base-name>-interview-prep.md
```
