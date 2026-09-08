"""Component aggregation, final score, friction groups, and classification."""

from __future__ import annotations

from typing import Any

from app.vibe.config.v1_1_0 import (
    CHEMISTRY_THRESHOLDS,
    COMPLEMENTARITY_MULTIPLIERS,
    FRICTION_MULTIPLIERS,
    GLOBAL_COMPONENT_WEIGHTS,
    THRESHOLDS,
)
from app.vibe.contracts import Chemistry, DimensionResult, Relationship
from app.vibe.signals import clamp01

FRICTION_GROUPS = {
    "PLANNING": ("D6",),
    "EMOTIONAL": ("D5", "D2"),
    "SOCIAL_ENERGY": ("D4", "D7", "D9"),
    "CONVERSATION": ("D1", "D8"),
}


def component_scores(results: dict[str, DimensionResult], mode_weights: dict[str, float]) -> dict[str, float]:
    alignment_raw = sum(max(0.0, result.interaction_score) * mode_weights[dimension] for dimension, result in results.items() if dimension != "D10" and result.relationship == Relationship.ALIGNMENT)
    alignment_capacity = sum(mode_weights[dimension] for dimension, result in results.items() if dimension != "D10" and result.relationship == Relationship.ALIGNMENT)
    alignment = alignment_raw / alignment_capacity if alignment_capacity > 0 else 0.0

    complementarity_raw = sum(result.interaction_score * mode_weights[dimension] * COMPLEMENTARITY_MULTIPLIERS[dimension] for dimension, result in results.items() if dimension != "D10" and result.relationship == Relationship.COMPLEMENTARITY)
    complementarity_capacity = sum(mode_weights[dimension] * COMPLEMENTARITY_MULTIPLIERS[dimension] for dimension, result in results.items() if dimension != "D10" and result.relationship == Relationship.COMPLEMENTARITY)
    complementarity = complementarity_raw / complementarity_capacity if complementarity_capacity > 0 else 0.0

    friction_raw = sum(abs(result.interaction_score) * mode_weights[dimension] * FRICTION_MULTIPLIERS[dimension] for dimension, result in results.items() if dimension != "D10" and result.relationship in {Relationship.SOFT_FRICTION, Relationship.HARD_FRICTION})
    friction_capacity = sum(mode_weights[dimension] * FRICTION_MULTIPLIERS[dimension] for dimension, result in results.items() if dimension != "D10" and result.relationship in {Relationship.SOFT_FRICTION, Relationship.HARD_FRICTION})
    friction = friction_raw / friction_capacity if friction_capacity > 0 else 0.0
    return {"alignment_score": clamp01(alignment), "complementarity_score": clamp01(complementarity), "friction_score": clamp01(friction)}


def friction_counts(results: dict[str, DimensionResult]) -> dict[str, int]:
    hard_count = sum(1 for dimension, result in results.items() if dimension != "D10" and result.interaction_score <= THRESHOLDS["hard_friction"])
    reinforced = sum(1 for dimensions in FRICTION_GROUPS.values() if any(results[dimension].interaction_score <= THRESHOLDS["meaningful_friction"] for dimension in dimensions))
    productive = sum(1 for dimension, result in results.items() if dimension != "D10" and result.relationship == Relationship.COMPLEMENTARITY and result.difference_score >= 0.30 and result.interaction_score >= THRESHOLDS["complementarity"] and result.interaction_score < THRESHOLDS["alignment"] and hard_count == 0)
    return {"hard_friction_count": hard_count, "reinforced_friction_group_count": reinforced, "productive_difference_count": productive}


def final_scores(components: dict[str, float], phase_adjustment: float) -> dict[str, float]:
    raw_final = components["alignment_score"] * GLOBAL_COMPONENT_WEIGHTS["alignment"] + components["complementarity_score"] * GLOBAL_COMPONENT_WEIGHTS["complementarity"] - components["friction_score"] * GLOBAL_COMPONENT_WEIGHTS["friction"]
    normalized_final = (raw_final + 0.60) / 1.35
    pre_phase = clamp01(normalized_final)
    final = clamp01(pre_phase + phase_adjustment)
    return {"raw_final": raw_final, "normalized_final": normalized_final, "final_score_pre_phase": pre_phase, "final_score_internal": final}


def classify(components: dict[str, float], scores: dict[str, float], counts: dict[str, int]) -> tuple[Chemistry, bool]:
    friction = components["friction_score"]
    alignment = components["alignment_score"]
    complementarity = components["complementarity_score"]
    final = scores["final_score_internal"]
    hard_count = counts["hard_friction_count"]
    reinforced = counts["reinforced_friction_group_count"]
    productive = counts["productive_difference_count"]

    potential_override = friction >= CHEMISTRY_THRESHOLDS["interesting_friction_max_exclusive"] or hard_count >= 2 or (hard_count >= 1 and reinforced >= 1 and final < CHEMISTRY_THRESHOLDS["natural_alignment"])
    if potential_override:
        return Chemistry.POTENTIAL_FRICTION, False
    natural = final >= CHEMISTRY_THRESHOLDS["natural_final"] and alignment >= CHEMISTRY_THRESHOLDS["natural_alignment"] and friction < CHEMISTRY_THRESHOLDS["natural_friction_max_exclusive"] and hard_count == 0
    if natural:
        return Chemistry.NATURAL_CLICK, False
    interesting = final >= CHEMISTRY_THRESHOLDS["interesting_final"] and complementarity >= CHEMISTRY_THRESHOLDS["interesting_complementarity"] and friction < CHEMISTRY_THRESHOLDS["interesting_friction_max_exclusive"] and productive >= 1 and hard_count == 0
    if interesting:
        return Chemistry.INTERESTING_CHEMISTRY, False
    if friction >= CHEMISTRY_THRESHOLDS["interesting_friction_max_exclusive"] or hard_count > 0:
        return Chemistry.POTENTIAL_FRICTION, True
    if productive >= 1 and complementarity >= THRESHOLDS["complementarity"]:
        return Chemistry.INTERESTING_CHEMISTRY, True
    return Chemistry.NATURAL_CLICK, True
