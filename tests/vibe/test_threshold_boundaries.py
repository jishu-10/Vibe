from __future__ import annotations

import pytest

from app.vibe.config.v1_1_0 import CHEMISTRY_THRESHOLDS, D10_MATRIX, INDIVIDUAL_THRESHOLDS
from app.vibe.contracts import Chemistry, Relationship
from app.vibe.dimensions import _band
from app.vibe.pair.aggregate import classify, final_scores
from app.vibe.pair.continuous import generic_continuous_evaluator, relationship_from_interaction


@pytest.mark.parametrize(
    ("thresholds", "labels"),
    [
        (INDIVIDUAL_THRESHOLDS["social_energy"], ("LOW", "LOW_MODERATE", "MODERATE", "HIGH", "VERY_HIGH")),
        (INDIVIDUAL_THRESHOLDS["social_density"], ("LOW", "MODERATE", "HIGH")),
        (INDIVIDUAL_THRESHOLDS["social_selectivity"], ("OPEN", "MODERATE", "SELECTIVE")),
        (INDIVIDUAL_THRESHOLDS["humor_connection"], ("LOW", "MODERATE", "HIGH", "VERY_HIGH")),
        (INDIVIDUAL_THRESHOLDS["introspection"], ("ACTION_ORIENTED", "MODERATE", "HIGHLY_INTERNAL")),
    ],
)
def test_profile_label_thresholds_are_inclusive(thresholds: tuple[float, ...], labels: tuple[str, ...]) -> None:
    epsilon = 1e-6
    for index, threshold in enumerate(thresholds):
        previous = labels[index]
        current = labels[index + 1]
        assert _band(threshold - epsilon, thresholds, labels) == previous
        assert _band(threshold, thresholds, labels) == current
        assert _band(threshold + epsilon, thresholds, labels) == current


@pytest.mark.parametrize("threshold", (0.15, 0.30, 0.70))
def test_generic_gap_boundaries_have_x_minus_x_x_plus_cases(threshold: float) -> None:
    epsilon = 1e-6
    for gap in (threshold - epsilon, threshold, threshold + epsilon):
        relationship, score = generic_continuous_evaluator(gap, productive_difference_policy=True, productive_guard=True, interference_policy=False)
        assert relationship in {Relationship.ALIGNMENT, Relationship.COMPLEMENTARITY, Relationship.NEUTRAL}
        assert -1.0 <= score <= 1.0


@pytest.mark.parametrize(
    ("value", "expected"),
    [(0.50, Relationship.ALIGNMENT), (0.25, Relationship.COMPLEMENTARITY), (0.0, Relationship.NEUTRAL), (-0.01, Relationship.SOFT_FRICTION), (-0.35, Relationship.SOFT_FRICTION), (-0.50, Relationship.HARD_FRICTION)],
)
def test_interaction_thresholds_are_exact(value: float, expected: Relationship) -> None:
    assert relationship_from_interaction(value) == expected
    epsilon = 1e-6
    if value > -0.5:
        assert relationship_from_interaction(value - epsilon) in {Relationship.SOFT_FRICTION, Relationship.NEUTRAL, Relationship.COMPLEMENTARITY}
        assert relationship_from_interaction(value + epsilon) in {Relationship.ALIGNMENT, Relationship.COMPLEMENTARITY, Relationship.NEUTRAL, Relationship.SOFT_FRICTION}


def test_chemistry_thresholds_have_exact_boundaries() -> None:
    def evaluate(final: float, alignment: float, complementarity: float, friction: float, productive: int = 1, hard: int = 0):
        scores = {"final_score_internal": final}
        return classify({"alignment_score": alignment, "complementarity_score": complementarity, "friction_score": friction}, scores, {"hard_friction_count": hard, "reinforced_friction_group_count": 0, "productive_difference_count": productive})[0]

    assert evaluate(CHEMISTRY_THRESHOLDS["natural_final"] - 1e-6, 0.55, 0.0, 0.0, productive=0) == Chemistry.NATURAL_CLICK
    assert evaluate(CHEMISTRY_THRESHOLDS["natural_final"], 0.55, 0.0, 0.0, productive=0) == Chemistry.NATURAL_CLICK
    assert evaluate(CHEMISTRY_THRESHOLDS["interesting_final"] - 1e-6, 0.0, 0.35, 0.0) == Chemistry.INTERESTING_CHEMISTRY
    assert evaluate(CHEMISTRY_THRESHOLDS["interesting_final"], 0.0, 0.35, 0.0) == Chemistry.INTERESTING_CHEMISTRY
    assert evaluate(0.65, 0.55, 0.0, CHEMISTRY_THRESHOLDS["natural_friction_max_exclusive"] - 1e-6, productive=0) == Chemistry.NATURAL_CLICK
    assert evaluate(0.65, 0.55, 0.0, CHEMISTRY_THRESHOLDS["natural_friction_max_exclusive"], productive=0) == Chemistry.NATURAL_CLICK


def test_phase_matrix_values_are_unrounded_and_bounded() -> None:
    values = {value for row in D10_MATRIX.values() for value in row.values()}
    assert values == {-0.025, 0.0, 0.025, 0.05}
    assert max(abs(value) for value in values) == 0.05
