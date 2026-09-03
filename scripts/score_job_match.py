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

    # Derive a contract/hourly billing-rate anchor from an FTE salary using
    # the standard 1.5x-2x contractor markup convention (self-employment
    # tax, self-funded benefits, no PTO, income-gap coverage).
    python3 scripts/score_job_match.py contract-rate --annual-salary <current-or-target-annual-salary>

    # Compare take-home pay between a current salary and a proposed one,
    # using real marginal tax brackets for one of a small, explicitly-dated
    # set of supported jurisdictions (see JURISDICTIONS below).
    python3 scripts/score_job_match.py net-pay-compare --current-gross <current-annual-salary> --current-employment-type employee \\
        --proposed-gross <proposed-annual-salary> --proposed-employment-type employee|self-employed --jurisdiction <jurisdiction-code>
"""
import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Tax-bracket data for net-pay comparisons. Deliberately narrow and NOT tied
# to any one adopter's location: only jurisdictions with a verified, dated,
# public government table are listed, as a small illustrative set an adopter
# can extend with their own province/state/country. Never guess a bracket
# table for an unsupported jurisdiction -- compute_net_pay() returns an
# explicit "unsupported jurisdiction" error instead, and the calling skill
# step must skip the comparison rather than fabricate one.
#
# CPP/EI are federal (apply to every Canadian province/territory), sourced
# from CRA/Service Canada rate announcements. Provincial brackets/BPA are
# sourced from each province's own tax authority. All figures are tax year
# 2026 -- refresh this table (and TAX_YEAR) each January, and add more
# provinces/states/countries here rather than assuming any one is "the"
# supported jurisdiction.
TAX_YEAR = 2026

CA_FEDERAL_2026_BRACKETS = [
    (0, 58523, 0.14),
    (58523, 117045, 0.205),
    (117045, 181440, 0.26),
    (181440, 258482, 0.29),
    (258482, None, 0.33),
]
CA_FEDERAL_2026_BPA = {"max": 16452, "min": 14829, "phaseout_low": 181440, "phaseout_high": 258482}

CA_2026_CPP = {
    "exemption": 3500,
    "ympe": 74600,
    "yampe": 85000,
    "employee_rate": 0.0595,
    "employee_max": 4230.45,
    "cpp2_employee_rate": 0.04,
    "cpp2_employee_max": 416.00,
    "self_employed_rate": 0.1190,
    "self_employed_max": 8460.90,
    "cpp2_self_employed_rate": 0.08,
    "cpp2_self_employed_max": 832.00,
}
CA_2026_EI = {"max_insurable": 68900, "employee_rate": 0.0163, "employee_max": 1123.07}

CA_BC_2026_BRACKETS = [
    (0, 45654, 0.0506),
    (45654, 91310, 0.0770),
    (91310, 104835, 0.1050),
    (104835, 127299, 0.1229),
    (127299, 172602, 0.1470),
    (172602, 240716, 0.1680),
    (240716, None, 0.2050),
]

CA_ON_2026_BRACKETS = [
    (0, 53891, 0.0505),
    (53891, 107785, 0.0915),
    (107785, 150000, 0.1116),
    (150000, 220000, 0.1216),
    (220000, None, 0.1316),
]


def _ca_jurisdiction(label: str, provincial_brackets, provincial_bpa: float) -> dict:
    return {
        "label": f"Canada federal + {label}, {TAX_YEAR} rates",
        "federal_brackets": CA_FEDERAL_2026_BRACKETS,
        "federal_bpa_max": CA_FEDERAL_2026_BPA["max"],
        "federal_bpa_min": CA_FEDERAL_2026_BPA["min"],
        "federal_bpa_phaseout_low": CA_FEDERAL_2026_BPA["phaseout_low"],
        "federal_bpa_phaseout_high": CA_FEDERAL_2026_BPA["phaseout_high"],
        "provincial_brackets": provincial_brackets,
        "provincial_bpa": provincial_bpa,
        "cpp": CA_2026_CPP,
        "ei": CA_2026_EI,
    }


# Jurisdiction codes follow <ISO-3166 country>-<province/state abbreviation>,
# e.g. CA-BC, CA-ON. This starter set covers two Canadian provinces; add more
# entries (any country) the same way rather than special-casing one adopter.
JURISDICTIONS = {
    "CA-BC": _ca_jurisdiction("British Columbia", CA_BC_2026_BRACKETS, 11981),
    "CA-ON": _ca_jurisdiction("Ontario", CA_ON_2026_BRACKETS, 12989),
}

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


def cmd_contract_rate(args):
    fte_hourly = args.annual_salary / args.annual_hours
    result = {
        "fte_hourly_equivalent": round(fte_hourly, 2),
        "floor_hourly": round(fte_hourly * args.floor_multiplier, 2),
        "stretch_hourly": round(fte_hourly * args.stretch_multiplier, 2),
        "floor_annualized_equivalent": round(fte_hourly * args.floor_multiplier * args.annual_hours),
        "stretch_annualized_equivalent": round(fte_hourly * args.stretch_multiplier * args.annual_hours),
        "floor_multiplier": args.floor_multiplier,
        "stretch_multiplier": args.stretch_multiplier,
        "annual_hours_basis": args.annual_hours,
        "note": (
            "Contract billing rate = FTE-equivalent hourly x 1.5-2x, covering self-employment "
            "tax, self-funded benefits, no PTO, and income gaps between contracts. This is a "
            "better-grounded anchor than generic salary-aggregator 'contractor hourly rate' "
            "listings, which report realized/averaged contractor income, not billing rates."
        ),
    }
    print(json.dumps(result, indent=2))


def _bracket_tax(income: float, brackets) -> float:
    tax = 0.0
    for low, high, rate in brackets:
        if income <= low:
            break
        upper = high if high is not None else income
        taxed = min(income, upper) - low
        if taxed > 0:
            tax += taxed * rate
    return tax


def _marginal_rate(income: float, brackets) -> float:
    for low, high, rate in brackets:
        if high is None or income <= high:
            return rate
    return brackets[-1][2]


def _federal_bpa(gross: float, j: dict) -> float:
    lo, hi = j["federal_bpa_phaseout_low"], j["federal_bpa_phaseout_high"]
    if gross <= lo:
        return j["federal_bpa_max"]
    if gross >= hi:
        return j["federal_bpa_min"]
    frac = (gross - lo) / (hi - lo)
    return j["federal_bpa_max"] - frac * (j["federal_bpa_max"] - j["federal_bpa_min"])


def compute_net_pay(gross: float, jurisdiction: str, employment_type: str) -> dict:
    if jurisdiction not in JURISDICTIONS:
        return {"error": f"unsupported jurisdiction: {jurisdiction}", "supported": list(JURISDICTIONS)}
    j = JURISDICTIONS[jurisdiction]

    federal_bpa = _federal_bpa(gross, j)
    federal_tax = max(0.0, _bracket_tax(gross, j["federal_brackets"]) - federal_bpa * j["federal_brackets"][0][2])
    provincial_tax = max(
        0.0, _bracket_tax(gross, j["provincial_brackets"]) - j["provincial_bpa"] * j["provincial_brackets"][0][2]
    )

    cpp = j["cpp"]
    ympe_band = max(0.0, min(gross, cpp["ympe"]) - cpp["exemption"])
    yampe_band = max(0.0, min(gross, cpp["yampe"]) - cpp["ympe"])
    if employment_type == "self-employed":
        cpp1 = min(ympe_band * cpp["self_employed_rate"], cpp["self_employed_max"])
        cpp2 = min(yampe_band * cpp["cpp2_self_employed_rate"], cpp["cpp2_self_employed_max"])
        ei = 0.0
    else:
        cpp1 = min(ympe_band * cpp["employee_rate"], cpp["employee_max"])
        cpp2 = min(yampe_band * cpp["cpp2_employee_rate"], cpp["cpp2_employee_max"])
        ei_j = j["ei"]
        ei = min(min(gross, ei_j["max_insurable"]) * ei_j["employee_rate"], ei_j["employee_max"])

    total_tax = federal_tax + provincial_tax
    total_deductions = total_tax + cpp1 + cpp2 + ei
    net = gross - total_deductions

    return {
        "jurisdiction": jurisdiction,
        "jurisdiction_label": j["label"],
        "employment_type": employment_type,
        "gross": round(gross, 2),
        "federal_tax": round(federal_tax, 2),
        "provincial_tax": round(provincial_tax, 2),
        "cpp": round(cpp1 + cpp2, 2),
        "ei": round(ei, 2),
        "total_tax_and_deductions": round(total_deductions, 2),
        "net": round(net, 2),
        "average_tax_rate": round(total_deductions / gross, 4) if gross else 0.0,
        "marginal_income_tax_rate": round(
            _marginal_rate(gross, j["federal_brackets"]) + _marginal_rate(gross, j["provincial_brackets"]), 4
        ),
    }


def cmd_net_pay(args):
    print(json.dumps(compute_net_pay(args.gross, args.jurisdiction, args.employment_type), indent=2))


def cmd_net_pay_compare(args):
    current = compute_net_pay(args.current_gross, args.jurisdiction, args.current_employment_type)
    proposed = compute_net_pay(args.proposed_gross, args.jurisdiction, args.proposed_employment_type)

    if "error" in current or "error" in proposed:
        print(json.dumps({"error": current.get("error") or proposed.get("error")}, indent=2))
        return

    gross_delta = proposed["gross"] - current["gross"]
    net_delta = proposed["net"] - current["net"]

    result = {
        "current": current,
        "proposed": proposed,
        "gross_delta": round(gross_delta, 2),
        "net_delta": round(net_delta, 2),
        "share_of_raise_kept": round(net_delta / gross_delta, 4) if gross_delta else None,
        # Under a marginal-bracket system, more gross income never produces
        # less net income tax domestically. If this is ever true, it means
        # a bad input (e.g. mismatched jurisdiction/employment type), not a
        # real tax cliff -- treat it as a bug signal, not a reportable fact.
        "net_decreased": net_delta < 0,
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

    p_contract = sub.add_parser(
        "contract-rate", help="Derive a contract/hourly billing-rate anchor from an FTE salary."
    )
    p_contract.add_argument("--annual-salary", type=float, required=True)
    p_contract.add_argument("--annual-hours", type=float, default=2080.0)
    p_contract.add_argument("--floor-multiplier", type=float, default=1.5)
    p_contract.add_argument("--stretch-multiplier", type=float, default=2.0)
    p_contract.set_defaults(func=cmd_contract_rate)

    p_netpay = sub.add_parser("net-pay", help="Estimate net (after-tax) pay for one gross income.")
    p_netpay.add_argument("--gross", type=float, required=True)
    p_netpay.add_argument("--jurisdiction", required=True, choices=list(JURISDICTIONS))
    p_netpay.add_argument("--employment-type", required=True, choices=["employee", "self-employed"])
    p_netpay.set_defaults(func=cmd_net_pay)

    p_netpay_cmp = sub.add_parser(
        "net-pay-compare", help="Compare net (after-tax) pay between a current and a proposed gross income."
    )
    p_netpay_cmp.add_argument("--current-gross", type=float, required=True)
    p_netpay_cmp.add_argument("--current-employment-type", required=True, choices=["employee", "self-employed"])
    p_netpay_cmp.add_argument("--proposed-gross", type=float, required=True)
    p_netpay_cmp.add_argument("--proposed-employment-type", required=True, choices=["employee", "self-employed"])
    p_netpay_cmp.add_argument("--jurisdiction", required=True, choices=list(JURISDICTIONS))
    p_netpay_cmp.set_defaults(func=cmd_net_pay_compare)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
