# Expected — Ambiguous Middle (the real calibration signal)

**Source:** `job-description.md` — a fabricated posting for a fictional company ("Bellwood Cloud Systems"), authored for this calibration set. Chosen deliberately to sit mid-"Solid match" band: the example applicant's (Dana Whitfield) `template/` gives real, partial overlap (AWS, Terraform, CI/CD pipeline ownership, cross-team tooling adoption, a migration-leadership track record) but two hard, undeniable gaps (no Go, no Kubernetes) plus a title band ("Senior or Staff") that only partially matches her current Senior title. This is the fixture most likely to catch rubric-wording drift, since a small change in how "partial" vs. "absent" gets classified can shift the total meaningfully within the band.

Calibrated 2026 against a real itemized classification run through `scripts/score_job_match.py`, against Dana Whitfield's actual `template/` data (the example applicant shipped on `main`) — it scored **63/100 ("Solid match with notable gaps")**, comfortably inside the band and within reach of the Strong-match boundary (70) without crossing it. **This fixture only produces comparable results when run against Dana Whitfield's `template/` data (i.e. from `main`)**.

## Expected ranges

| Dimension | Expected range | Notes |
|---|---|---|
| Skill Overlap | 14–24 / 30 | Go and Kubernetes are hard absences with no partial-credit basis; AWS/Terraform, CI/CD ownership, and cross-team tooling adoption are real, cited matches that should keep this from cratering. |
| Experience Relevance | 8–20 / 30 | Two of six extracted JD-responsibility items (Go service development, Kubernetes operations) should classify `absent`; migration leadership and internal-tooling adoption should classify `direct`. |
| Seniority Match | 11–18 / 20 | The JD's "Senior or Staff" band gives real credit for Dana's exact current title, while scope/years should reflect that she isn't yet at full Staff-level scope. |
| Transferable Skills | 10–16 / 20 | AWS certification, CI/CD leadership, cross-team tooling reuse, and current employment at an observability-focused company are all real, cited differentiators. |
| **Total** | **50–72 / 100** | Deliberately spans most of the "Solid match" band and reaches toward "Strong match" — the point of this fixture isn't to pin one exact score, it's to confirm the total doesn't drift *outside* this range (e.g. down into "Stretch role" or up past "Strong match" into "Exceptional"). |
| Interpretation | "Solid match with notable gaps" (most likely) or "Strong match" | Either is fine on a single run. If it lands in "Stretch role" (≤54) or "Exceptional match" (85+) on two separate checks, the itemization has drifted materially. |
