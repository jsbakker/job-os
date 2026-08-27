#!/usr/bin/env python3
"""Deterministic arithmetic for job-match scoring and salary positioning.

Claude does the judgment: classifying each required/preferred skill, each JD
responsibility, each seniority signal, and each transferable-skill item
against the applicant's template/, with a one-line citation for each call.
This script does the arithmetic on top of that classification (weighting,
capping, interpretation-band lookup, salary-range positioning) so the same
itemized classification always produces the same numbers -- no LLM mental
math involved, which is what caused two runs against an unchanged job
description to disagree by 11 points in practice.

Usage:
    # Compute job_match (4 sub-scores + total + interpretation) from an
    # itemized classification JSON file (see README.md / tailor-resume.md
    # Step 2b for the exact shape).
    python3 scripts/score_job_match.py score --input /tmp/classification.json

    # Compare a freshly computed job_match against a prior .manifest's
    # job_match, to detect and explain a "material rescore" instead of
    # silently overwriting the old number.
    python3 scripts/score_job_match.py compare --new /tmp/new_job_match.json --prior output/some-job.manifest

    # Position a suggested asking-salary range inside a posted/researched
    # anchor range, based on the total score.
    python3 scripts/score_job_match.py salary-position --anchor-low 150450 --anchor-high 194700 \\
        --total-score 62 --transferable-score 14
"""
import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Same bands as tailor-resume.md Step 2b's "Interpretation" section -- this
# table is the single source of truth for the label, so the LLM never has to
# eyeball whether e.g. 84 vs 85 crosses a boundary.
INTERPRETATION_BANDS = [
    (85, 100, "Exceptional match"),
    (70, 84, "Strong match"),
    (55, 69, "Solid match with notable gaps"),
    (40, 54, "Stretch role"),
    (0, 39, "Reach application"),
]

DIMENSION_LABELS = {
    "skill_overlap": "Skill Overlap",
    "experience_relevance": "Experience Relevance",
    "seniority_match": "Seniority Match",
    "transferable_skills": "Transferable Skills",
}

# (score_band_low, score_band_high, fraction_into_anchor_range)
# Mirrors Step 2c's "top / upper-middle / middle / lower-middle to low" bands.
SALARY_POSITION_BANDS = [
    (85, 100, 0.95),
    (70, 84, 0.70),
    (55, 69, 0.50),
    (40, 54, 0.30),
    (0, 39, 0.15),
]


def interpretation_for(total: int) -> str:
    for low, high, label in INTERPRETATION_BANDS:
        if low <= total <= high:
            return label
    return "Reach application"


def _read_json(path: str | None):
    if path:
        return json.loads(Path(path).read_text())
    return json.loads(sys.stdin.read())


def compute_skill_overlap(data: dict) -> int:
    required = data.get("required", [])
    preferred = data.get("preferred", [])

    def counts(items):
        matches = sum(1 for i in items if i.get("status") == "match")
        partials = sum(1 for i in items if i.get("status") == "partial")
        return matches, partials, len(items)

    req_matches, req_partials, req_total = counts(required)
    pref_matches, pref_partials, pref_total = counts(preferred)

    required_points = 20 if req_total == 0 else round(20 * (req_matches + 0.5 * req_partials) / req_total)
    preferred_points = 10 if pref_total == 0 else round(10 * (pref_matches + 0.5 * pref_partials) / pref_total)

    return min(30, required_points + preferred_points)


def compute_experience_relevance(data: dict) -> int:
    items = data.get("items", [])
    if not items:
        return 0
    direct = sum(1 for i in items if i.get("status") == "direct")
    adjacent = sum(1 for i in items if i.get("status") == "adjacent")
    return min(30, round(30 * (direct + 0.4 * adjacent) / len(items)))


def compute_seniority_match(data: dict) -> int:
    title = data.get("title_level", {}).get("score", 0)
    scope = data.get("scope", {}).get("score", 0)
    years = data.get("years", {}).get("score", 0)
    return min(20, title + scope + years)


def compute_transferable_skills(data: dict) -> int:
    items = data.get("items", [])
    return min(20, sum(i.get("score", 0) for i in items))


def cmd_score(args):
    payload = _read_json(args.input)

    skill_overlap = compute_skill_overlap(payload.get("skill_overlap", {}))
    experience_relevance = compute_experience_relevance(payload.get("experience_relevance", {}))
    seniority_match = compute_seniority_match(payload.get("seniority_match", {}))
    transferable_skills = compute_transferable_skills(payload.get("transferable_skills", {}))
    total = skill_overlap + experience_relevance + seniority_match + transferable_skills

    result = {
        "total": total,
        "skill_overlap": skill_overlap,
        "experience_relevance": experience_relevance,
        "seniority_match": seniority_match,
        "transferable_skills": transferable_skills,
        "interpretation": interpretation_for(total),
        "checklist": payload,
    }
    print(json.dumps(result, indent=2))


def cmd_compare(args):
    new = _read_json(args.new)

    prior_raw = json.loads(Path(args.prior).read_text())
    prior = prior_raw.get("job_match", prior_raw)

    if not prior or "total" not in prior:
        print(json.dumps({"material_rescore": False, "reason": "no prior job_match found"}, indent=2))
        return

    dims = list(DIMENSION_LABELS.keys())
    deltas = {d: new[d] - prior[d] for d in dims}
    total_delta = new["total"] - prior["total"]
    label_changed = new["interpretation"] != prior["interpretation"]
    material = abs(total_delta) >= 8 or label_changed

    lines = [
        f'⚠ Score changed since last run (was {prior["total"]}/100 "{prior["interpretation"]}", '
        f'now {new["total"]}/100 "{new["interpretation"]}"):'
    ]
    for d in dims:
        sign = "+" if deltas[d] >= 0 else ""
        flag = "  <-- explain this" if abs(deltas[d]) >= 3 else ""
        lines.append(f"  {DIMENSION_LABELS[d]:22s}: {prior[d]} → {new[d]}  ({sign}{deltas[d]}){flag}")

    result = {
        "material_rescore": material,
        "total_delta": total_delta,
        "label_changed": label_changed,
        "per_dimension_delta": deltas,
        "dimensions_needing_explanation": [d for d in dims if abs(deltas[d]) >= 3],
        "report_text": "\n".join(lines),
    }
    print(json.dumps(result, indent=2))


def position_fraction(total_score: int) -> float:
    for low, high, frac in SALARY_POSITION_BANDS:
        if low <= total_score <= high:
            return frac
    return 0.15


def _round_to_thousand(value: float) -> int:
    return int(round(value / 1000.0) * 1000)


def cmd_salary_position(args):
    anchor_low, anchor_high = args.anchor_low, args.anchor_high
    span = anchor_high - anchor_low
    frac = position_fraction(args.total_score)

    stretch_above = (
        args.total_score >= 85
        and args.transferable_score >= 16
        and args.market_worth_high is not None
        and args.market_worth_high > anchor_high
    )

    if stretch_above:
        suggested_low = _round_to_thousand(anchor_high * 1.02)
        suggested_high = _round_to_thousand(anchor_high * 1.10)
    else:
        center = anchor_low + span * frac
        half_width = span * 0.05
        suggested_low = _round_to_thousand(max(anchor_low, center - half_width))
        suggested_high = _round_to_thousand(min(anchor_high, center + half_width))
        if suggested_low > suggested_high:
            suggested_low, suggested_high = suggested_high, suggested_low

    result = {
        "suggested_low": suggested_low,
        "suggested_high": suggested_high,
        "positioned_fraction": frac,
        "stretch_above_anchor": stretch_above,
    }
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Deterministic scoring/salary arithmetic for /tailor-resume.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_score = sub.add_parser("score", help="Compute job_match from an itemized classification JSON.")
    p_score.add_argument("--input", help="Path to classification JSON. Reads stdin if omitted.")
    p_score.set_defaults(func=cmd_score)

    p_compare = sub.add_parser("compare", help="Compare a new job_match against a prior manifest's job_match.")
    p_compare.add_argument("--new", help="Path to the newly computed job_match JSON (from `score`). Reads stdin if omitted.")
    p_compare.add_argument("--prior", required=True, help="Path to the prior .manifest file (or a bare job_match JSON).")
    p_compare.set_defaults(func=cmd_compare)

    p_salary = sub.add_parser("salary-position", help="Position a suggested salary range inside an anchor range.")
    p_salary.add_argument("--anchor-low", type=float, required=True)
    p_salary.add_argument("--anchor-high", type=float, required=True)
    p_salary.add_argument("--total-score", type=int, required=True)
    p_salary.add_argument("--transferable-score", type=int, required=True)
    p_salary.add_argument("--market-worth-high", type=float, default=None)
    p_salary.set_defaults(func=cmd_salary_position)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
