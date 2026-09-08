"""Categorical pair matrices."""

from __future__ import annotations

from typing import Mapping

from app.vibe.config.v1_1_0 import D1_MATRIX, D3_MATRIX, D6_MATRIX, D7_MATRIX
from app.vibe.contracts import ConfigurationError, DimensionResult, Relationship
from app.vibe.pair.continuous import relationship_from_interaction


def _matrix_result(dimension: str, matrix: Mapping[str, Mapping[str, float]], category_a: str, category_b: str) -> DimensionResult:
    try:
        interaction = float(matrix[category_a][category_b])
    except KeyError as exc:
        raise ConfigurationError(f"{dimension}.matrix.{category_a}.{category_b}", "Missing categorical matrix entry.") from exc
    relationship = relationship_from_interaction(interaction)
    difference = {
        Relationship.ALIGNMENT: 0.00,
        Relationship.COMPLEMENTARITY: 0.40,
        Relationship.NEUTRAL: 0.20,
        Relationship.SOFT_FRICTION: 0.55,
        Relationship.HARD_FRICTION: 0.80,
    }[relationship]
    return DimensionResult(
        dimension=dimension,
        relationship=relationship,
        interaction_score=interaction,
        difference_score=difference,
        confidence=1.0,
        trace={"category_a": category_a, "category_b": category_b, "matrix": dimension},
    )


def compare_d1(a: dict, b: dict) -> DimensionResult:
    return _matrix_result("D1", D1_MATRIX, a["D1"]["category"], b["D1"]["category"])


def compare_d3(a: dict, b: dict) -> DimensionResult:
    return _matrix_result("D3", D3_MATRIX, a["D3"]["category"], b["D3"]["category"])


def compare_d6(a: dict, b: dict) -> DimensionResult:
    return _matrix_result("D6", D6_MATRIX, a["D6"]["planning_style"], b["D6"]["planning_style"])


def compare_d7(a: dict, b: dict) -> DimensionResult:
    return _matrix_result("D7", D7_MATRIX, a["D7"]["category"], b["D7"]["category"])


def compare_d10(a: dict, b: dict) -> DimensionResult:
    category_a = a["D10"]["category"]
    category_b = b["D10"]["category"]
    try:
        adjustment = float(__import__("app.vibe.config.v1_1_0", fromlist=["D10_MATRIX"]).D10_MATRIX[category_a][category_b])
    except KeyError as exc:
        raise ConfigurationError(f"D10.matrix.{category_a}.{category_b}", "Missing phase matrix entry.") from exc
    difference = 0.00 if category_a == category_b else 0.25 if adjustment == 0.025 else 0.75 if adjustment == -0.025 else 0.50
    return DimensionResult(
        dimension="D10",
        relationship=Relationship.NEUTRAL,
        interaction_score=adjustment,
        difference_score=difference,
        confidence=1.0,
        trace={"category_a": category_a, "category_b": category_b, "phase_adjustment": adjustment},
    )

