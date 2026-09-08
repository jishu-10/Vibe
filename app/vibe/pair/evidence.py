"""Deterministic pair evidence selection and confidence."""

from __future__ import annotations

from typing import Any

from app.vibe.config.v1_1_0 import DIMENSION_ORDER, NARRATIVE_LIMITS, PAIR_POLICY_THRESHOLDS, THRESHOLDS
from app.vibe.contracts import ConfidenceLabel, DimensionResult, EvidenceItem, Relationship


def _signal_strength_factor(strength: float) -> float:
    return 0.25 if strength < 0.40 else 0.50 if strength < 0.60 else 0.75 if strength < 0.80 else 1.00


def confidence_label(value: float) -> ConfidenceLabel:
    if value < 0.50:
        return ConfidenceLabel.WEAK
    if value < 0.70:
        return ConfidenceLabel.MODERATE
    if value < 0.85:
        return ConfidenceLabel.STRONG
    return ConfidenceLabel.VERY_STRONG


def _dimension_confidence(result: DimensionResult) -> float:
    evidence_count_factor = 0.50
    signal_strength_factor = _signal_strength_factor(abs(result.interaction_score))
    consistency_factor = {Relationship.ALIGNMENT: 1.00, Relationship.COMPLEMENTARITY: 0.75, Relationship.NEUTRAL: 0.50, Relationship.SOFT_FRICTION: 0.50, Relationship.HARD_FRICTION: 0.25}[result.relationship]
    return (evidence_count_factor + signal_strength_factor + consistency_factor) / 3.0


def select_evidence(results: dict[str, DimensionResult], mode_weights: dict[str, float], derived_a: dict[str, Any], derived_b: dict[str, Any]) -> tuple[list[EvidenceItem], float]:
    max_weight = max(mode_weights[d] for d in DIMENSION_ORDER)
    candidates: list[EvidenceItem] = []
    for dimension in DIMENSION_ORDER:
        result = results[dimension]
        confidence = _dimension_confidence(result)
        mode_relevance = mode_weights[dimension] / max_weight
        effective_dimension_weight = mode_weights[dimension] * (1.0 + 0.10 * mode_relevance)
        priority = effective_dimension_weight * abs(result.interaction_score) * confidence * mode_relevance
        if result.interaction_score >= THRESHOLDS["high_conf_alignment"]:
            kind = "positive"
        elif result.interaction_score >= THRESHOLDS["complementarity"] and result.difference_score >= PAIR_POLICY_THRESHOLDS["d2_productive_gap"] and result.relationship == Relationship.COMPLEMENTARITY:
            kind = "complementary"
        elif result.interaction_score <= -0.35:
            kind = "friction"
        else:
            continue
        paths_a = tuple(derived_a[dimension].get("answer_paths", ()))
        paths_b = tuple(derived_b[dimension].get("answer_paths", ()))
        signal_paths_a = tuple(sorted(set(derived_a[dimension].get("features", {})) | set(derived_a[dimension].get("scores", {}))))
        signal_paths_b = tuple(sorted(set(derived_b[dimension].get("features", {})) | set(derived_b[dimension].get("scores", {}))))
        candidates.append(EvidenceItem(f"{dimension}:{kind}", dimension, kind, result.interaction_score, result.difference_score, confidence, priority, paths_a + paths_b, f"{kind}_{dimension}", signal_paths_a, signal_paths_b, f"pair.{dimension}"))

    order = {dimension: index for index, dimension in enumerate(DIMENSION_ORDER)}
    ranked = sorted(candidates, key=lambda item: (-item.insight_priority, -item.confidence, -abs(item.interaction_score), order[item.dimension]))
    positive = [item for item in ranked if item.kind in {"positive", "complementary"}][:NARRATIVE_LIMITS["positive_findings"]]
    friction = [item for item in ranked if item.kind == "friction"][:NARRATIVE_LIMITS["friction_findings"]]
    selected = sorted(positive + friction, key=lambda item: (-item.insight_priority, -item.confidence, -abs(item.interaction_score), order[item.dimension]))[:NARRATIVE_LIMITS["max_evidence"]]
    if not selected:
        return [], 0.0
    weighted_confidence = sum(item.confidence * item.insight_priority for item in selected)
    total_weight = sum(item.insight_priority for item in selected)
    return selected, weighted_confidence / total_weight if total_weight > 0 else 0.0
