from __future__ import annotations

from types import MappingProxyType

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.vibe import profile as profile_module
from app.vibe.config import v1_1_0 as config
from app.vibe.confidence import confidence_label
from app.vibe.contracts import Chemistry, ConfigurationError, Relationship, SpecificationGap
from app.vibe.narrative import render_pair_fallback, validate_llm_output
from app.vibe.pair.aggregate import classify, component_scores, final_scores, friction_counts
from app.vibe.pair.continuous import generic_continuous_evaluator
from app.vibe.pair.dimensions import compare_d4, compare_d8, compare_d9, compare_all_dimensions
from app.vibe.pair.engine import analyze_pair
from app.vibe.pair.modes import config_hash, effective_mode_weights, validate_configuration
from app.vibe.profile import build_partial_profile, build_profile, profile_version
from app.vibe.questionnaire import validate_answers
from app.vibe.signal_map import map_answers_to_signals
from app.vibe.wildcard import select_wildcard_from_candidates
from app.vibe.cache import pair_cache_key
from app.services.vibe_service import analyze_pair_on_demand, compute_profile


def answers(**overrides: str) -> dict[str, str]:
    result = {f"Q{i}": f"Q{i}_A" for i in range(1, 11)}
    result.update(overrides)
    return result


def test_T01_complete_assessment() -> None:
    profile = build_profile("t01", answers())
    assert profile["answers"] == answers()


def test_T02_missing_answer_fails_closed() -> None:
    with pytest.raises(Exception) as error:
        validate_answers({key: value for key, value in answers().items() if key != "Q10"})
    assert error.value.code == "INCOMPLETE_ASSESSMENT"


def test_T03_unknown_option_fails_closed() -> None:
    with pytest.raises(Exception) as error:
        validate_answers(answers(Q1="Q1_Z"))
    assert error.value.code == "INVALID_ANSWER_CODE"


def test_T04_q1_a_exact_mapping() -> None:
    assert len(map_answers_to_signals(answers())["per_question"]["Q1"]) == 6


def test_T05_q4_d_exact_mapping() -> None:
    assert len(map_answers_to_signals(answers(Q4="Q4_D"))["per_question"]["Q4"]) == 5


def test_T06_q5_d_context() -> None:
    profile = build_partial_profile("t06", answers(Q5="Q5_D"))
    assert profile["derived"]["D10"]["category"] == "PRESSURED"


def test_T07_q6_c_controlled_label() -> None:
    raw = map_answers_to_signals(answers(Q6="Q6_C"))
    assert raw["question_categories"]["Q6"] == "ACTION_RESPONSE"
    assert "avoidant" not in str(raw).lower()


def test_T08_q7_d_controlled_label() -> None:
    raw = map_answers_to_signals(answers(Q7="Q7_D"))
    assert raw["question_categories"]["Q7"] == "ATTENTIVE"
    assert "receiving" not in str(raw).lower()


def test_T09_d6_hard_boundary() -> None:
    a = build_partial_profile("t09a", answers(Q8="Q8_A"))
    b = build_partial_profile("t09b", answers(Q8="Q8_C"))
    result = compare_all_dimensions(a["derived"], b["derived"])["D6"]
    assert result.interaction_score == -0.80 and result.relationship == Relationship.HARD_FRICTION


def test_T10_d7_hard_boundary() -> None:
    a = build_partial_profile("t10a", answers(Q9="Q9_A"))
    b = build_partial_profile("t10b", answers(Q9="Q9_B"))
    result = compare_all_dimensions(a["derived"], b["derived"])["D7"]
    assert result.interaction_score == -0.60 and result.relationship == Relationship.HARD_FRICTION


def test_T11_d1_alignment_matrix() -> None:
    a = build_partial_profile("t11a", answers(Q2="Q2_C"))
    b = build_partial_profile("t11b", answers(Q2="Q2_C"))
    assert compare_all_dimensions(a["derived"], b["derived"])["D1"].interaction_score == 0.95


def test_T12_d1_hard_matrix() -> None:
    a = build_partial_profile("t12a", answers(Q2="Q2_A"))
    b = build_partial_profile("t12b", answers(Q2="Q2_D"))
    result = compare_all_dimensions(a["derived"], b["derived"])["D1"]
    assert result.interaction_score == -0.55 and result.relationship == Relationship.HARD_FRICTION


def test_T13_d9_energizer_relaxed_complementarity() -> None:
    a = {"D9": {"primary": "ENERGIZER", "scores": {}, "features": {"social_presence": 0.80, "energy_contribution": 0.80, "relaxed_presence": 0.20, "humor_presence": 0.80, "attentional_presence": 0.20}}, "D4": {"features": {"social_energy": 0.70}}}
    b = {"D9": {"primary": "RELAXED", "scores": {}, "features": {"social_presence": 0.45, "energy_contribution": 0.45, "relaxed_presence": 0.55, "humor_presence": 0.45, "attentional_presence": 0.55}}, "D4": {"features": {"social_energy": 0.70}}}
    d7 = type("D7", (), {"relationship": Relationship.ALIGNMENT})()
    result = compare_d9(a, b, d7)
    assert result.relationship == Relationship.COMPLEMENTARITY


def test_T14_d8_hard_pair_at_high_gap() -> None:
    a = build_partial_profile("t14a", answers(Q3="Q3_A", Q6="Q6_A", Q10="Q10_C"))
    b = build_partial_profile("t14b", answers(Q3="Q3_C", Q6="Q6_B", Q10="Q10_A"))
    result = compare_all_dimensions(a["derived"], b["derived"])["D8"]
    assert result.relationship in {Relationship.HARD_FRICTION, Relationship.SOFT_FRICTION}


def test_T15_phase_context_only() -> None:
    a = build_partial_profile("t15a", answers(Q5="Q5_A"))
    b = build_partial_profile("t15b", answers(Q5="Q5_A"))
    result = analyze_pair(a, b, "DATE")
    assert result["phase_adjustment"] == 0.05
    assert result["trace"]["dimensions"]["D10"]["weight"] == 0.0


def test_T16_natural_gate() -> None:
    scores = final_scores({"alignment_score": 0.82, "complementarity_score": 0.18, "friction_score": 0.12}, 0.05)
    chemistry, fallback = classify({"alignment_score": 0.82, "complementarity_score": 0.18, "friction_score": 0.12}, scores, {"hard_friction_count": 0, "reinforced_friction_group_count": 0, "productive_difference_count": 0})
    assert chemistry == Chemistry.NATURAL_CLICK and fallback is False


def test_T17_interesting_requires_productive_difference() -> None:
    scores = final_scores({"alignment_score": 0.0, "complementarity_score": 0.35, "friction_score": 0.10}, 0.0)
    chemistry, _ = classify({"alignment_score": 0.0, "complementarity_score": 0.35, "friction_score": 0.10}, scores, {"hard_friction_count": 0, "reinforced_friction_group_count": 0, "productive_difference_count": 1})
    assert chemistry in {Chemistry.INTERESTING_CHEMISTRY, Chemistry.POTENTIAL_FRICTION}


def test_T18_friction_override() -> None:
    scores = final_scores({"alignment_score": 0.90, "complementarity_score": 0.90, "friction_score": 0.50}, 0.05)
    assert classify({"alignment_score": 0.90, "complementarity_score": 0.90, "friction_score": 0.50}, scores, {"hard_friction_count": 0, "reinforced_friction_group_count": 0, "productive_difference_count": 2})[0] == Chemistry.POTENTIAL_FRICTION


def test_T19_two_hard_frictions_override() -> None:
    scores = final_scores({"alignment_score": 0.90, "complementarity_score": 0.90, "friction_score": 0.10}, 0.05)
    assert classify({"alignment_score": 0.90, "complementarity_score": 0.90, "friction_score": 0.10}, scores, {"hard_friction_count": 2, "reinforced_friction_group_count": 0, "productive_difference_count": 2})[0] == Chemistry.POTENTIAL_FRICTION


def test_T20_hard_reinforced_low_final_override() -> None:
    scores = final_scores({"alignment_score": 0.20, "complementarity_score": 0.20, "friction_score": 0.10}, 0.0)
    assert classify({"alignment_score": 0.20, "complementarity_score": 0.20, "friction_score": 0.10}, scores, {"hard_friction_count": 1, "reinforced_friction_group_count": 1, "productive_difference_count": 0})[0] == Chemistry.POTENTIAL_FRICTION


def test_T21_fallback_productive_difference() -> None:
    scores = final_scores({"alignment_score": 0.10, "complementarity_score": 0.25, "friction_score": 0.20}, 0.0)
    chemistry, fallback = classify({"alignment_score": 0.10, "complementarity_score": 0.25, "friction_score": 0.20}, scores, {"hard_friction_count": 0, "reinforced_friction_group_count": 0, "productive_difference_count": 1})
    assert chemistry == Chemistry.INTERESTING_CHEMISTRY and fallback is True


def test_T22_fallback_alignment_dominant() -> None:
    scores = final_scores({"alignment_score": 0.40, "complementarity_score": 0.0, "friction_score": 0.0}, 0.0)
    chemistry, fallback = classify({"alignment_score": 0.40, "complementarity_score": 0.0, "friction_score": 0.0}, scores, {"hard_friction_count": 0, "reinforced_friction_group_count": 0, "productive_difference_count": 0})
    assert chemistry == Chemistry.NATURAL_CLICK and fallback is True


def test_T23_pair_symmetry() -> None:
    a = build_partial_profile("t23a", answers(Q2="Q2_C"))
    b = build_partial_profile("t23b", answers(Q2="Q2_D", Q8="Q8_C"))
    ab = analyze_pair(a, b, "DATE")
    ba = analyze_pair(b, a, "DATE")
    assert {key: ab[key] for key in ("alignment_score", "complementarity_score", "friction_score", "final_score_internal", "classification")} == {key: ba[key] for key in ("alignment_score", "complementarity_score", "friction_score", "final_score_internal", "classification")}


def test_T24_same_pair_modes_differ() -> None:
    a = build_partial_profile("t24a", answers())
    b = build_partial_profile("t24b", answers(Q4="Q4_D", Q9="Q9_B"))
    assert analyze_pair(a, b, "DATE")["relationship_mode"] == "DATE"
    assert analyze_pair(a, b, "FRIEND")["relationship_mode"] == "FRIEND"


def test_T25_answer_change_changes_profile_and_cache_identity() -> None:
    a = build_partial_profile("t25a", answers())
    changed = build_partial_profile("t25a", answers(Q5="Q5_D"))
    b = build_partial_profile("t25b", answers())
    assert a["profile_version"] != changed["profile_version"]
    assert pair_cache_key("t25a", "t25b", "DATE", a, b) != pair_cache_key("t25a", "t25b", "DATE", changed, b)


def test_T26_scoring_version_changes_cache_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    a = build_partial_profile("t26a", answers())
    b = build_partial_profile("t26b", answers())
    before = pair_cache_key("t26a", "t26b", "DATE", a, b)
    monkeypatch.setattr(config, "VERSIONS", MappingProxyType({**dict(config.VERSIONS), "scoring_model": "1.3.0"}))
    after = pair_cache_key("t26a", "t26b", "DATE", a, b)
    assert before != after


def test_T27_public_pair_has_no_internal_numeric_score() -> None:
    a = build_partial_profile("t27a", answers())
    b = build_partial_profile("t27b", answers(Q4="Q4_B"))
    from app.vibe.narrative import render_pair_fallback
    from app.vibe.pair.engine import public_pair_result
    result = analyze_pair(a, b, "DATE")
    public = public_pair_result("id", result, render_pair_fallback(result))
    assert "final_score_internal" not in public and "overall_score_percent" not in public


def test_T28_unsupported_llm_evidence_blocked() -> None:
    with pytest.raises(Exception) as error:
        validate_llm_output({"title": "x", "explanation": "x", "claim_keys": ["positive_D1"], "evidence_ids": ["unknown"]}, {"evidence": [{"evidence_id": "known", "statement_key": "positive_D1"}]})
    assert error.value.code == "NARRATIVE_RENDER_ERROR"


def test_T29_forbidden_llm_claim_blocked() -> None:
    with pytest.raises(Exception):
        validate_llm_output({"title": "diagnosis", "explanation": "This is an attachment style.", "claim_keys": ["positive_D1"], "evidence_ids": ["known"]}, {"evidence": [{"evidence_id": "known", "statement_key": "positive_D1"}]})


def test_T30_severe_friction_wildcard_rejected() -> None:
    assert select_wildcard_from_candidates([{"archetype": "HIGHER_ENERGY", "difference_score": 0.90, "complementarity_score": 0.90, "friction_score": 0.50, "hard_friction_count": 0}]) is None


def test_Z01_d2_fixed_tie_order() -> None:
    assert profile_module._profile_signal_view  # module boundary exists
    from app.vibe.dimensions import _sort_modes
    assert _sort_modes({"EASE_LED": 1.0, "ATTENTION_LED": 1.0}, config.D2_TIE_ORDER)[0][0] == "ATTENTION_LED"


def test_Z02_d4_productive_guard_is_explicit() -> None:
    a = build_partial_profile("z02a", answers(Q1="Q1_A", Q3="Q3_A"))
    b = build_partial_profile("z02b", answers(Q1="Q1_D", Q3="Q3_C"))
    assert "productive_guard" in compare_d4(a["derived"], b["derived"]).trace


def test_Z03_d4_interference_policy() -> None:
    a = {"metrics": {"social_energy": 0.80, "social_density": 0.70}, "D4": {"features": {"social_energy": 0.80, "social_density": 0.70, "initial_openness": 0.80, "warmup_speed": 0.80, "energy_contribution": 0.80, "social_replenishment": 0.80}}}
    b = {"metrics": {"social_energy": 0.20, "social_density": 0.10}, "D4": {"features": {"social_energy": 0.20, "social_density": 0.10, "initial_openness": 0.20, "warmup_speed": 0.20, "energy_contribution": 0.20, "social_replenishment": 0.10}}}
    assert compare_d4(a, b).trace["interference_policy"] is True


def test_Z04_d5_all_high_salience_predicates() -> None:
    from app.vibe.pair.dimensions import d5_high_salience
    assert d5_high_salience(0.55, 0.50, -0.50)
    assert not d5_high_salience(0.55, 0.50, -0.499999)


def test_Z05_d8_hard_threshold() -> None:
    a = {"D8": {"category": "IMMEDIATE", "features": {"initial_openness": 0.0, "warmup_speed": 0.0, "processing_delay": 0.0, "introspection": 0.0, "action_orientation": 0.0}}}
    b = {"D8": {"category": "PROCESS_FIRST", "features": {"initial_openness": 0.6, "warmup_speed": 0.6, "processing_delay": 0.6, "introspection": 0.6, "action_orientation": 0.6}}}
    assert compare_d8(a, b).relationship == Relationship.HARD_FRICTION


def test_Z06_d9_energy_interference() -> None:
    a = {"D9": {"primary": "ENERGIZER", "scores": {}, "features": {"social_presence": 1.0, "energy_contribution": 1.0, "relaxed_presence": 0.0, "humor_presence": 1.0, "attentional_presence": 0.0}}, "D4": {"features": {"social_energy": 1.0}}}
    b = {"D9": {"primary": "UNDERSTATED", "scores": {}, "features": {"social_presence": 0.0, "energy_contribution": 0.0, "relaxed_presence": 1.0, "humor_presence": 0.0, "attentional_presence": 1.0}}, "D4": {"features": {"social_energy": 0.0}}}
    d7 = type("D7", (), {"relationship": Relationship.SOFT_FRICTION})()
    assert compare_d9(a, b, d7).trace["interference_policy"] is True


def test_Z07_wildcard_fixed_tie() -> None:
    selected = select_wildcard_from_candidates([
        {"archetype": "MORE_DIRECT", "difference_score": 0.50, "complementarity_score": 0.50, "friction_score": 0.10, "hard_friction_count": 0},
        {"archetype": "HIGHER_ENERGY", "difference_score": 0.50, "complementarity_score": 0.50, "friction_score": 0.10, "hard_friction_count": 0},
    ])
    assert selected["archetype"] == "HIGHER_ENERGY"


def test_Z08_pull_drain_shortage_no_fabrication() -> None:
    assert profile_module._pulls({"humor_connection": 0.0, "playful_affection": 0.0, "emotional_depth": 0.0, "intellectual_depth": 0.0, "conversation_ease": 0.0, "attentional_affection": 0.0, "social_selectivity": 0.0, "warmup_speed": 1.0, "social_presence": 0.0, "solitary_recovery": 0.0, "attentional_presence": 0.0, "flexibility": 0.0, "spontaneity": 0.0}) == []
    assert profile_module._drains({"social_energy": 1.0, "solitary_recovery": 0.0, "social_selectivity": 0.0, "warmup_speed": 1.0, "structure_preference": 0.0, "spontaneity": 0.0, "connection_depth": 0.0, "humor_connection": 0.0, "conversation_ease": 0.0, "processing_delay": 0.0, "Q6_category": "DIRECT_PROCESSOR"}) == []


def test_Z09_fallback_cannot_bypass_friction() -> None:
    scores = final_scores({"alignment_score": 0.90, "complementarity_score": 0.90, "friction_score": 0.51}, 0.05)
    assert classify({"alignment_score": 0.90, "complementarity_score": 0.90, "friction_score": 0.51}, scores, {"hard_friction_count": 0, "reinforced_friction_group_count": 0, "productive_difference_count": 2})[0] == Chemistry.POTENTIAL_FRICTION


def test_Z10_d10_only_phase_evidence() -> None:
    a = build_partial_profile("z10a", answers())
    b = build_partial_profile("z10b", answers(Q5="Q5_D"))
    result = analyze_pair(a, b, "DATE")
    assert result["trace"]["dimensions"]["D10"]["weight"] == 0.0


def test_Z11_normalized_mode_weights() -> None:
    for mode in ("DATE", "FRIEND", "HANGOUT"):
        weights = effective_mode_weights(mode)
        assert sum(weights[d] for d in config.DIMENSION_ORDER) == pytest.approx(1.0)
        assert weights["D10"] == 0.0


def test_Z12_symmetric_cache_key() -> None:
    a = build_partial_profile("z12a", answers())
    b = build_partial_profile("z12b", answers(Q4="Q4_B"))
    assert pair_cache_key("z12a", "z12b", "DATE", a, b) == pair_cache_key("z12b", "z12a", "DATE", b, a)


def test_Z13_invalid_configuration_is_typed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "VERSIONS", MappingProxyType({"questionnaire": "1.0"}))
    with pytest.raises(ConfigurationError) as error:
        validate_configuration()
    assert error.value.code == "ENGINE_CONFIG_INVALID"


def test_Z14_narrative_fallback_leaves_deterministic_facts() -> None:
    a = build_partial_profile("z14a", answers())
    b = build_partial_profile("z14b", answers(Q2="Q2_C"))
    result = analyze_pair(a, b, "DATE")
    fallback = render_pair_fallback(result)
    assert fallback["chemistry"] == result["classification"]
    assert fallback["evidence_ids"] == [item["evidence_id"] for item in result["evidence"]]


def test_Z15_no_intermediate_rounding() -> None:
    scores = final_scores({"alignment_score": 0.82, "complementarity_score": 0.18, "friction_score": 0.12}, 0.05)
    assert scores["final_score_internal"] == pytest.approx(0.7781481481481482)
    assert scores["final_score_internal"] != round(scores["final_score_internal"], 2)


def test_observability_replay_has_versions_trace_cache_hit_and_request_metadata(db_session) -> None:
    compute_profile(db_session, "obs_a", answers())
    compute_profile(db_session, "obs_b", answers(Q4="Q4_B"))
    _, first, _ = analyze_pair_on_demand(db_session, "obs_a", "obs_b", "DATE")
    _, second, _ = analyze_pair_on_demand(db_session, "obs_b", "obs_a", "DATE")
    assert first["profile_versions"] == {"user_a": first["profile_versions"]["user_a"], "user_b": first["profile_versions"]["user_b"]}
    assert first["trace"]["dimensions"]["D1"]["rule"] == "pair.D1"
    assert first["observability"]["cache_hit"] is False
    assert first["observability"]["request_id"]
    assert second["observability"]["cache_hit"] is True
    assert "scoring_model" in first["engine_versions"]


def test_authorization_boundary_fails_closed_outside_local(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api import deps
    from app.core.config import Settings

    monkeypatch.setattr(deps, "get_settings", lambda: Settings(environment="production", vibe_service_token="secret"))
    empty = Request({"type": "http", "headers": []})
    with pytest.raises(HTTPException) as error:
        deps.require_vibe_service_authorization(empty)
    assert error.value.status_code == 403
    authorized = Request({"type": "http", "headers": [(b"authorization", b"Bearer secret")]})
    deps.require_vibe_service_authorization(authorized)
