---
name: score-job-match
description: Score the applicant's fit for a job posting across four rubric dimensions (skill overlap, experience relevance, seniority match, transferable skills) using scripts/score_job_match.py, and persist the result to a fixed scratch file. Internal helper skill, not for direct end-user invocation -- called by /tailor-resume and /find-job-descriptions.
---

Score the applicant's fit for one job posting against their career profile. Inputs (the caller must have these ready before invoking this skill):

1. The job description text (already read by the caller).
2. The applicant's career profile (already loaded via `load-career-profile`, or otherwise available to the caller).
3. Optionally, the path to a prior `.manifest` file with an existing `job_match` block, for reconciliation against a previous score of the same job.

## Step 1 — Build the Itemized Classification

Score the applicant's fit for this role across four dimensions. Be honest — over-scoring a weak match wastes the applicant's time; under-scoring a strong one undersells them.

**Do not compute or estimate a dimension score yourself.** Your job is the itemized classification below — build it, write it to a temp JSON file (e.g. `/tmp/job-match-input.json`), then run:

```bash
python3 scripts/score_job_match.py score --input /tmp/job-match-input.json
```

That command returns `formatted_report` (a ready-to-use, deterministically-formatted block with all four sub-scores and rationale), the `total`, all four sub-scores, and the `interpretation` label — use its output verbatim. If a result looks wrong given the list you built, the itemization was wrong (a bad classification, or too many/few items extracted) — fix the classification and re-run the script. Never override its output by hand, and never hand-write your own version of `formatted_report` — it's built deterministically from the same classification you already produced.

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
- `title_level` (0–8): how the role's expected level (IC, Senior, Staff, Principal, etc.) compares to the applicant's title history. `scope` (0–8): ownership, cross-team impact, mentorship evidence from the experience entries. `years` (0–4): years of relevant experience vs. what the role expects. Note the reasoning for each — these notes are what make a future rescore auditable, and feed `formatted_report`'s rationale text directly.

### Transferable Skills
- Identify up to 5 items that aren't a direct requirement match but meaningfully strengthen the application — adjacent technologies, domain knowledge, process leadership, or a differentiator addressing an unstated need. Score each 0–5 based on strength/specificity; cite the evidence.

### Interpretation

Use the `interpretation` label from `scripts/score_job_match.py score`'s output verbatim — it's derived from `INTERPRETATION_BANDS`, the single source of truth for the band boundaries. Do not restate or eyeball the bands here, especially near a boundary.

## Step 2 — Persist the Result (unconditional, every run)

Immediately save the full JSON stdout from Step 1's `score` command to `/tmp/job-match-score.json`, overwriting any prior content. Do this every time, regardless of whether reconciliation (Step 3) applies — this is the file the caller will read back verbatim later, instead of relying on memory of what was computed here. Do not skip or defer this step.

## Step 3 — Reconciliation (only if a prior manifest path was given)

If the caller gave you a prior manifest path (an existing `job_match` block from a previous run against the same job), run:

```bash
python3 scripts/score_job_match.py compare --new /tmp/job-match-score.json --prior <prior-manifest-path>
```

Report the full result back to the caller (`material_rescore`, `total_delta`, `label_changed`, `per_dimension_delta`, `dimensions_needing_explanation`, `report_text`) — the caller decides how/whether to surface this in its own report step. If `material_rescore` is `true`, also be ready to explain, for each dimension in `dimensions_needing_explanation` (moved 3+ points), a specific one-line reason: either a genuine input change (cite the changed file/content), or — if the inputs are unchanged — an honest note naming which checklist item(s) were classified differently this time versus what the prior manifest's `job_match.checklist` recorded.

If no prior manifest path was given, skip this step entirely.

## After Scoring

State in one line what happened and where the result was saved, e.g. "Job match scored: 70/100 (Strong match), saved to /tmp/job-match-score.json." plus, if Step 3 ran, whether it was a material rescore — so the caller's next step can proceed without re-reading this list. The caller must re-read `/tmp/job-match-score.json` at its own later write/report steps rather than recalling values from this invocation's output.
