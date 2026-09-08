from __future__ import annotations

import pytest

from app.vibe.contracts import Chemistry, DimensionResult, Relationship, VibeError
from app.vibe.narrative import validate_llm_output
from app.vibe.pair.aggregate import classify, final_scores
from app.vibe.pair.engine import analyze_pair
from app.vibe.pair.evidence import confidence_label
from app.vibe.profile import build_partial_profile


def _classify(final: float, alignment: float, complementarity: float, friction: float, productive: int = 1, hard: int = 0):
    scores = {"final_score_internal": final}
    return classify({"alignment_score": alignment, "complementarity_score": complementarity, "friction_score": friction}, scores, {"hard_friction_count": hard, "reinforced_friction_group_count": 0, "productive_difference_count": productive})


@pytest.mark.parametrize(
    ("value", "expected"),
    [(0.499999, "WEAK"), (0.50, "MODERATE"), (0.699999, "MODERATE"), (0.70, "STRONG"), (0.849999, "STRONG"), (0.85, "VERY_STRONG")],
)
def test_confidence_threshold_boundaries(value: float, expected: str) -> None:
    assert confidence_label(value).value == expected


def test_classification_threshold_boundaries() -> None:
    assert _classify(0.65, 0.55, 0.0, 0.349999, productive=0)[0] == Chemistry.NATURAL_CLICK
    assert _classify(0.65, 0.55, 0.0, 0.35, productive=0)[0] == Chemistry.NATURAL_CLICK
    assert _classify(0.45, 0.0, 0.35, 0.49, productive=1)[0] == Chemistry.INTERESTING_CHEMISTRY
    assert _classify(0.45, 0.0, 0.35, 0.50, productive=1)[0] == Chemistry.POTENTIAL_FRICTION


def test_llm_cannot_change_facts_or_cite_unknown_evidence() -> None:
    pair = {
        "classification": Chemistry.NATURAL_CLICK.value,
        "evidence": [{"evidence_id": "D1:positive", "statement_key": "positive_D1", "kind": "positive"}],
    }
    good = validate_llm_output({"title": "Grounded", "explanation": "The evidence supports this.", "claim_keys": ["positive_D1"], "evidence_ids": ["D1:positive"]}, pair)
    assert good["evidence_ids"] == ["D1:positive"]
    with pytest.raises(VibeError) as unsupported:
        validate_llm_output({"title": "Unsupported", "explanation": "The evidence supports this.", "claim_keys": ["positive_D1"], "evidence_ids": ["not-real"]}, pair)
    assert unsupported.value.code == "NARRATIVE_RENDER_ERROR"
    with pytest.raises(VibeError):
        validate_llm_output({"title": "Diagnosis", "explanation": "This is an attachment style.", "claim_keys": ["positive_D1"], "evidence_ids": ["D1:positive"]}, pair)
    with pytest.raises(VibeError):
        validate_llm_output({"title": "Certain", "explanation": "This will definitely work.", "claim_keys": ["positive_D1"], "evidence_ids": ["D1:positive"]}, {**pair, "confidence": {"label": "MODERATE"}})


def test_amended_d5_guard_and_salience_path_is_executable() -> None:
    base = {f"Q{i}": f"Q{i}_A" for i in range(1, 11)}
    a = build_partial_profile("a", base)
    b = build_partial_profile("b", {**base, "Q2": "Q2_B", "Q6": "Q6_B"})
    result = analyze_pair(a, b, "DATE")
    d5 = result["dimension_results"]["D5"]
    assert d5["computed_negative_score"] == max(0.0, -d5["interaction_score"])
    assert d5["friction_score"] == d5["computed_negative_score"]
