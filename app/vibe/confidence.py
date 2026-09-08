"""Canonical deterministic confidence calculations for individual profiles."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from app.vibe.config.v1_1_0 import PROFILE_WEIGHTS
from app.vibe.contracts import ConfigurationError, ConfidenceLabel, SpecificationGap


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def continuous_strength(value: float) -> float:
    return clamp01(abs((2.0 * float(value)) - 1.0))


def _validate_unit(unit: Mapping[str, Any], index: int) -> None:
    if unit.get("polarity") not in {"SUPPORT", "CONTRADICT"}:
        raise SpecificationGap(f"profile.confidence.evidence[{index}].polarity", "Every confidence evidence unit requires SUPPORT or CONTRADICT polarity.")
    if "strength_value" not in unit:
        raise SpecificationGap(f"profile.confidence.evidence[{index}].strength_value", "Every confidence evidence unit requires strength_value.")
    try:
        strength = float(unit["strength_value"])
    except (TypeError, ValueError) as exc:
        raise SpecificationGap(f"profile.confidence.evidence[{index}].strength_value", "Evidence strength_value must be numeric.") from exc
    if not 0.0 <= strength <= 1.0:
        raise SpecificationGap(f"profile.confidence.evidence[{index}].strength_value", "Evidence strength_value must be in [0,1].")


def unique_evidence_units(units: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, unit in enumerate(units):
        _validate_unit(unit, index)
        source = unit.get("source")
        if not isinstance(source, str) or not source:
            raise SpecificationGap(f"profile.confidence.evidence[{index}].source", "Every confidence evidence unit requires a canonical source.")
        if source in seen:
            continue
        seen.add(source)
        result.append(dict(unit))
    return result


def _count_factor(count: int) -> float:
    return 0.0 if count == 0 else 0.50 if count == 1 else 0.75 if count == 2 else 1.00


def _strength_factor(mean_strength: float) -> float:
    if mean_strength < 0.40:
        return 0.25
    if mean_strength < 0.60:
        return 0.50
    if mean_strength < 0.80:
        return 0.75
    return 1.00


def _consistency_factor(units: Sequence[Mapping[str, Any]]) -> float:
    total = len(units)
    if total == 0:
        return 0.0
    if total == 1:
        return 0.75
    support = sum(1 for unit in units if unit["polarity"] == "SUPPORT")
    ratio = support / total
    if ratio < 0.60:
        return 0.25
    if ratio < 0.75:
        return 0.50
    if ratio < 0.90:
        return 0.75
    return 1.00


def section_confidence(units: Sequence[Mapping[str, Any]]) -> float:
    unique = unique_evidence_units(units)
    count = len(unique)
    mean_strength = sum(float(unit["strength_value"]) for unit in unique) / count if count else 0.0
    value = (_count_factor(count) + _strength_factor(mean_strength) + _consistency_factor(unique)) / 3.0
    return clamp01(value)


def confidence_label(value: float) -> ConfidenceLabel:
    value = clamp01(value)
    if value < 0.50:
        return ConfidenceLabel.WEAK
    if value < 0.70:
        return ConfidenceLabel.MODERATE
    if value < 0.85:
        return ConfidenceLabel.STRONG
    return ConfidenceLabel.VERY_STRONG


def profile_confidence(section_values: Mapping[str, float]) -> tuple[float, ConfidenceLabel]:
    if set(section_values) != set(PROFILE_WEIGHTS):
        raise ConfigurationError("profile.confidence.sections", "Profile confidence requires exactly D1-D10 section confidence values.")
    denominator = sum(PROFILE_WEIGHTS.values())
    value = sum(float(section_values[dimension]) * PROFILE_WEIGHTS[dimension] for dimension in PROFILE_WEIGHTS) / denominator
    value = clamp01(value)
    return value, confidence_label(value)


def strong_profile_claim_allowed(section_value: float, units: Sequence[Mapping[str, Any]], prohibited: bool = False) -> bool:
    if prohibited or section_value < 0.70:
        return False
    unique = unique_evidence_units(units)
    direct = any(str(unit.get("source", "")).startswith("Q") for unit in unique)
    derived_count = sum(1 for unit in unique if str(unit.get("source", "")).startswith("signal:"))
    return direct or derived_count >= 2

