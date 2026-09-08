from __future__ import annotations

import pytest

from app.vibe.contracts import Chemistry, Relationship, SpecificationGap
from app.vibe.pair.aggregate import classify, component_scores, final_scores, friction_counts
from app.vibe.pair.dimensions import compare_d1, compare_d6, compare_d7
from app.vibe.pair.engine import analyze_pair
from app.vibe.pair.modes import effective_mode_weights, validate_configuration
from app.vibe.profile import build_partial_profile
from app.vibe.questionnaire import validate_answers
from app.vibe.signal_map import map_answers_to_signals
from app.vibe.wildcard import select_wildcard_from_candidates


def answers(**overrides: str) -> dict[str, str]:
    result = {f"Q{i}": f"Q{i}_A" for i in range(1, 11)}
    result.update(overrides)
    return result


def test_q1_a_exact_six_raw_signals() -> None:
    raw = map_answers_to_signals(answers())["per_question"]["Q1"]
    assert raw == {
        "social_energy": 1.00,
        "social_density": 1.00,
        "group_orientation": 1.00,
        "one_to_one_preference": 0.25,
        "solitude_preference": 0.00,
        "external_stimulation": 1.00,
    }


def test_q4_d_exact_five_raw_signals() -> None:
    raw = map_answers_to_signals(answers(Q4="Q4_D"))["per_question"]["Q4"]
    assert raw == {
        "social_presence": 0.30,
        "energy_contribution": 0.20,
        "relaxed_presence": 0.55,
        "humor_presence": 0.20,
        "attentional_presence": 1.00,
    }


def test_q5_d_and_q6_c_and_q7_d_are_controlled_categories() -> None:
    raw = map_answers_to_signals(answers(Q5="Q5_D", Q6="Q6_C", Q7="Q7_D"))
    assert raw["question_categories"]["Q5"] == "PRESSURED"
    assert raw["per_question"]["Q5"]["future_pressure"] == "HIGH"
    assert raw["question_categories"]["Q6"] == "ACTION_RESPONSE"
    assert "avoidant" not in str(raw).lower()
    assert raw["question_categories"]["Q7"] == "ATTENTIVE"
    assert "receiving" not in str(raw).lower()


def test_incomplete_and_unknown_answers_fail_closed() -> None:
    with pytest.raises(Exception) as missing:
        validate_answers({key: value for key, value in answers().items() if key != "Q10"})
    assert missing.value.code == "INCOMPLETE_ASSESSMENT"
    with pytest.raises(Exception) as unknown:
        validate_answers(answers(Q3="Q3_Z"))
    assert unknown.value.code == "INVALID_ANSWER_CODE"


def test_canonical_categorical_matrices_and_hard_boundaries() -> None:
    a = build_partial_profile("a", answers(Q2="Q2_C", Q8="Q8_A", Q9="Q9_A"))
    b = build_partial_profile("b", answers(Q2="Q2_C", Q8="Q8_C", Q9="Q9_B"))
    assert compare_d1(a["derived"], b["derived"]).interaction_score == 0.95
    assert compare_d6(a["derived"], b["derived"]).interaction_score == -0.80
    assert compare_d7(a["derived"], b["derived"]).interaction_score == -0.60

    c = build_partial_profile("c", answers(Q2="Q2_A"))
    d = build_partial_profile("d", answers(Q2="Q2_D"))
    assert compare_d1(c["derived"], d["derived"]).interaction_score == -0.55
    assert compare_d1(c["derived"], d["derived"]).relationship == Relationship.HARD_FRICTION


def test_mode_weights_match_canonical_date_fixture() -> None:
    validate_configuration()
    weights = effective_mode_weights("DATE")
    assert weights["D1"] == pytest.approx(0.152517, abs=1e-6)
    assert weights["D9"] == pytest.approx(0.077783, abs=1e-6)
    assert sum(weights.values()) == pytest.approx(1.0)


def test_same_pair_is_symmetric_and_modes_are_explicit() -> None:
    a = build_partial_profile("a", answers(Q2="Q2_C", Q4="Q4_A"))
    b = build_partial_profile("b", answers(Q2="Q2_D", Q4="Q4_B", Q8="Q8_B"))
    date_ab = analyze_pair(a, b, "DATE")
    date_ba = analyze_pair(b, a, "DATE")
    for field in ("alignment_score", "complementarity_score", "friction_score", "final_score_internal", "phase_adjustment", "classification"):
        assert date_ab[field] == date_ba[field]
    friend = analyze_pair(a, b, "FRIEND")
    hangout = analyze_pair(a, b, "HANGOUT")
    assert {friend["final_score_internal"], hangout["final_score_internal"], date_ab["final_score_internal"]}


def test_final_score_formula_and_friction_override() -> None:
    scores = final_scores({"alignment_score": 0.82, "complementarity_score": 0.18, "friction_score": 0.12}, 0.05)
    assert scores["raw_final"] == pytest.approx(0.383)
    assert scores["final_score_internal"] == pytest.approx(0.7781481481481482)
    chemistry, fallback = classify({"alignment_score": 0.82, "complementarity_score": 0.18, "friction_score": 0.12}, scores, {"hard_friction_count": 0, "reinforced_friction_group_count": 0, "productive_difference_count": 0})
    assert chemistry == Chemistry.NATURAL_CLICK
    assert fallback is False

    potential_scores = final_scores({"alignment_score": 0.90, "complementarity_score": 0.90, "friction_score": 0.50}, 0.05)
    chemistry, _ = classify({"alignment_score": 0.90, "complementarity_score": 0.90, "friction_score": 0.50}, potential_scores, {"hard_friction_count": 0, "reinforced_friction_group_count": 0, "productive_difference_count": 2})
    assert chemistry == Chemistry.POTENTIAL_FRICTION


def test_wildcard_safety_and_tie_break() -> None:
    assert select_wildcard_from_candidates(
        [{"archetype": "HIGHER_ENERGY", "difference_score": 0.30, "complementarity_score": 0.35, "friction_score": 0.35, "hard_friction_count": 0}]
    ) is None
    selected = select_wildcard_from_candidates(
        [
            {"archetype": "MORE_DIRECT", "difference_score": 0.50, "complementarity_score": 0.50, "friction_score": 0.10, "hard_friction_count": 0},
            {"archetype": "HIGHER_ENERGY", "difference_score": 0.50, "complementarity_score": 0.50, "friction_score": 0.10, "hard_friction_count": 0},
        ]
    )
    assert selected is not None
    assert selected["archetype"] == "HIGHER_ENERGY"
    with pytest.raises(SpecificationGap):
        from app.vibe.wildcard import select_wildcard

        select_wildcard({})
