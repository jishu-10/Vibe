from __future__ import annotations

import pytest

from app.vibe.config.v1_1_0 import CONTRAST_NORMALIZED_WEIGHTS, CONTRAST_PROTOTYPES, WILDCARD_DELTAS
from app.vibe.confidence import confidence_label, continuous_strength, profile_confidence, section_confidence, strong_profile_claim_allowed
from app.vibe.contracts import SpecificationGap
from app.vibe.contrast import build_contrast_analysis, contrast_prototype, contrast_score
from app.vibe.pair.dimensions import compare_d5, d5_high_salience
from app.vibe.profile import build_partial_profile, build_profile
from app.vibe.wildcard import build_wildcard_candidate, materialize_wildcard_candidates, perturb_signals, select_wildcard_from_candidates


def answers(**overrides: str) -> dict[str, str]:
    result = {f"Q{i}": f"Q{i}_A" for i in range(1, 11)}
    result.update(overrides)
    return result


def d5(features: dict[str, float], category: str = "DIRECT_PROCESSOR") -> dict:
    return {"D5": {"category": category, "features": features}}


def test_ga_d5_01_to_05_inclusive_predicate_and_strict_failures() -> None:
    assert d5_high_salience(0.55, 0.50, -0.50) is True
    assert d5_high_salience(0.549999, 0.50, -0.50) is False
    assert d5_high_salience(0.55, 0.499999, -0.50) is False
    assert d5_high_salience(0.55, 0.50, -0.499999) is False
    assert d5_high_salience(0.70, 0.60, -0.70) is True


def test_ga_d5_06_and_07_result_exposes_amended_friction_fields() -> None:
    result = compare_d5(
        d5({"direct_expression": 1.0, "processing_delay": 1.0, "action_response": 1.0, "context_sensitivity": 1.0}),
        d5({"direct_expression": 0.0, "processing_delay": 0.0, "action_response": 0.0, "context_sensitivity": 0.0}, "PROCESS_THEN_TALK"),
    )
    assert result.computed_negative_score == max(0.0, -result.interaction_score)
    assert result.friction_score == result.computed_negative_score
    assert result.is_hard_friction is (result.interaction_score <= -0.50)
    assert result.high_salience is True
    assert result.as_dict()["trace"]["computed_negative_score"] == result.computed_negative_score


def test_ga_wildcard_01_to_03_exact_deltas_and_clamp() -> None:
    profile = build_partial_profile("u", answers())
    base = profile["signals"]["signals"]
    higher = perturb_signals(profile, "HIGHER_ENERGY")
    assert higher["social_energy"] == min(1.0, base.get("social_energy", 0.0) + 0.30)
    assert higher["energy_contribution"] == min(1.0, base.get("energy_contribution", 0.0) + 0.15)
    assert higher["social_presence"] == min(1.0, base.get("social_presence", 0.0) + 0.15)
    direct = perturb_signals(profile, "MORE_DIRECT")
    assert direct["direct_expression"] == min(1.0, base.get("direct_expression", 0.0) + 0.30)
    assert all(0.0 <= value <= 1.0 for value in higher.values())
    candidate = build_wildcard_candidate(profile, "MORE_SOCIAL")
    assert candidate["ephemeral"] is True
    assert candidate["signals"]["question_categories"] == profile["signals"]["question_categories"]
    assert set(candidate["derived"]) == set(profile["derived"])


def test_ga_wildcard_04_to_08_fixed_set_safety_and_ranking() -> None:
    profile = build_partial_profile("u", answers())
    candidates = materialize_wildcard_candidates(profile)
    assert [candidate["archetype"] for candidate in candidates] == list(WILDCARD_DELTAS)
    assert select_wildcard_from_candidates([
        {"archetype": "HIGHER_ENERGY", "difference_score": 0.30, "complementarity_score": 0.35, "friction_score": 0.35, "hard_friction_count": 0}
    ]) is None
    selected = select_wildcard_from_candidates([
        {"archetype": "MORE_DIRECT", "difference_score": 0.50, "complementarity_score": 0.50, "friction_score": 0.10, "hard_friction_count": 0},
        {"archetype": "HIGHER_ENERGY", "difference_score": 0.50, "complementarity_score": 0.50, "friction_score": 0.10, "hard_friction_count": 0},
    ])
    assert selected is not None and selected["archetype"] == "HIGHER_ENERGY"
    assert select_wildcard_from_candidates([
        {"archetype": "HIGHER_ENERGY", "difference_score": 0.50, "complementarity_score": 0.50, "friction_score": 0.10, "hard_friction_count": 1}
    ]) is None


def test_ga_contrast_01_to_05_formula_weights_prototypes_and_omission() -> None:
    assert CONTRAST_PROTOTYPES.keys() == {"HIGH_ENERGY", "VERY_QUIET", "HIGHLY_STRUCTURED", "HIGHLY_SPONTANEOUS"}
    assert CONTRAST_NORMALIZED_WEIGHTS["D1"] == pytest.approx(0.10679611650485436)
    assert sum(CONTRAST_NORMALIZED_WEIGHTS.values()) == pytest.approx(0.9029126213592233)
    assert contrast_score(0.40, 0.80) == pytest.approx(0.52)
    analyses = build_contrast_analysis(build_partial_profile("u", answers()))
    assert len(analyses) == 4
    assert all("chemistry" in item and item["chemistry"] is None for item in analyses)
    assert all("dimension_values" in item for item in analyses)
    assert all(item["omission_threshold"] is (item["contrast_score"] < 0.30) for item in analyses)
    from app.vibe.contrast import _rank_dimensions
    tied = {dimension: {"evidence_priority": 1.0, "confidence": 1.0, "difference": 1.0} for dimension in ("D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9")}
    assert _rank_dimensions(tied)[:3] == ["D4", "D1", "D6"]


def test_ga_confidence_01_to_05_evidence_count_strength_and_consistency() -> None:
    assert continuous_strength(0.0) == 1.0
    assert continuous_strength(0.5) == 0.0
    assert continuous_strength(1.0) == 1.0
    assert section_confidence([]) == pytest.approx((0.0 + 0.25 + 0.0) / 3.0)
    assert section_confidence([{"source": "Q1", "polarity": "SUPPORT", "strength_value": 1.0}]) == pytest.approx((0.50 + 1.0 + 0.75) / 3.0)
    assert section_confidence([
        {"source": "Q1", "polarity": "SUPPORT", "strength_value": 0.40},
        {"source": "Q2", "polarity": "SUPPORT", "strength_value": 0.40},
    ]) == pytest.approx((0.75 + 0.50 + 1.0) / 3.0)
    assert confidence_label(0.499999).value == "WEAK"
    assert confidence_label(0.50).value == "MODERATE"
    assert confidence_label(0.70).value == "STRONG"
    assert confidence_label(0.85).value == "VERY_STRONG"


def test_ga_confidence_06_to_12_unique_units_boundaries_and_profile_mean() -> None:
    duplicate = [
        {"source": "Q1", "polarity": "SUPPORT", "strength_value": 1.0},
        {"source": "Q1", "polarity": "CONTRADICT", "strength_value": 0.0},
    ]
    assert section_confidence(duplicate) == pytest.approx((0.50 + 1.0 + 0.75) / 3.0)
    units = {f"D{i}": [{"source": f"Q{i}", "polarity": "SUPPORT", "strength_value": 1.0}] for i in range(1, 11)}
    values = {dimension: section_confidence(items) for dimension, items in units.items()}
    profile_value, label = profile_confidence(values)
    assert 0.0 <= profile_value <= 1.0
    assert label.value in {"STRONG", "VERY_STRONG"}
    assert strong_profile_claim_allowed(values["D1"], units["D1"]) is True
    with pytest.raises(SpecificationGap):
        section_confidence([{"source": "Q1", "strength_value": 1.0}])
    with pytest.raises(SpecificationGap):
        section_confidence([{"source": "Q1", "polarity": "SUPPORT"}])


def test_amendment_typed_errors_for_unknown_contrast_and_missing_guards() -> None:
    with pytest.raises(Exception) as error:
        contrast_prototype("UNKNOWN")
    assert error.value.code == "ENGINE_CONFIG_INVALID"


def test_amendment_profile_has_all_named_sections_and_version_metadata() -> None:
    profile = build_profile("u", answers())
    assert set(profile["facts"]) == {"your_vibe", "social_rhythm", "connection_style", "energy_signature", "what_pulls_you_in", "what_drains_you", "current_phase", "how_you_are_with_different_people", "wildcard"}
    assert len(profile["facts"]["how_you_are_with_different_people"]) == 4
    assert "completion_amendment" in profile["engine_versions"]
    assert profile["profile_narrative"]["generated_by"] == "deterministic_fallback"
