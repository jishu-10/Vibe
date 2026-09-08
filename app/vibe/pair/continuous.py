"""Canonical continuous dimension evaluator."""

from __future__ import annotations

from app.vibe.config.v1_1_0 import PAIR_POLICY_THRESHOLDS
from app.vibe.contracts import Relationship
from app.vibe.signals import assert_interaction, clamp01, weighted_signal_average


def weighted_gap(features_a: dict[str, float], features_b: dict[str, float], weights: dict[str, float]) -> float:
    names = tuple(weights)
    return weighted_signal_average(
        [abs(features_a[name] - features_b[name]) for name in names],
        [weights[name] for name in names],
    )


def generic_continuous_evaluator(
    gap: float,
    *,
    productive_difference_policy: bool,
    productive_guard: bool,
    interference_policy: bool,
) -> tuple[Relationship, float]:
    if gap <= PAIR_POLICY_THRESHOLDS["generic_gap_1"]:
        relationship = Relationship.ALIGNMENT
        interaction = 0.75 + 0.25 * (1.0 - gap / PAIR_POLICY_THRESHOLDS["generic_gap_1"])
    elif gap <= PAIR_POLICY_THRESHOLDS["generic_gap_2"]:
        relationship = Relationship.ALIGNMENT
        interaction = 0.50 + 0.25 * (1.0 - (gap - PAIR_POLICY_THRESHOLDS["generic_gap_1"]) / PAIR_POLICY_THRESHOLDS["generic_gap_1"])
    elif gap <= PAIR_POLICY_THRESHOLDS["generic_gap_3"] and productive_difference_policy and productive_guard:
        relationship = Relationship.COMPLEMENTARITY
        interaction = 0.25 + 0.24 * (1.0 - (gap - PAIR_POLICY_THRESHOLDS["generic_gap_2"]) / 0.40)
    elif interference_policy:
        if gap <= 0.50:
            relationship = Relationship.SOFT_FRICTION
            interaction = -0.01 - 0.34 * ((gap - 0.30) / 0.20)
        elif gap <= 0.70:
            interaction = -0.35 - 0.30 * ((gap - 0.50) / 0.20)
            relationship = Relationship.HARD_FRICTION if interaction <= -0.50 else Relationship.SOFT_FRICTION
        else:
            relationship = Relationship.HARD_FRICTION
            interaction = -0.65 - 0.35 * min(1.0, (gap - 0.70) / 0.30)
    else:
        relationship = Relationship.NEUTRAL
        interaction = 0.00
    return relationship, assert_interaction(clamp01(interaction) if interaction >= 0 else max(-1.0, min(1.0, interaction)), "pair.generic.interaction")


def relationship_from_interaction(interaction: float) -> Relationship:
    score = assert_interaction(interaction, "pair.relationship.interaction")
    if score >= 0.50:
        return Relationship.ALIGNMENT
    if score >= 0.25:
        return Relationship.COMPLEMENTARITY
    if score >= 0.00:
        return Relationship.NEUTRAL
    if score > -0.50:
        return Relationship.SOFT_FRICTION
    return Relationship.HARD_FRICTION
