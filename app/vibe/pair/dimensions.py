"""Dimension-specific pair interaction policies."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.vibe.config.v1_1_0 import (
    D2_INTERFERENCE_PAIRS,
    D2_PRODUCTIVE_PAIRS,
    D4_FEATURE_WEIGHTS,
    D5_FEATURE_WEIGHTS,
    D5_PRODUCTIVE_PAIRS,
    D8_FEATURE_WEIGHTS,
    D8_HARD_PAIRS,
    D8_PRODUCTIVE_PAIRS,
    D9_FEATURE_WEIGHTS,
    D9_PRODUCTIVE_PAIRS,
    D2_TIE_ORDER,
    PAIR_POLICY_THRESHOLDS,
    THRESHOLDS,
)
from app.vibe.contracts import DimensionResult, Relationship, SpecificationGap
from app.vibe.pair.continuous import generic_continuous_evaluator, weighted_gap
from app.vibe.pair.matrices import compare_d1, compare_d10, compare_d3, compare_d6, compare_d7


def _pair(categories: str, a: str, b: str) -> frozenset[str]:
    return frozenset({a, b})


def _result(dimension: str, relationship: Relationship, score: float, difference: float, trace: dict[str, Any]) -> DimensionResult:
    return DimensionResult(dimension, relationship, score, difference, 1.0, trace=trace)


def _guard_friction(value: float | None, path: str) -> float:
    if value is None:
        raise SpecificationGap(path, "The D5 friction guard input is undefined.")
    if not 0.0 <= float(value) <= 1.0:
        raise SpecificationGap(path, "The D5 friction guard input must be in [0,1].")
    return float(value)


def d5_high_salience(direct_gap: float, delay_gap: float, interaction_score: float) -> bool:
    """Canonical inclusive high-salience predicate from the completion amendment."""
    computed_negative_score = max(0.0, -float(interaction_score))
    return (
        float(direct_gap) >= PAIR_POLICY_THRESHOLDS["d5_direct_gap"]
        and float(delay_gap) >= PAIR_POLICY_THRESHOLDS["d5_delay_gap"]
        and computed_negative_score >= 0.50
    )


def compare_d2(a: dict, b: dict, *, d5_friction_score: float | None = None) -> DimensionResult:
    modes_a = a["D2"]["scores"]
    modes_b = b["D2"]["scores"]
    names = tuple(D2_TIE_ORDER)
    for source, label in ((modes_a, "a"), (modes_b, "b")):
        missing = sorted(set(names).difference(source))
        if missing:
            raise SpecificationGap(f"pair.D2.scores_{label}.{missing[0]}", "D2 comparison requires the complete canonical mode score vector.")
    denominator = sum(max(modes_a[name], modes_b[name]) for name in names)
    if denominator <= 0:
        raise SpecificationGap("pair.D2.scores", "D2 comparison requires a positive canonical score denominator.")
    shared = sum(min(modes_a[name], modes_b[name]) for name in names) / denominator
    label_gap = 1.0 - shared
    top_a = a["D2"]["selected_modes"][0]
    top_b = b["D2"]["selected_modes"][0]
    pair = _pair("D2", top_a, top_b)
    if shared >= PAIR_POLICY_THRESHOLDS["d2_shared_alignment"]:
        return _result("D2", Relationship.ALIGNMENT, 0.50 + 0.50 * shared, label_gap, {"shared": shared, "label_gap": label_gap, "top_modes": [top_a, top_b]})
    if pair in D2_PRODUCTIVE_PAIRS and label_gap >= PAIR_POLICY_THRESHOLDS["d2_productive_gap"]:
        guard_friction = _guard_friction(d5_friction_score, "pair.D2.productive_guard")
        if guard_friction >= 0.50:
            return _result("D2", Relationship.NEUTRAL, 0.0, 0.20, {"shared": shared, "label_gap": label_gap, "top_modes": [top_a, top_b], "productive_guard": False, "d5_friction_score": guard_friction})
        return _result("D2", Relationship.COMPLEMENTARITY, 0.25 + 0.24 * (1.0 - (label_gap - 0.30) / 0.30), 0.40, {"shared": shared, "label_gap": label_gap, "top_modes": [top_a, top_b], "productive_guard": True, "d5_friction_score": guard_friction})
    if label_gap > PAIR_POLICY_THRESHOLDS["d2_interference_gap"] and pair in D2_INTERFERENCE_PAIRS:
        score = -0.55 if label_gap >= PAIR_POLICY_THRESHOLDS["d2_hard_gap"] else -0.35
        return _result("D2", Relationship.HARD_FRICTION if label_gap >= PAIR_POLICY_THRESHOLDS["d2_hard_gap"] else Relationship.SOFT_FRICTION, score, 0.80 if label_gap >= PAIR_POLICY_THRESHOLDS["d2_hard_gap"] else 0.55, {"shared": shared, "label_gap": label_gap, "top_modes": [top_a, top_b]})
    return _result("D2", Relationship.NEUTRAL, 0.0, 0.20, {"shared": shared, "label_gap": label_gap, "top_modes": [top_a, top_b]})


def compare_d4(a: dict, b: dict) -> DimensionResult:
    features_a = a["D4"]["features"]
    features_b = b["D4"]["features"]
    gap = weighted_gap(features_a, features_b, dict(D4_FEATURE_WEIGHTS))
    metrics_a = a["metrics"]
    metrics_b = b["metrics"]
    high_social = metrics_a["social_energy"] >= PAIR_POLICY_THRESHOLDS["d4_high_social"]
    high_social_b = metrics_b["social_energy"] >= PAIR_POLICY_THRESHOLDS["d4_high_social"]
    high_density = metrics_a["social_density"] >= PAIR_POLICY_THRESHOLDS["d4_high_density"]
    high_density_b = metrics_b["social_density"] >= PAIR_POLICY_THRESHOLDS["d4_high_density"]
    fast_warm = features_a["warmup_speed"] >= PAIR_POLICY_THRESHOLDS["d4_fast_warm"]
    fast_warm_b = features_b["warmup_speed"] >= PAIR_POLICY_THRESHOLDS["d4_fast_warm"]
    productive_guard = (high_social and not high_social_b) or (high_social_b and not high_social) or (high_density and not high_density_b) or (high_density_b and not high_density) or (fast_warm and not fast_warm_b) or (fast_warm_b and not fast_warm)
    interference = ((metrics_a["social_energy"] >= PAIR_POLICY_THRESHOLDS["d4_interference_energy_a"] and features_a["social_replenishment"] >= PAIR_POLICY_THRESHOLDS["d4_interference_replenishment_high"]) and (metrics_b["social_energy"] <= PAIR_POLICY_THRESHOLDS["d4_interference_energy_b"] and features_b["social_replenishment"] <= PAIR_POLICY_THRESHOLDS["d4_interference_recovery_low"])) or ((metrics_b["social_energy"] >= PAIR_POLICY_THRESHOLDS["d4_interference_energy_a"] and features_b["social_replenishment"] >= PAIR_POLICY_THRESHOLDS["d4_interference_replenishment_high"]) and (metrics_a["social_energy"] <= PAIR_POLICY_THRESHOLDS["d4_interference_energy_b"] and features_a["social_replenishment"] <= PAIR_POLICY_THRESHOLDS["d4_interference_recovery_low"]))
    if interference and gap > 0.50:
        relationship, score = generic_continuous_evaluator(gap, productive_difference_policy=False, productive_guard=False, interference_policy=True)
    elif productive_guard and gap <= 0.70:
        relationship, score = generic_continuous_evaluator(gap, productive_difference_policy=True, productive_guard=True, interference_policy=False)
    elif gap <= 0.30:
        relationship, score = generic_continuous_evaluator(gap, productive_difference_policy=False, productive_guard=False, interference_policy=False)
    else:
        relationship, score = Relationship.NEUTRAL, 0.0
    return _result("D4", relationship, score, gap, {"gap": gap, "productive_guard": productive_guard, "interference_policy": interference})


def compare_d5(a: dict, b: dict) -> DimensionResult:
    features_a = a["D5"]["features"]
    features_b = b["D5"]["features"]
    gap = weighted_gap(features_a, features_b, dict(D5_FEATURE_WEIGHTS))
    category_pair = _pair("D5", a["D5"]["category"], b["D5"]["category"])
    direct_gap = abs(features_a["direct_expression"] - features_b["direct_expression"])
    delay_gap = abs(features_a["processing_delay"] - features_b["processing_delay"])
    if category_pair in D5_PRODUCTIVE_PAIRS and PAIR_POLICY_THRESHOLDS["d5_productive_gap_min"] < gap <= PAIR_POLICY_THRESHOLDS["d5_productive_gap_max"]:
        relationship = Relationship.COMPLEMENTARITY
        score = 0.25 + 0.24 * (1.0 - (gap - 0.30) / 0.20)
    elif gap <= PAIR_POLICY_THRESHOLDS["d5_alignment_gap_1"]:
        relationship = Relationship.ALIGNMENT
        score = 0.75 + 0.25 * (1.0 - gap / 0.15)
    elif gap <= PAIR_POLICY_THRESHOLDS["d5_alignment_gap_2"]:
        relationship = Relationship.ALIGNMENT
        score = 0.50 + 0.25 * (1.0 - (gap - 0.15) / 0.15)
    elif gap > 0.50:
        relationship, score = (Relationship.SOFT_FRICTION, -0.35) if gap < PAIR_POLICY_THRESHOLDS["d5_hard_gap"] else (Relationship.HARD_FRICTION, -0.55)
    else:
        relationship, score = Relationship.SOFT_FRICTION, -0.20
    computed_negative_score = max(0.0, -score)
    friction_score = computed_negative_score
    is_hard_friction = score <= THRESHOLDS["hard_friction"]
    high_salience = d5_high_salience(direct_gap, delay_gap, score)
    trace = {"gap": gap, "category_pair": sorted(category_pair), "direct_gap": direct_gap, "delay_gap": delay_gap, "computed_negative_score": computed_negative_score, "friction_score": friction_score, "is_hard_friction": is_hard_friction, "high_salience": high_salience}
    return DimensionResult("D5", relationship, score, gap, 1.0, trace=trace, computed_negative_score=computed_negative_score, friction_score=friction_score, is_hard_friction=is_hard_friction, high_salience=high_salience)


def compare_d8(a: dict, b: dict, *, d5_friction_score: float | None = None) -> DimensionResult:
    features_a = a["D8"]["features"]
    features_b = b["D8"]["features"]
    gap = weighted_gap(features_a, features_b, dict(D8_FEATURE_WEIGHTS))
    category_pair = _pair("D8", a["D8"]["category"], b["D8"]["category"])
    if category_pair in D8_HARD_PAIRS and gap >= PAIR_POLICY_THRESHOLDS["d8_hard_gap"]:
        return _result("D8", Relationship.HARD_FRICTION, -0.55, 0.80, {"gap": gap, "category_pair": sorted(category_pair)})
    if category_pair in D8_PRODUCTIVE_PAIRS and PAIR_POLICY_THRESHOLDS["d8_productive_gap_min"] < gap <= PAIR_POLICY_THRESHOLDS["d8_productive_gap_max"]:
        if category_pair == frozenset({"ACTION_FIRST", "PROCESS_FIRST"}):
            guard_friction = _guard_friction(d5_friction_score, "pair.D8.productive_guard")
            if guard_friction >= 0.50:
                return _result("D8", Relationship.NEUTRAL, 0.0, 0.20, {"gap": gap, "category_pair": sorted(category_pair), "productive_guard": False, "d5_friction_score": guard_friction})
        else:
            guard_friction = None
        score = 0.25 + 0.24 * (1.0 - (gap - 0.30) / 0.40)
        return _result("D8", Relationship.COMPLEMENTARITY, score, 0.40, {"gap": gap, "category_pair": sorted(category_pair), "productive_guard": True, "d5_friction_score": guard_friction})
    if gap <= PAIR_POLICY_THRESHOLDS["d5_alignment_gap_2"]:
        relationship, score = generic_continuous_evaluator(gap, productive_difference_policy=False, productive_guard=False, interference_policy=False)
        return _result("D8", relationship, score, gap, {"gap": gap, "category_pair": sorted(category_pair)})
    if category_pair in D8_HARD_PAIRS:
        relationship, score = generic_continuous_evaluator(gap, productive_difference_policy=False, productive_guard=False, interference_policy=True)
        return _result("D8", relationship, score, gap, {"gap": gap, "category_pair": sorted(category_pair)})
    return _result("D8", Relationship.NEUTRAL, 0.0, 0.20, {"gap": gap, "category_pair": sorted(category_pair)})


def compare_d9(a: dict, b: dict, d7: DimensionResult) -> DimensionResult:
    features_a = a["D9"]["scores"]
    features_b = b["D9"]["scores"]
    # D9 vector features are sourced from the raw/derived feature set, not the
    # seven categorical label scores.
    raw_a = a["D9"]["features"]
    raw_b = b["D9"]["features"]
    gap = weighted_gap(raw_a, raw_b, dict(D9_FEATURE_WEIGHTS))
    pair = _pair("D9", a["D9"]["primary"], b["D9"]["primary"])
    social_energy_gap = abs(a["D4"]["features"]["social_energy"] - b["D4"]["features"]["social_energy"])
    interference = social_energy_gap > PAIR_POLICY_THRESHOLDS["d9_energy_gap"] and d7.relationship in {Relationship.SOFT_FRICTION, Relationship.HARD_FRICTION}
    if interference:
        relationship, score = (Relationship.HARD_FRICTION, -0.55) if gap >= PAIR_POLICY_THRESHOLDS["d9_hard_gap"] else (Relationship.SOFT_FRICTION, -0.35)
    elif pair in D9_PRODUCTIVE_PAIRS and PAIR_POLICY_THRESHOLDS["d8_productive_gap_min"] < gap <= PAIR_POLICY_THRESHOLDS["d8_productive_gap_max"]:
        relationship, score = Relationship.COMPLEMENTARITY, 0.25 + 0.24 * (1.0 - (gap - 0.30) / 0.40)
    else:
        relationship, score = generic_continuous_evaluator(gap, productive_difference_policy=False, productive_guard=False, interference_policy=False)
    return _result("D9", relationship, score, gap, {"gap": gap, "category_pair": sorted(pair), "interference_policy": interference, "social_energy_gap": social_energy_gap})


def compare_all_dimensions(a: dict, b: dict) -> dict[str, DimensionResult]:
    results: dict[str, DimensionResult] = {}
    results["D1"] = compare_d1(a, b)
    results["D3"] = compare_d3(a, b)
    results["D4"] = compare_d4(a, b)
    results["D5"] = compare_d5(a, b)
    results["D2"] = compare_d2(a, b, d5_friction_score=results["D5"].friction_score)
    results["D6"] = compare_d6(a, b)
    results["D7"] = compare_d7(a, b)
    results["D8"] = compare_d8(a, b, d5_friction_score=results["D5"].friction_score)
    results["D9"] = compare_d9(a, b, results["D7"])
    results["D10"] = compare_d10(a, b)
    return results
