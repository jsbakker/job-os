# Expected — Stretch / Reach (Reach/Stretch Boundary)

**Source:** `job-description.md` — a fabricated posting for a fictional company ("Everline Financial Technologies"), authored for this calibration set. Chosen to test a "right stack, wrong domain and level" gap rather than a total stack mismatch: the required language (Java/Spring Boot) and cloud platform (AWS) genuinely overlap with the example applicant's (Dana Whitfield) `template/`, but the regulated-finance domain (PCI-DSS, ledger/reconciliation, fraud detection) and the Staff-level seniority bar are both real, substantial gaps with zero supporting evidence anywhere in her history.

Calibrated 2026 against a real itemized classification run through `scripts/score_job_match.py`, against Dana Whitfield's actual `template/` data (the example applicant shipped on `main`) — it scored **39/100 ("Reach application")**, one point below the Stretch-role floor (40). This is a deliberate boundary fixture, complementary to `fixture-03-ambiguous-middle`'s Solid/Strong boundary: it tests the Reach/Stretch line instead. **This fixture only produces comparable results when run against Dana Whitfield's `template/` data (i.e. from `main`)**.

## Expected ranges

| Dimension | Expected range | Notes |
|---|---|---|
| Skill Overlap | 8–18 / 30 | Real matches on Java/Spring Boot, relational-database work, and AWS, offset by hard absences on PCI-DSS, ledger design, and fraud/risk decisioning — none of which appear anywhere in `template/`. |
| Experience Relevance | 3–11 / 30 | The regulated-finance domain itself is entirely absent from `template/`; only general backend-service-ownership items should classify `direct`, with everything domain-specific `absent`. |
| Seniority Match | 5–12 / 20 | JD is Staff-level (one full step above Dana's current Senior title) with a 3+ year regulated-domain requirement she has zero years against — this dimension should read as a real, not marginal, gap. |
| Transferable Skills | 7–14 / 20 | AWS/Kafka fluency and migration-leadership experience are real, cited differentiators, but shouldn't be enough on their own to offset the domain gap above. |
| **Total** | **28–48 / 100** | Deliberately spans the "Reach application" and "Stretch role" bands — the point of this fixture is to confirm the total doesn't drift *outside* this range (e.g. up into "Solid match" or down into a near-zero score). |
| Interpretation | "Reach application" or "Stretch role" | Either is fine on a single run — this fixture sits right at that boundary by design. If it lands in "Solid match" (55+) on two separate checks, the itemization has drifted materially, likely from over-crediting the stack overlap despite the domain gap. |
