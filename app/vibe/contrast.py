"""Bounded deterministic comparison against the four canonical prototypes."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.vibe.config.v1_1_0 import CONTRAST_NORMALIZED_WEIGHTS, CONTRAST_PROTOTYPES, CONTRAST_TIE_ORDER, CONTRAST_WEIGHTS, DIMENSION_ORDER
from app.vibe.contracts import ConfigurationError
from app.vibe.dimensions import derive_dimensions
from app.vibe.pair.dimensions import compare_all_dimensions
from app.vibe.signal_map import map_answers_to_signals


def _prototype_profile(answer_ids: tuple[str, ...]) -> dict[str, Any]:
    answers = {f"Q{i}": answer_ids[i - 1] for i in range(1, 11)}
    raw = map_answers_to_signals(answers)
    return {"answers": answers, "signals": raw, "derived": derive_dimensions(raw)}


def contrast_prototype(prototype_id: str) -> dict[str, Any]:
    answer_ids = CONTRAST_PROTOTYPES.get(prototype_id)
    if answer_ids is None:
        raise ConfigurationError(f"contrast.prototypes.{prototype_id}", "Unknown contrast prototype.")
    if not isinstance(answer_ids, tuple) or len(answer_ids) != 10:
        raise ConfigurationError(f"contrast.prototypes.{prototype_id}", "Contrast prototype must contain exactly ten canonical answers.")
    return _prototype_profile(answer_ids)


def contrast_score(relevance: float, support: float) -> float:
    return 0.70 * float(relevance) + 0.30 * float(support)


def contrast_is_bounded(score: float) -> bool:
    """Return whether a contrast is below the canonical specific-claim threshold."""
    return float(score) < 0.30


def contrast_dimension_values(user: Mapping[str, Any], prototype: Mapping[str, Any]) -> dict[str, dict[str, float]]:
    results = compare_all_dimensions(user["derived"], prototype["derived"])
    values: dict[str, dict[str, float]] = {}
    for dimension in DIMENSION_ORDER:
        difference = max(0.0, min(1.0, float(results[dimension].difference_score)))
        confidence = max(0.0, min(1.0, float(results[dimension].confidence)))
        weight = CONTRAST_WEIGHTS.get(dimension)
        if weight is None:
            raise ConfigurationError(f"contrast.weights.{dimension}", "Missing contrast dimension weight.")
        values[dimension] = {
            "difference": difference,
            "confidence": confidence,
            "weight": float(weight),
            "normalized_weight": float(CONTRAST_NORMALIZED_WEIGHTS[dimension]),
            "relevance_contribution": difference * float(CONTRAST_NORMALIZED_WEIGHTS[dimension]),
            "support_contribution": difference * confidence * float(CONTRAST_NORMALIZED_WEIGHTS[dimension]),
            "evidence_priority": difference * confidence * float(CONTRAST_NORMALIZED_WEIGHTS[dimension]),
            "interaction_score": float(results[dimension].interaction_score),
        }
    return values


def contrast_dimension_difference(user: Mapping[str, Any], prototype: Mapping[str, Any], dimension: str) -> float:
    if dimension not in DIMENSION_ORDER:
        raise ConfigurationError(f"contrast.dimension.{dimension}", "Unknown contrast dimension.")
    return contrast_dimension_values(user, prototype)[dimension]["difference"]


def contrast_dimension_confidence(user: Mapping[str, Any], prototype: Mapping[str, Any], dimension: str) -> float:
    if dimension not in DIMENSION_ORDER:
        raise ConfigurationError(f"contrast.dimension.{dimension}", "Unknown contrast dimension.")
    return contrast_dimension_values(user, prototype)[dimension]["confidence"]


def _rank_dimensions(values: Mapping[str, Mapping[str, float]]) -> list[str]:
    order = {dimension: index for index, dimension in enumerate(CONTRAST_TIE_ORDER)}
    return sorted(values, key=lambda dimension: (-float(values[dimension]["evidence_priority"]), -float(values[dimension]["confidence"]), -float(values[dimension]["difference"]), order[dimension]))


def build_contrast_analysis(profile: Mapping[str, Any]) -> list[dict[str, Any]]:
    user_derived = profile.get("derived")
    if not isinstance(user_derived, Mapping):
        raise ConfigurationError("profile.contrast.user", "Contrast analysis requires the stored individual dimensions.")
    analyses: list[dict[str, Any]] = []
    for prototype_id, answer_ids in CONTRAST_PROTOTYPES.items():
        prototype = contrast_prototype(prototype_id)
        values = contrast_dimension_values({"derived": user_derived}, prototype)
        relevance = sum(values[d]["relevance_contribution"] for d in DIMENSION_ORDER)
        support = sum(values[d]["support_contribution"] for d in DIMENSION_ORDER)
        score = contrast_score(relevance, support)
        ranking = _rank_dimensions(values)
        analyses.append(
            {
                "prototype": prototype_id,
                "answers": list(answer_ids),
                "contrast_relevance": relevance,
                "contrast_support": support,
                "contrast_score": score,
                "omission_threshold": contrast_is_bounded(score),
                "primary_dimension": ranking[0] if ranking else None,
                "evidence": [{"dimension": d, **values[d]} for d in ranking[:4]],
                "dimension_values": values,
                "chemistry": None,
            }
        )
    return analyses


__all__ = ["CONTRAST_PROTOTYPES", "build_contrast_analysis", "contrast_dimension_confidence", "contrast_dimension_difference", "contrast_dimension_values", "contrast_is_bounded", "contrast_prototype", "contrast_score"]
