# Expected — Strong Match

**Source:** `job-description.md` — a fabricated posting for a fictional company ("Northgate Fleet Systems"), authored for this calibration set. Chosen because it combines direct stack overlap (Java/Spring Boot, Angular/NgRx, Kafka, PostgreSQL) with direct domain overlap (dispatch/fleet-tracking software) against the example applicant's (Dana Whitfield) real `template/` — most notably her current role at Harborline Logistics, itself a dispatch/fleet-tracking product. It should score cleanly high without needing transferable-skills padding to get there.

Calibrated 2026 against a real itemized classification run through `scripts/score_job_match.py`, against Dana Whitfield's actual `template/` data (the example applicant shipped on `main`) — it scored **80/100 ("Strong match")**, which anchors these ranges. **This fixture only produces comparable results when run against Dana Whitfield's `template/` data (i.e. from `main`)** — running it against a personalized `template/` on a fork will score against different underlying evidence and isn't comparable to these ranges.

## Expected ranges

| Dimension | Expected range | Notes |
|---|---|---|
| Skill Overlap | 24–30 / 30 | Direct required-skill matches across Java/Spring Boot, Angular/NgRx, Kafka, PostgreSQL, OAuth2/JWT, Docker/CI, and testing frameworks — nearly every required item should classify `match`. |
| Experience Relevance | 17–25 / 30 | Harborline Logistics is itself a dispatch/fleet-tracking product, so several JD-responsibility items should classify `direct`, not just `adjacent`. |
| Seniority Match | 14–19 / 20 | JD title ("Senior Software Engineer") is an exact match to Dana's current title — this dimension should read strong, not ambiguous. |
| Transferable Skills | 10–16 / 20 | AWS certification and direct prior domain experience (not just a stack match) should carry real, cited credit. |
| **Total** | **72–88 / 100** | |
| Interpretation | "Strong match" or "Exceptional match" | Should not fall to "Solid match with notable gaps" (≤69) — if it does on two separate checks, the itemization or rubric wording has drifted. |
