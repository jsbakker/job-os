"""Tests for scripts/score_job_match.py.

Pure arithmetic on top of an LLM-produced itemized classification: weighting,
capping, interpretation-band lookup, and salary-range positioning, so the
same classification always produces the same numbers.
"""
import json


# ---- payload builders -------------------------------------------------
# Each builder gives exact control over one sub-score so boundary totals
# can be constructed precisely rather than guessed at.

def _skill_overlap_payload(required_points, include_preferred_credit=True):
    """required_points in [0, 20], via 20 required items (k match, rest absent).
    include_preferred_credit=True -> empty preferred list (+10 auto credit).
    include_preferred_credit=False -> one absent preferred item (+0 credit).
    Resulting skill_overlap = required_points + (10 if credit else 0)."""
    required = [{"status": "match"} for _ in range(required_points)] + \
               [{"status": "absent"} for _ in range(20 - required_points)]
    preferred = [] if include_preferred_credit else [{"status": "absent"}]
    return {"required": required, "preferred": preferred}


def _experience_relevance_payload(direct_count, total=30):
    """direct_count in [0, total] -> experience_relevance == direct_count exactly."""
    items = [{"status": "direct"} for _ in range(direct_count)] + \
            [{"status": "absent"} for _ in range(total - direct_count)]
    return {"items": items}


def _seniority_payload(title=0, scope=0, years=0):
    return {"title_level": {"score": title}, "scope": {"score": scope}, "years": {"score": years}}


def _transferable_payload(total_score):
    return {"items": [{"score": total_score}]} if total_score else {"items": []}


def _payload(skill_overlap, experience_relevance, seniority, transferable):
    return {
        "skill_overlap": skill_overlap,
        "experience_relevance": experience_relevance,
        "seniority_match": seniority,
        "transferable_skills": transferable,
    }


def _score(tmp_path, run_json, payload):
    path = tmp_path / "classification.json"
    path.write_text(json.dumps(payload))
    _, data = run_json("score_job_match.py", "score", "--input", str(path))
    return data


# ---- score: sub-score arithmetic --------------------------------------

def test_empty_preferred_list_gives_full_credit(tmp_path, run_json):
    with_credit = _score(tmp_path, run_json, _payload(
        _skill_overlap_payload(0, include_preferred_credit=True),
        _experience_relevance_payload(0), _seniority_payload(), _transferable_payload(0),
    ))
    without_credit = _score(tmp_path, run_json, _payload(
        _skill_overlap_payload(0, include_preferred_credit=False),
        _experience_relevance_payload(0), _seniority_payload(), _transferable_payload(0),
    ))
    assert with_credit["skill_overlap"] == 10
    assert without_credit["skill_overlap"] == 0


def test_seniority_and_transferable_are_direct_sums(tmp_path, run_json):
    data = _score(tmp_path, run_json, _payload(
        _skill_overlap_payload(0, include_preferred_credit=False),
        _experience_relevance_payload(0),
        _seniority_payload(title=7, scope=6, years=3),
        _transferable_payload(0),
    ))
    assert data["seniority_match"] == 16

    data2 = _score(tmp_path, run_json, _payload(
        _skill_overlap_payload(0, include_preferred_credit=False),
        _experience_relevance_payload(0), _seniority_payload(),
        {"items": [{"score": 4}, {"score": 3}, {"score": 5}]},
    ))
    assert data2["transferable_skills"] == 12


def test_dimensions_cap_at_their_maximums(tmp_path, run_json):
    data = _score(tmp_path, run_json, _payload(
        _skill_overlap_payload(20, include_preferred_credit=True),  # 20 + 10 = 30, at cap already
        _experience_relevance_payload(30),
        _seniority_payload(title=8, scope=8, years=4),  # = 20
        {"items": [{"score": 20}, {"score": 20}]},  # sum 40, capped to 20
    ))
    assert data["skill_overlap"] == 30
    assert data["experience_relevance"] == 30
    assert data["seniority_match"] == 20
    assert data["transferable_skills"] == 20
    assert data["total"] == 100


# ---- interpretation band boundaries ------------------------------------
# Boundaries: 39/40, 54/55, 69/70, 84/85.

def test_boundary_39_is_reach_40_is_stretch(tmp_path, run_json):
    # skill_overlap and experience_relevance both zeroed via explicit
    # absent items (not empty lists, to avoid the empty-list auto-credit).
    zero_so = _skill_overlap_payload(0, include_preferred_credit=False)
    zero_er = _experience_relevance_payload(0, total=1)

    at_39 = _score(tmp_path, run_json, _payload(
        zero_so, zero_er, _seniority_payload(title=8, scope=8, years=3), _transferable_payload(20),
    ))
    assert at_39["total"] == 39
    assert at_39["interpretation"] == "Reach application"

    at_40 = _score(tmp_path, run_json, _payload(
        zero_so, zero_er, _seniority_payload(title=8, scope=8, years=4), _transferable_payload(20),
    ))
    assert at_40["total"] == 40
    assert at_40["interpretation"] == "Stretch role"


def test_boundary_54_is_stretch_55_is_solid(tmp_path, run_json):
    # Fixed +40 from maxed seniority/transferable; skill_overlap +
    # experience_relevance supply the remaining 14 / 15.
    seniority = _seniority_payload(title=8, scope=8, years=4)  # 20
    transferable = _transferable_payload(20)

    at_54 = _score(tmp_path, run_json, _payload(
        _skill_overlap_payload(0, include_preferred_credit=True),  # 10
        _experience_relevance_payload(4), seniority, transferable,
    ))
    assert at_54["total"] == 54
    assert at_54["interpretation"] == "Stretch role"

    at_55 = _score(tmp_path, run_json, _payload(
        _skill_overlap_payload(0, include_preferred_credit=True),  # 10
        _experience_relevance_payload(5), seniority, transferable,
    ))
    assert at_55["total"] == 55
    assert at_55["interpretation"] == "Solid match with notable gaps"


def test_boundary_69_is_solid_70_is_strong(tmp_path, run_json):
    seniority = _seniority_payload(title=8, scope=8, years=4)  # 20
    transferable = _transferable_payload(20)

    at_69 = _score(tmp_path, run_json, _payload(
        _skill_overlap_payload(0, include_preferred_credit=True),  # 10
        _experience_relevance_payload(19), seniority, transferable,
    ))
    assert at_69["total"] == 69
    assert at_69["interpretation"] == "Solid match with notable gaps"

    at_70 = _score(tmp_path, run_json, _payload(
        _skill_overlap_payload(0, include_preferred_credit=True),  # 10
        _experience_relevance_payload(20), seniority, transferable,
    ))
    assert at_70["total"] == 70
    assert at_70["interpretation"] == "Strong match"


def test_boundary_84_is_strong_85_is_exceptional(tmp_path, run_json):
    seniority = _seniority_payload(title=8, scope=8, years=4)  # 20
    transferable = _transferable_payload(20)

    at_84 = _score(tmp_path, run_json, _payload(
        _skill_overlap_payload(4, include_preferred_credit=True),  # 14
        _experience_relevance_payload(30), seniority, transferable,
    ))
    assert at_84["total"] == 84
    assert at_84["interpretation"] == "Strong match"

    at_85 = _score(tmp_path, run_json, _payload(
        _skill_overlap_payload(5, include_preferred_credit=True),  # 15
        _experience_relevance_payload(30), seniority, transferable,
    ))
    assert at_85["total"] == 85
    assert at_85["interpretation"] == "Exceptional match"


# ---- compare -----------------------------------------------------------

def test_compare_material_rescore_true_at_exactly_8_point_delta(tmp_path, run_json, manifest_file):
    prior = manifest_file(job_match={
        "total": 60, "skill_overlap": 15, "experience_relevance": 15,
        "seniority_match": 15, "transferable_skills": 15, "interpretation": "Solid match with notable gaps",
    })
    new = tmp_path / "new.json"
    new.write_text(json.dumps({
        "total": 68, "skill_overlap": 17, "experience_relevance": 17,
        "seniority_match": 17, "transferable_skills": 17, "interpretation": "Solid match with notable gaps",
    }))
    _, data = run_json("score_job_match.py", "compare", "--new", str(new), "--prior", str(prior))
    assert data["total_delta"] == 8
    assert data["label_changed"] is False
    assert data["material_rescore"] is True


def test_compare_material_rescore_false_at_7_point_delta_no_label_change(tmp_path, run_json, manifest_file):
    prior = manifest_file(job_match={
        "total": 60, "skill_overlap": 15, "experience_relevance": 15,
        "seniority_match": 15, "transferable_skills": 15, "interpretation": "Solid match with notable gaps",
    })
    new = tmp_path / "new.json"
    new.write_text(json.dumps({
        "total": 67, "skill_overlap": 17, "experience_relevance": 16,
        "seniority_match": 17, "transferable_skills": 17, "interpretation": "Solid match with notable gaps",
    }))
    _, data = run_json("score_job_match.py", "compare", "--new", str(new), "--prior", str(prior))
    assert data["total_delta"] == 7
    assert data["material_rescore"] is False


def test_compare_dimensions_needing_explanation_at_exactly_3_point_delta(tmp_path, run_json, manifest_file):
    prior = manifest_file(job_match={
        "total": 60, "skill_overlap": 15, "experience_relevance": 15,
        "seniority_match": 15, "transferable_skills": 15, "interpretation": "Solid match with notable gaps",
    })
    new = tmp_path / "new.json"
    new.write_text(json.dumps({
        "total": 65, "skill_overlap": 18, "experience_relevance": 17,
        "seniority_match": 15, "transferable_skills": 15, "interpretation": "Solid match with notable gaps",
    }))
    _, data = run_json("score_job_match.py", "compare", "--new", str(new), "--prior", str(prior))
    # skill_overlap delta = 3 (included), experience_relevance delta = 2 (excluded)
    assert data["dimensions_needing_explanation"] == ["skill_overlap"]


def test_compare_accepts_bare_job_match_prior_without_wrapper(tmp_path, run_json):
    # The code has an explicit fallback: prior_raw.get("job_match", prior_raw)
    bare_prior = tmp_path / "bare_prior.json"
    bare_prior.write_text(json.dumps({
        "total": 60, "skill_overlap": 15, "experience_relevance": 15,
        "seniority_match": 15, "transferable_skills": 15, "interpretation": "Solid match with notable gaps",
    }))
    new = tmp_path / "new.json"
    new.write_text(json.dumps({
        "total": 60, "skill_overlap": 15, "experience_relevance": 15,
        "seniority_match": 15, "transferable_skills": 15, "interpretation": "Solid match with notable gaps",
    }))
    _, data = run_json("score_job_match.py", "compare", "--new", str(new), "--prior", str(bare_prior))
    assert data["material_rescore"] is False
    assert data["total_delta"] == 0


def test_compare_no_prior_job_match_found(tmp_path, run_json, manifest_file):
    prior = manifest_file()  # no job_match key at all
    new = tmp_path / "new.json"
    new.write_text(json.dumps({
        "total": 60, "skill_overlap": 15, "experience_relevance": 15,
        "seniority_match": 15, "transferable_skills": 15, "interpretation": "Solid match with notable gaps",
    }))
    _, data = run_json("score_job_match.py", "compare", "--new", str(new), "--prior", str(prior))
    assert data["material_rescore"] is False
    assert "reason" in data


# ---- salary-position -----------------------------------------------------

def test_salary_position_mid_band(run_json):
    _, data = run_json(
        "score_job_match.py", "salary-position",
        "--anchor-low", "100000", "--anchor-high", "200000",
        "--total-score", "62", "--transferable-score", "10",
    )
    assert data["positioned_fraction"] == 0.50
    assert data["stretch_above_anchor"] is False
    assert data["suggested_low"] == 145000
    assert data["suggested_high"] == 155000


def test_salary_position_stretch_above_anchor_when_all_conditions_met(run_json):
    _, data = run_json(
        "score_job_match.py", "salary-position",
        "--anchor-low", "100000", "--anchor-high", "200000",
        "--total-score", "90", "--transferable-score", "18",
        "--market-worth-high", "250000",
    )
    assert data["stretch_above_anchor"] is True
    assert data["suggested_low"] == 204000
    assert data["suggested_high"] == 220000


def test_salary_position_no_stretch_when_transferable_score_too_low(run_json):
    _, data = run_json(
        "score_job_match.py", "salary-position",
        "--anchor-low", "100000", "--anchor-high", "200000",
        "--total-score", "90", "--transferable-score", "10",  # below the 16 threshold
        "--market-worth-high", "250000",
    )
    assert data["stretch_above_anchor"] is False
    assert data["suggested_high"] == 200000  # clamped to anchor_high, not stretched above it


def test_salary_position_no_stretch_when_market_worth_not_provided(run_json):
    _, data = run_json(
        "score_job_match.py", "salary-position",
        "--anchor-low", "100000", "--anchor-high", "200000",
        "--total-score", "90", "--transferable-score", "18",
    )
    assert data["stretch_above_anchor"] is False
