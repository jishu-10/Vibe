"""Deterministic Wildcard candidate construction, comparison, and selection."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from app.vibe.config import v1_1_0 as config
from app.vibe.contracts import ConfigurationError, SpecificationGap
from app.vibe.dimensions import derive_dimensions
from app.vibe.pair.aggregate import component_scores, friction_counts
from app.vibe.pair.dimensions import compare_all_dimensions
from app.vibe.pair.modes import validate_wildcard_configuration, wildcard_effective_weights
from app.vibe.signals import clamp01


def _validate_deltas() -> None:
    validate_wildcard_configuration()


def perturb_signals(profile: Mapping[str, Any], archetype: str) -> dict[str, float]:
    _validate_deltas()
    if archetype not in config.WILDCARD_DELTAS:
        raise ConfigurationError(f"wildcard.archetype.{archetype}", "Unknown wildcard archetype.")
    signal_object = profile.get("signals")
    if not isinstance(signal_object, Mapping):
        raise SpecificationGap("wildcard.candidate_generation.signal_object", "Wildcard construction requires the stored deterministic signal object.")
    base = signal_object.get("signals")
    if not isinstance(base, Mapping):
        raise SpecificationGap("wildcard.candidate_generation.signal_object.signals", "Wildcard construction requires the stored deterministic continuous signal representation.")
    required = set(config.WILDCARD_DELTAS[archetype])
    missing = sorted(required.difference(base))
    if missing:
        raise SpecificationGap(
            f"wildcard.candidate_generation.required_signal.{missing[0]}",
            "Wildcard construction requires every canonical continuous signal.",
        )
    base_values: dict[str, float] = {}
    for signal, value in base.items():
        if signal not in config.CONTINUOUS_SIGNAL_NAMES:
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError) as exc:
            raise SpecificationGap(
                f"wildcard.candidate_generation.required_signal.{signal}",
                "Wildcard source signal must be numeric.",
            ) from exc
        if not 0.0 <= numeric <= 1.0:
            raise SpecificationGap(
                f"wildcard.candidate_generation.required_signal.{signal}",
                "Wildcard source signal must be in [0,1].",
            )
        base_values[signal] = numeric
    for signal in required:
        if signal not in base_values:
            raise SpecificationGap(
                f"wildcard.candidate_generation.required_signal.{signal}",
                "Wildcard source signal must be a continuous numeric signal.",
            )
    candidate = dict(base_values)
    for signal, delta in config.WILDCARD_DELTAS[archetype].items():
        candidate[signal] = clamp01(candidate[signal] + float(delta))
    return candidate


def build_wildcard_candidate(profile: Mapping[str, Any], archetype: str) -> dict[str, Any]:
    signals = perturb_signals(profile, archetype)
    source = profile.get("signals")
    if not isinstance(source, Mapping):
        raise SpecificationGap("wildcard.candidate_generation.signal_object", "Wildcard construction requires the stored deterministic signal object.")
    for field in ("signal_model_version", "question_categories", "per_question"):
        if field not in source:
            raise SpecificationGap(f"wildcard.candidate_generation.signal_object.{field}", "Wildcard construction requires the complete stored signal object.")
    raw = {
        "signal_model_version": source["signal_model_version"],
        "signals": signals,
        "question_categories": dict(source["question_categories"]),
        "per_question": {question: dict(values) for question, values in source["per_question"].items()},
    }
    return {
        "archetype": archetype,
        "deltas": dict(config.WILDCARD_DELTAS[archetype]),
        "signals": raw,
        "derived": derive_dimensions(raw),
        "engine_versions": dict(profile["engine_versions"]),
        "wildcard_scoring_config_version": config.WILDCARD_SCORING_CONFIG_VERSION,
        "ephemeral": True,
    }


def _candidate_metrics(profile: Mapping[str, Any], candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Run D1-D9 comparison without classifying chemistry or persisting a user."""
    results = compare_all_dimensions(profile["derived"], candidate["derived"])
    weights = wildcard_effective_weights()
    dimensions = config.WILDCARD_DIMENSION_ORDER
    difference = sum(results[d].difference_score * weights[d] for d in dimensions)
    components = component_scores(results, weights)
    counts = friction_counts(results)
    return {
        "scoring_mode": "WILDCARD",
        "wildcard_scoring_config_version": config.WILDCARD_SCORING_CONFIG_VERSION,
        "difference_score": difference,
        "complementarity_score": components["complementarity_score"],
        "friction_score": components["friction_score"],
        **counts,
        "dimension_results": {d: results[d].as_dict() for d in dimensions},
    }


def materialize_wildcard_candidates(profile: Mapping[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    _validate_deltas()
    for archetype in config.WILDCARD_ORDER:
        candidate = build_wildcard_candidate(profile, archetype)
        candidate.update(_candidate_metrics(profile, candidate))
        candidates.append(candidate)
    return candidates


def select_wildcard_from_candidates(candidates: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    _validate_deltas()
    order = {name: index for index, name in enumerate(config.WILDCARD_ORDER)}
    for index, candidate in enumerate(candidates):
        if candidate.get("archetype") not in order:
            raise ConfigurationError(f"wildcard.candidates[{index}].archetype", "Unknown wildcard archetype.")
        required = ("difference_score", "complementarity_score", "friction_score", "hard_friction_count")
        missing = [key for key in required if key not in candidate]
        if missing:
            raise ConfigurationError(f"wildcard.candidates[{index}]", f"Missing wildcard candidate fields: {missing}.")
        for field in ("difference_score", "complementarity_score", "friction_score"):
            if not 0.0 <= float(candidate[field]) <= 1.0:
                raise SpecificationGap(f"wildcard.candidates[{index}].{field}", "Wildcard candidate scores must be in [0,1].")
        if int(candidate["hard_friction_count"]) < 0:
            raise SpecificationGap(f"wildcard.candidates[{index}].hard_friction_count", "Wildcard hard-friction count cannot be negative.")
    eligible = [
        candidate
        for candidate in candidates
        if float(candidate["difference_score"]) >= config.WILDCARD_THRESHOLDS["difference"]
        and float(candidate["complementarity_score"]) >= config.WILDCARD_THRESHOLDS["complementarity"]
        and float(candidate["friction_score"]) < config.WILDCARD_THRESHOLDS["friction_exclusive"]
        and int(candidate["hard_friction_count"]) == config.WILDCARD_THRESHOLDS["hard_friction_count"]
    ]
    if not eligible:
        return None
    ranked = sorted(
        eligible,
        key=lambda candidate: (
            -(float(candidate["difference_score"]) * float(candidate["complementarity_score"]) * (1.0 - float(candidate["friction_score"]))),
            -float(candidate["complementarity_score"]),
            -float(candidate["difference_score"]),
            order[candidate["archetype"]],
        ),
    )
    selected = dict(ranked[0])
    selected["wildcard_score"] = selected["difference_score"] * selected["complementarity_score"] * (1.0 - selected["friction_score"])
    return selected


def select_wildcard(profile: Mapping[str, Any]) -> dict[str, Any] | None:
    return select_wildcard_from_candidates(materialize_wildcard_candidates(profile))


__all__ = ["build_wildcard_candidate", "materialize_wildcard_candidates", "perturb_signals", "select_wildcard", "select_wildcard_from_candidates"]
