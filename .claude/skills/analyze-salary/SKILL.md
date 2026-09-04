---
name: analyze-salary
description: Produce a report-only asking-salary recommendation for one job posting -- currency, applicant floor, market worth, compensation anchor (including contract/hourly roles), positioning, a net-pay sanity check, and mismatch flags -- and persist the full result to a fixed scratch file. Internal helper skill, not for direct end-user invocation -- called by /tailor-resume.
---

Produce an asking-salary analysis for one job posting. This is a report-only recommendation — it does not appear on the resume or cover letter. Never fabricate a precise, unsourced number; every figure must trace back to either the job posting, a cited web search, or the applicant's own stated expectations.

Inputs (the caller must have these ready before invoking this skill): the job description text, the applicant's career profile, `variable-input/salary-expectations.md`'s contents if present, and the job-match `total` and `transferable_skills` sub-score from `score-job-match` (needed for positioning math — invoke `score-job-match` first).

## Step 1 — Determine the Reporting Currency

Never assume USD or any other currency by default — derive it:
- If `variable-input/salary-expectations.md` has a `Currency` field, that's the applicant's currency for all figures on the applicant side of this analysis.
- Otherwise, infer the applicant's local currency from their location (`contact-info.txt`'s location if stated, otherwise infer from the job posting's stated location/remote policy and flag the assumption).
- Use the job posting's own stated currency for the job's compensation anchor when it states one explicitly (look for an explicit code like USD/CAD/EUR, or contextual clues — company HQ, job location, "USD"/"CAD" in the text — since a bare "$" is ambiguous).
- Every dollar figure recorded in this step must carry an explicit currency code (e.g., "$130,000 CAD"), never a bare "$".
- If the job's anchor currency differs from the applicant's local currency, flag it (Step 6) rather than silently converting — do not fabricate an exchange-rate conversion.

## Step 2 — Read the Applicant's Floor, if Provided

If `variable-input/salary-expectations.md` exists, note the current salary, minimum acceptable, and/or target range (in the currency from Step 1). This is a hard floor: the suggested range's low end must never be recommended below the applicant's stated minimum. If the file doesn't exist, there is no floor to enforce — proceed on computed value alone.

## Step 3 — Establish the Applicant's General Market Worth

Independent of this specific job posting, determine what a candidate with this applicant's title, years of experience, seniority (reuse the Seniority Match reasoning from `score-job-match`), and core skills typically commands. Search the web to find current data (prefer sources like levels.fyi, Glassdoor, Payscale, Bureau of Labor Statistics, or recent salary-survey aggregators; prefer results from the last ~2 years) for the applicant's location. Record this as the applicant's market-worth range, labeled with its currency code, with a cited source.

## Step 4 — Establish the Job's Compensation Anchor

- If the job posting states a salary or range explicitly, use it verbatim (currency and all) as the primary anchor — this is always preferred over research.
- Otherwise, first check whether this is a **contract/hourly engagement** — language like "contract", "hourly rate", "day rate", "1099", "corp-to-corp"/"C2C", or "on incorporation", or the absence of any salaried-employment framing. If so:
  - Do **not** anchor on generic salary-aggregator "hourly rate" or "contractor salary" listings. Those sites report realized/averaged contractor *income*, not billing *rates* — dividing a typical FTE salary survey by working hours (or reading a site's "contract consultant salary") systematically understates what a contractor needs to charge, because it doesn't price in self-employment tax, self-funded benefits, lost PTO, or gaps between contracts.
  - Instead, ground the anchor in the applicant's own comp data via the standard contractor markup convention (contract billing rate ≈ 1.5x-2x the equivalent FTE hourly rate):
    ```bash
    python3 scripts/score_job_match.py contract-rate --annual-salary <current salary from salary-expectations.md, or the market-worth midpoint from Step 3 if unavailable>
    ```
    Use its `floor_hourly`/`stretch_hourly` (and the `*_annualized_equivalent` fields) as the anchor low/high. Still do one corroborating web search for actual contractor/consultant *billing* rates (not converted-salary figures) in the applicant's field and location — cite it if it materially agrees or disagrees — but the multiplier-derived figures take precedence as the anchor unless the corroborating research is clearly stronger (e.g. a staffing agency's published rate card for this exact role type).
- For a salaried (non-contract) role with no posted range, search the web for a market range for this specific title/level/location/company, using the same sourcing standard as Step 3, in the currency established in Step 1. Label this anchor as "researched" (not "posted") in the report so the applicant knows it isn't from the employer.

## Step 5 — Position the Ask Within the Anchor Range

Do not hand-pick a percentage yourself — run:
```bash
python3 scripts/score_job_match.py salary-position --anchor-low <low> --anchor-high <high> \
  --total-score <job-match total> --transferable-score <job-match Transferable Skills sub-score> \
  [--market-worth-high <applicant's market-worth range high, if Step 3 found one>]
```
This applies fixed bands (85–100 → top of range, or up to 10% above it if market-worth-high exceeds the anchor high and transferable-score is strong; 70–84 → upper-middle; 55–69 → middle; under 55 → lower-middle to low end) — use its `suggested_low`/`suggested_high` output verbatim.
- Do not inflate the number to force it up to the applicant's market worth if the job's anchor range is simply lower across the board — surface that as a flag instead (Step 6), don't mask it.
- If a floor from `salary-expectations.md` exists and the script's `suggested_low` falls below it, use the floor as the suggested low end instead and flag the conflict.
- If the job anchor and the applicant's market-worth figure ended up in different currencies (Step 1 flagged a mismatch), position within the job anchor's own currency and range — don't pass a market-worth-high from a different currency into the script.
- For a contract role anchored via `contract-rate` above, also convert `suggested_low`/`suggested_high` back to an hourly figure (divide by the same `annual_hours_basis`) since that's the unit the applicant will actually quote.

## Step 5b — Net-Pay Sanity Check

A raise can look bigger on paper than it is in the bank, especially moving from salaried employment to a contract (higher marginal tax bracket eating more of each incremental dollar, plus — for a contract specifically — losing employer-paid benefits/PTO and paying both CPP portions instead of half). Compare current vs. proposed take-home so the applicant sees the real delta:
- First construct a jurisdiction code from the applicant's location (from `contact-info.txt`, or `salary-expectations.md`'s `Location`/`Currency` fields): `<ISO-3166 country code>-<province/state abbreviation>`, e.g. `CA-BC` for British Columbia, Canada or `CA-ON` for Ontario, Canada.
- Check whether that code is in the script's supported set — run `python3 scripts/score_job_match.py net-pay --help` and look at the `--jurisdiction` choices, or read `JURISDICTIONS` in `scripts/score_job_match.py` directly. Only a small, explicitly-dated set of jurisdictions is supported at any given time.
- If the applicant's jurisdiction isn't supported, skip this sub-step entirely and note that a net-pay comparison isn't available for the applicant's jurisdiction — never fabricate a bracket table for an unsupported location.
- If `salary-expectations.md` has no stated current salary, skip this sub-step — there is nothing to compare against.
- Otherwise run:
  ```bash
  python3 scripts/score_job_match.py net-pay-compare \
    --current-gross <current salary from salary-expectations.md> --current-employment-type employee \
    --proposed-gross <the suggested range's midpoint, annualized> --proposed-employment-type <employee for a salaried role, self-employed for a contract> \
    --jurisdiction <the jurisdiction code from above>
  ```
- Record the `net_delta` and `share_of_raise_kept` (not just the gross delta), plus the `average_tax_rate` before and after, so the applicant sees how much of the raise actually survives taxes and (for a contract) the CPP/benefit shift.
- **Do not claim that moving into a higher tax bracket reduces net pay.** Canada's federal and provincial brackets are marginal — more gross income never produces less net income tax domestically (ignoring benefit-clawback edge cases like OAS, which don't apply here). What's real and worth surfacing plainly: the marginal rate on the *incremental* dollars is higher, so a smaller fraction of the raise is kept than the headline number suggests, and moving to contract status specifically adds the CPP/benefit/PTO costs already priced into Step 4's multiplier. If the script's `net_decreased` field ever comes back `true`, that means a bad input (e.g. a swapped current/proposed value), not a real tax outcome — check the inputs rather than reporting it as a finding.

## Step 6 — Flag Mismatches Explicitly — Do Not Smooth Them Over

- ⚠ **Pay cut risk:** the job's anchor range sits meaningfully (~10%+) below the applicant's market-worth range (only compare when both are in the same currency, or note that a currency difference makes the comparison approximate). State it plainly, especially if paired with a borderline job-match score.
- ⚠ **Below stated floor:** the job's anchor range can't support the minimum in `salary-expectations.md`.
- ⚠ **No salary data found:** neither the posting nor web search produced usable compensation data (ambiguous location, obscure title, etc.) — say so rather than inventing a number, and note that the suggested range should be omitted from the caller's report.
- ⚠ **Location assumed:** the applicant's location wasn't stated in `contact-info.txt` and had to be inferred.
- ⚠ **Currency mismatch:** the job's anchor currency differs from the applicant's local currency — note both currencies explicitly and that the comparison is approximate absent a real conversion.
- ⚠ **Net-pay comparison unavailable:** the applicant's jurisdiction isn't in the script's supported tax-bracket set.

## Step 7 — Persist the Result (unconditional, every run)

Save one JSON file to `/tmp/salary-analysis.json`, overwriting any prior content, containing everything the caller's later report step needs verbatim — do not make the caller reconstruct any of this from memory:

```json
{
  "suggested_asking_salary": "<Step 5's suggested range with currency code, and an hourly figure too for a contract role, e.g. '$130,000 - $145,000 CAD', or null if Step 6 flagged no usable data>",
  "job_posting_salary_range": {
    "range": "<Step 4's compensation anchor, e.g. '$120,000 - $150,000 CAD', or null>",
    "source": "<'posted' | 'researched' | 'contractor-multiplier', or null>"
  },
  "anchor_citation": "<the anchor's source description and citation, e.g. 'Researched range for Senior iOS Developer, Vancouver BC (source: levels.fyi, 2026)'>",
  "market_worth": "<applicant's general market-worth range with currency code, e.g. '$140,000 - $170,000 CAD'>",
  "market_worth_citation": "<source cited in Step 3>",
  "rationale": "<one line tying the position within the range to the job-match score and transferable skills>",
  "applicant_floor_respected": "<the minimum from salary-expectations.md if that file was found, else null>",
  "net_pay_comparison": {
    "jurisdiction_label": "<from Step 5b, or omit this whole object if Step 5b didn't run>",
    "current_net": <number>,
    "proposed_net": <number>,
    "share_of_raise_kept": <fraction>
  },
  "flags": ["<each ⚠ flag raised in Step 6 as its own string, in order>"]
}
```

This file is a superset of what the manifest schema needs — the caller copies only `suggested_asking_salary` and `job_posting_salary_range` into its manifest's matching fields, and reads the rest of this file directly at its own report step.

## After Analysis

State in one line what was found and where it was saved, e.g. "Salary analysis complete: suggested $130,000-$145,000 CAD, saved to /tmp/salary-analysis.json." plus a one-line mention of any flags raised — so the caller's next step can proceed without re-reading this list. The caller must re-read `/tmp/salary-analysis.json` at its own later write/report steps rather than recalling values from this invocation's output.
