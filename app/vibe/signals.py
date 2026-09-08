"""Raw-signal normalization and invariants."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import isfinite
from typing import Any

from app.vibe.contracts import ConfigurationError


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def weighted_signal_average(values: Sequence[float], weights: Sequence[float]) -> float:
    if len(values) != len(weights) or not values or sum(weights) <= 0:
        raise ConfigurationError("signals.weighted_signal_average", "Values and positive weights must have equal non-zero length.")
    return sum(value * weight for value, weight in zip(values, weights, strict=True)) / sum(weights)


def assert_continuous_signal(value: Any, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)):
        raise ConfigurationError(path, "Continuous raw signal must be a finite number.")
    numeric = float(value)
    if not 0.0 <= numeric <= 1.0:
        raise ConfigurationError(path, "Continuous raw signal must be within [0,1].")
    return numeric


def assert_interaction(value: float, path: str) -> float:
    if not -1.0 <= value <= 1.0:
        raise ConfigurationError(path, "Interaction score must be within [-1,1].")
    return value


def validate_raw_signal_representation(raw: Mapping[str, Any]) -> None:
    signals = raw.get("signals")
    if not isinstance(signals, Mapping):
        raise ConfigurationError("signals", "Raw representation must contain a signals object.")
    for name, value in signals.items():
        if isinstance(value, (int, float)):
            assert_continuous_signal(value, f"signals.{name}")
        elif not isinstance(value, str):
            raise ConfigurationError(f"signals.{name}", "Categorical signal must be a string enum.")


def merge_signal_values(answer_mappings: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    signals: dict[str, Any] = {}
    for question_id in sorted(answer_mappings):
        for name, value in answer_mappings[question_id].items():
            if name in signals:
                raise ConfigurationError(f"signal_map.{question_id}.{name}", "Duplicate raw signal assignment is undefined.")
            signals[name] = value
    return signals

