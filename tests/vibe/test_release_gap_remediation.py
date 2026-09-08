from __future__ import annotations

import copy
import json
from types import MappingProxyType

import pytest

from app.vibe.config import v1_1_0 as config
from app.vibe.confidence import confidence_label, section_confidence
from app.vibe.contracts import Chemistry, ConfigurationError, DimensionResult, Relationship, SpecificationGap
from app.vibe.contrast import build_contrast_analysis, contrast_is_bounded, contrast_score
from app.vibe.narrative import validate_llm_output
from app.vibe.pair.aggregate import classify, friction_counts
from app.vibe.pair.evidence import select_evidence
from app.vibe.pair.modes import config_hash, validate_configuration, wildcard_effective_weights
from app.vibe.pair.continuous import relationship_from_interaction
from app.vibe.profile import build_partial_profile, profile_version
from app.vibe.wildcard import build_wildcard_candidate, materialize_wildcard_candidates, perturb_signals, select_wildcard_from_candidates


def answers(**overrides: str) -> dict[str, str]:
    result = {f"Q{i}": f"Q{i}_A" for i in range(1, 11)}
    result.update(overrides)
    return result


def test_valid_wildcard_configuration_is_dedicated_and_normalized() -> None:
    validate_configuration()
    weights = wildcard_effective_weights()
    assert set(weights) == set(config.WILDCARD_DIMENSION_ORDER) | {"D10"}
    assert weights["D10"] == 0.0
    assert sum(weights[dimension] for dimension in config.WILDCARD_DIMENSION_ORDER) == pytest.approx(9.30 / 10.30)
    assert config.WILDCARD_WEIGHT_DENOMINATOR == pytest.approx(10.30)
    assert config.WILDCARD_SCORING_CONFIG_VERSION == "1.0"


def test_canonical_signal_mapping_persists_complete_continuous_vector() -> None:
    profile = build_partial_profile("complete-signals", answers())
    assert set(config.CONTINUOUS_SIGNAL_NAMES).issubset(profile["signals"]["signals"])


@pytest.mark.parametrize("missing", ["social_energy", "social_energy,energy_contribution"])
def test_missing_wildcard_signals_fail_closed(missing: str) -> None:
    profile = build_partial_profile("missing", answers())
    for signal in missing.split(","):
        del profile["signals"]["signals"][signal]
    with pytest.raises(SpecificationGap) as error:
        perturb_signals(profile, "HIGHER_ENERGY")
    assert error.value.path.startswith("wildcard.candidate_generation.required_signal.")


def test_missing_wildcard_signal_object_fails_closed() -> None:
    profile = build_partial_profile("missing-object", answers())
    del profile["signals"]["signals"]
    with pytest.raises(SpecificationGap) as error:
        perturb_signals(profile, "HIGHER_ENERGY")
    assert error.value.path == "wildcard.candidate_generation.signal_object.signals"


def test_malformed_wildcard_configuration_is_rejected_before_calculation(monkeypatch: pytest.MonkeyPatch) -> None:
    malformed = dict(config.WILDCARD_DELTAS)
    malformed["HIGHER_ENERGY"] = MappingProxyType({"not_a_signal": 0.30})
    monkeypatch.setattr(config, "WILDCARD_DELTAS", malformed)
    with pytest.raises(ConfigurationError) as error:
        validate_configuration()
    assert error.value.code == "ENGINE_CONFIG_INVALID"
    assert error.value.path == "wildcard_deltas.HIGHER_ENERGY.not_a_signal"


@pytest.mark.parametrize(
    ("attribute", "value", "path"),
    [
        ("WILDCARD_EFFECTIVE_WEIGHTS", {"D1": 1.0}, "wildcard_effective_weights"),
        ("WILDCARD_WEIGHT_DENOMINATOR", "bad", "wildcard_weight_denominator"),
        ("WILDCARD_DELTAS", None, "wildcard_deltas"),
        ("WILDCARD_THRESHOLDS", {"difference": "bad"}, "wildcard_thresholds"),
        ("CONTRAST_PROTOTYPES", {"HIGH_ENERGY": ("Q1_A",)}, "contrast_prototypes"),
    ],
)
def test_malformed_required_configuration_blocks_fail_closed(monkeypatch: pytest.MonkeyPatch, attribute: str, value: object, path: str) -> None:
    monkeypatch.setattr(config, attribute, value)
    with pytest.raises(ConfigurationError) as error:
        validate_configuration()
    assert error.value.code == "ENGINE_CONFIG_INVALID"
    assert error.value.path.startswith(path)


def test_malformed_mode_multiplier_is_rejected_before_weight_calculation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "MODE_MULTIPLIERS", {"DATE": None})
    with pytest.raises(ConfigurationError) as error:
        validate_configuration()
    assert error.value.code == "ENGINE_CONFIG_INVALID"
    assert error.value.path == "mode_multipliers.DATE"


def test_missing_matrix_entry_is_rejected_before_calculation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "D1_MATRIX", {"INTELLECTUAL": {}})
    with pytest.raises(ConfigurationError) as error:
        validate_configuration()
    assert error.value.code == "ENGINE_CONFIG_INVALID"
    assert error.value.path == "D1_MATRIX.INTELLECTUAL.INTELLECTUAL"


def test_all_wildcard_archetypes_are_deterministic_and_scored() -> None:
    profile = build_partial_profile("wildcard", answers())
    first = materialize_wildcard_candidates(profile)
    second = materialize_wildcard_candidates(profile)
    assert json.dumps(first, sort_keys=True, separators=(",", ":")) == json.dumps(second, sort_keys=True, separators=(",", ":"))
    assert [candidate["archetype"] for candidate in first] == list(config.WILDCARD_ORDER)
    for candidate in first:
        assert candidate["scoring_mode"] == "WILDCARD"
        assert candidate["wildcard_scoring_config_version"] == config.WILDCARD_SCORING_CONFIG_VERSION
        assert set(candidate["derived"]) == set(profile["derived"])
        assert 0.0 <= candidate["difference_score"] <= 1.0
        assert 0.0 <= candidate["complementarity_score"] <= 1.0
        assert 0.0 <= candidate["friction_score"] <= 1.0
        expected_score = candidate["difference_score"] * candidate["complementarity_score"] * (1.0 - candidate["friction_score"])
        selected = select_wildcard_from_candidates([candidate])
        if selected is not None:
            assert selected["wildcard_score"] == pytest.approx(expected_score)


def test_wildcard_exact_delta_and_clamping_edges() -> None:
    profile = build_partial_profile("wildcard-edges", answers())
    for archetype, deltas in config.WILDCARD_DELTAS.items():
        base = dict(profile["signals"]["signals"])
        for signal, delta in deltas.items():
            base[signal] = 1.0 if delta > 0 else 0.0
        edge_profile = copy.deepcopy(profile)
        edge_profile["signals"]["signals"] = base
        candidate = perturb_signals(edge_profile, archetype)
        for signal, delta in deltas.items():
            assert candidate[signal] == pytest.approx(max(0.0, min(1.0, base[signal] + delta)))


def test_wildcard_eligibility_boundaries_and_safety() -> None:
    epsilon = 1e-6
    base = {"archetype": "HIGHER_ENERGY", "difference_score": 0.30, "complementarity_score": 0.35, "hard_friction_count": 0}
    below_difference = {**base, "difference_score": 0.30 - epsilon, "friction_score": 0.10}
    exact = {**base, "friction_score": 0.35 - epsilon}
    above_friction = {**base, "friction_score": 0.35}
    assert select_wildcard_from_candidates([below_difference]) is None
    assert select_wildcard_from_candidates([exact]) is not None
    assert select_wildcard_from_candidates([above_friction]) is None
    assert select_wildcard_from_candidates([{**exact, "hard_friction_count": 1}]) is None


def test_contrast_omission_threshold_has_below_exact_above_cases() -> None:
    epsilon = 1e-6
    assert contrast_is_bounded(0.30 - epsilon) is True
    assert contrast_is_bounded(0.30) is False
    assert contrast_is_bounded(0.30 + epsilon) is False
    assert contrast_score(0.30, 0.30) == pytest.approx(0.30)


def test_all_contrast_prototypes_are_deterministic_and_never_classified() -> None:
    profile = build_partial_profile("contrast", answers())
    first = build_contrast_analysis(profile)
    second = build_contrast_analysis(profile)
    assert json.dumps(first, sort_keys=True, separators=(",", ":")) == json.dumps(second, sort_keys=True, separators=(",", ":"))
    assert len(first) == 4
    assert all(item["chemistry"] is None for item in first)


def test_profile_version_changes_when_wildcard_configuration_changes(monkeypatch: pytest.MonkeyPatch) -> None:
    before_hash = config_hash()
    before_version = profile_version(answers())
    changed = dict(config.WILDCARD_MULTIPLIERS)
    changed["D1"] = 1.01
    monkeypatch.setattr(config, "WILDCARD_MULTIPLIERS", changed)
    after_hash = config_hash()
    after_version = profile_version(answers())
    assert before_hash != after_hash
    assert before_version != after_version


def test_confidence_boundaries_and_no_evidence_are_deterministic() -> None:
    epsilon = 1e-6
    assert section_confidence([]) == pytest.approx((0.0 + 0.25 + 0.0) / 3.0)
    assert confidence_label(0.50 - epsilon).value == "WEAK"
    assert confidence_label(0.50).value == "MODERATE"
    assert confidence_label(0.70 - epsilon).value == "MODERATE"
    assert confidence_label(0.70).value == "STRONG"
    assert confidence_label(0.85 - epsilon).value == "STRONG"
    assert confidence_label(0.85).value == "VERY_STRONG"


def test_llm_claim_envelope_rejects_valid_evidence_with_unsupported_prose() -> None:
    pair = {
        "confidence": {"label": "VERY_STRONG"},
        "evidence": [{"evidence_id": "D1:positive", "statement_key": "positive_D1"}],
    }
    with pytest.raises(Exception) as error:
        validate_llm_output(
            {"title": "Mind reader", "explanation": "You can read minds.", "evidence_ids": ["D1:positive"]},
            pair,
        )
    assert error.value.code == "NARRATIVE_RENDER_ERROR"
    with pytest.raises(Exception) as error:
        validate_llm_output(
            {"title": "Grounded", "explanation": "The evidence supports that you are a genius.", "claim_keys": ["positive_D1"], "evidence_ids": ["D1:positive"]},
            pair,
        )
    assert error.value.code == "NARRATIVE_RENDER_ERROR"
    with pytest.raises(Exception) as error:
        validate_llm_output(
            {"title": "Unsupported", "explanation": "Unsupported trait.", "claim_keys": ["invented"], "evidence_ids": ["D1:positive"]},
            pair,
        )
    assert error.value.code == "NARRATIVE_RENDER_ERROR"


def _classify(final: float, alignment: float, complementarity: float, friction: float, productive: int = 1, hard: int = 0, reinforced: int = 0) -> tuple[Chemistry, bool]:
    return classify(
        {"alignment_score": alignment, "complementarity_score": complementarity, "friction_score": friction},
        {"final_score_internal": final},
        {"productive_difference_count": productive, "hard_friction_count": hard, "reinforced_friction_group_count": reinforced},
    )


@pytest.mark.parametrize("threshold", (0.45, 0.65))
def test_classification_final_boundaries(threshold: float) -> None:
    epsilon = 1e-6
    if threshold == 0.45:
        below = _classify(threshold - epsilon, 0.0, 0.35, 0.10)
        exact = _classify(threshold, 0.0, 0.35, 0.10)
        above = _classify(threshold + epsilon, 0.0, 0.35, 0.10)
        assert below == (Chemistry.INTERESTING_CHEMISTRY, True)
        assert exact == (Chemistry.INTERESTING_CHEMISTRY, False)
        assert above == (Chemistry.INTERESTING_CHEMISTRY, False)
    else:
        below = _classify(threshold - epsilon, 0.60, 0.0, 0.10, productive=0)
        exact = _classify(threshold, 0.60, 0.0, 0.10, productive=0)
        above = _classify(threshold + epsilon, 0.60, 0.0, 0.10, productive=0)
        assert below == (Chemistry.NATURAL_CLICK, True)
        assert exact == (Chemistry.NATURAL_CLICK, False)
        assert above == (Chemistry.NATURAL_CLICK, False)


def test_classification_alignment_complementarity_and_friction_boundaries() -> None:
    epsilon = 1e-6
    assert relationship_from_interaction(0.50 - epsilon) != Relationship.ALIGNMENT
    assert relationship_from_interaction(0.50) == Relationship.ALIGNMENT
    assert relationship_from_interaction(0.50 + epsilon) == Relationship.ALIGNMENT
    assert _classify(0.70, 0.55 - epsilon, 0.0, 0.10, productive=0)[1] is True
    assert _classify(0.70, 0.55, 0.0, 0.10, productive=0)[1] is False
    assert _classify(0.70, 0.55 + epsilon, 0.0, 0.10, productive=0)[1] is False
    assert _classify(0.45, 0.0, 0.25 - epsilon, 0.10)[0] == Chemistry.NATURAL_CLICK
    assert _classify(0.45, 0.0, 0.25, 0.10)[0] == Chemistry.INTERESTING_CHEMISTRY
    assert _classify(0.50, 0.0, 0.35 - epsilon, 0.10)[1] is True
    assert _classify(0.50, 0.0, 0.35, 0.10)[1] is False
    assert _classify(0.70, 0.60, 0.0, 0.35 - epsilon, productive=0)[1] is False
    assert _classify(0.70, 0.60, 0.0, 0.35, productive=0)[1] is True
    assert _classify(0.70, 0.60, 0.0, 0.50 - epsilon, productive=0)[0] == Chemistry.NATURAL_CLICK
    assert _classify(0.70, 0.60, 0.0, 0.50, productive=0)[0] == Chemistry.POTENTIAL_FRICTION
    assert _classify(0.70, 0.60, 0.0, 0.50 + epsilon, productive=0)[0] == Chemistry.POTENTIAL_FRICTION


def test_classification_final_055_and_alignment_065_boundaries() -> None:
    epsilon = 1e-6
    assert _classify(0.55 - epsilon, 0.0, 0.0, 0.10, productive=0, hard=1, reinforced=1) == (Chemistry.POTENTIAL_FRICTION, False)
    assert _classify(0.55, 0.0, 0.0, 0.10, productive=0, hard=1, reinforced=1) == (Chemistry.POTENTIAL_FRICTION, True)
    assert _classify(0.55 + epsilon, 0.0, 0.0, 0.10, productive=0, hard=1, reinforced=1) == (Chemistry.POTENTIAL_FRICTION, True)

    from app.vibe.config.v1_1_0 import DIMENSION_ORDER

    def results(score: float) -> dict[str, DimensionResult]:
        return {
            dimension: DimensionResult(
                dimension,
                Relationship.ALIGNMENT if dimension == "D1" else Relationship.NEUTRAL,
                score if dimension == "D1" else 0.0,
                0.0,
                1.0,
            )
            for dimension in DIMENSION_ORDER
        }

    weights = wildcard_effective_weights()
    assert select_evidence(results(0.65 - epsilon), weights, {d: {} for d in DIMENSION_ORDER}, {d: {} for d in DIMENSION_ORDER})[0] == []
    assert select_evidence(results(0.65), weights, {d: {} for d in DIMENSION_ORDER}, {d: {} for d in DIMENSION_ORDER})[0]
    assert select_evidence(results(0.65 + epsilon), weights, {d: {} for d in DIMENSION_ORDER}, {d: {} for d in DIMENSION_ORDER})[0]


def test_productive_difference_and_hard_count_boundaries() -> None:
    results: dict[str, DimensionResult] = {}
    for dimension in (f"D{i}" for i in range(1, 11)):
        results[dimension] = DimensionResult(dimension, Relationship.NEUTRAL, 0.0, 0.0, 1.0)
    results["D1"] = DimensionResult("D1", Relationship.COMPLEMENTARITY, 0.25, 0.30, 1.0)
    assert friction_counts(results)["productive_difference_count"] == 1
    results["D1"] = DimensionResult("D1", Relationship.COMPLEMENTARITY, 0.25, 0.30 - 1e-6, 1.0)
    assert friction_counts(results)["productive_difference_count"] == 0
    assert _classify(0.70, 0.60, 0.0, 0.10, productive=0, hard=0)[0] == Chemistry.NATURAL_CLICK
    assert _classify(0.70, 0.60, 0.0, 0.10, productive=0, hard=1)[0] == Chemistry.POTENTIAL_FRICTION
    assert _classify(0.70, 0.60, 0.0, 0.10, productive=0, hard=2)[0] == Chemistry.POTENTIAL_FRICTION


def test_pair_evidence_high_alignment_boundary_and_no_evidence() -> None:
    from app.vibe.config.v1_1_0 import DIMENSION_ORDER

    def make_results(score: float) -> dict[str, DimensionResult]:
        return {
            dimension: DimensionResult(
                dimension,
                Relationship.ALIGNMENT if dimension == "D1" else Relationship.NEUTRAL,
                score if dimension == "D1" else 0.0,
                0.0,
                1.0,
            )
            for dimension in DIMENSION_ORDER
        }

    weights = wildcard_effective_weights()
    empty, confidence = select_evidence(make_results(0.0), weights, {d: {} for d in DIMENSION_ORDER}, {d: {} for d in DIMENSION_ORDER})
    assert empty == [] and confidence == 0.0
    assert select_evidence(make_results(0.65 - 1e-6), weights, {d: {} for d in DIMENSION_ORDER}, {d: {} for d in DIMENSION_ORDER})[0] == []
    selected, _ = select_evidence(make_results(0.65), weights, {d: {} for d in DIMENSION_ORDER}, {d: {} for d in DIMENSION_ORDER})
    assert selected and selected[0].dimension == "D1"
