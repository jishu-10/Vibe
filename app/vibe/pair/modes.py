"""Relationship-mode weights and canonical configuration identity."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from typing import Any

from app.vibe.config import v1_1_0 as config
from app.vibe.contracts import ConfigurationError, RelationshipMode, ensure_relationship_mode


def effective_mode_weights(mode: str | RelationshipMode) -> dict[str, float]:
    selected = ensure_relationship_mode(mode).value
    if not isinstance(config.MODE_BASE_WEIGHTS, Mapping):
        raise ConfigurationError("mode_base_weights", "Relationship-mode base weights must be a mapping.")
    if not isinstance(config.MODE_MULTIPLIERS, Mapping):
        raise ConfigurationError("mode_multipliers", "Relationship-mode multipliers must be a mapping.")
    multipliers = config.MODE_MULTIPLIERS.get(selected)
    if multipliers is None:
        raise ConfigurationError(f"mode_multipliers.{selected}", "Missing relationship-mode multiplier configuration.")
    if not isinstance(multipliers, Mapping):
        raise ConfigurationError(f"mode_multipliers.{selected}", "Relationship-mode multipliers must be a mapping.")
    required_dimensions = set(config.MODE_BASE_WEIGHTS)
    if set(multipliers) != required_dimensions:
        raise ConfigurationError(f"mode_multipliers.{selected}", "Relationship-mode multipliers must cover D1-D10 exactly.")
    values = tuple(config.MODE_BASE_WEIGHTS.values()) + tuple(multipliers.values())
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) for value in values):
        raise ConfigurationError(f"mode_multipliers.{selected}", "Relationship-mode multipliers must be finite numeric values.")
    raw = {dimension: config.MODE_BASE_WEIGHTS[dimension] * multipliers[dimension] for dimension in config.MODE_BASE_WEIGHTS}
    denominator = sum(raw[dimension] for dimension in config.DIMENSION_ORDER)
    if denominator <= 0:
        raise ConfigurationError(f"mode_weights.{selected}", "D1-D9 normalization denominator must be positive.")
    normalized = {dimension: raw[dimension] / denominator for dimension in config.DIMENSION_ORDER}
    normalized["D10"] = 0.0
    return normalized


def wildcard_effective_weights() -> dict[str, float]:
    """Return the dedicated individual-profile Wildcard scoring weights."""
    validate_wildcard_configuration()
    expected_total = sum(config.WILDCARD_EFFECTIVE_WEIGHTS.values()) / config.WILDCARD_WEIGHT_DENOMINATOR
    normalized = {dimension: config.WILDCARD_NORMALIZED_WEIGHTS[dimension] for dimension in config.WILDCARD_DIMENSION_ORDER}
    normalized["D10"] = 0.0
    if abs(sum(normalized[dimension] for dimension in config.WILDCARD_DIMENSION_ORDER) - expected_total) > 1e-12:
        raise ConfigurationError("wildcard_weights", "Wildcard normalized weights do not match their configured denominator.")
    return normalized


def _validate_numeric_mapping(mapping: Mapping[str, Any], path: str) -> None:
    for key, value in mapping.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise ConfigurationError(f"{path}.{key}", "Configuration values must be finite numeric values.")


def validate_wildcard_configuration() -> None:
    """Validate every configuration block consumed by Wildcard generation."""
    if not isinstance(config.WILDCARD_SCORING_CONFIG_VERSION, str) or not config.WILDCARD_SCORING_CONFIG_VERSION:
        raise ConfigurationError("wildcard_scoring_config_version", "Wildcard scoring configuration version is required.")
    if not isinstance(config.WILDCARD_ORDER, (tuple, list)):
        raise ConfigurationError("wildcard_order", "Wildcard archetype order must be a sequence.")
    if not isinstance(config.WILDCARD_DELTAS, Mapping):
        raise ConfigurationError("wildcard_deltas", "Wildcard delta configuration must be a mapping.")
    if set(config.WILDCARD_DELTAS) != set(config.WILDCARD_ORDER):
        raise ConfigurationError("wildcard_deltas", "Wildcard delta configuration must contain exactly the six canonical archetypes.")
    for archetype, deltas in config.WILDCARD_DELTAS.items():
        if not isinstance(deltas, Mapping) or not deltas:
            raise ConfigurationError(f"wildcard_deltas.{archetype}", "Wildcard deltas must be non-empty mappings.")
        for signal, delta in deltas.items():
            if signal not in config.CONTINUOUS_SIGNAL_NAMES:
                raise ConfigurationError(f"wildcard_deltas.{archetype}.{signal}", "Wildcard delta references an unknown signal name.")
            if isinstance(delta, bool) or not isinstance(delta, (int, float)) or not math.isfinite(float(delta)):
                raise ConfigurationError(f"wildcard_deltas.{archetype}.{signal}", "Wildcard deltas must be finite numeric values.")
    for name in ("WILDCARD_BASE_WEIGHTS", "WILDCARD_MULTIPLIERS", "WILDCARD_EFFECTIVE_WEIGHTS", "WILDCARD_NORMALIZED_WEIGHTS"):
        if not isinstance(getattr(config, name), Mapping):
            raise ConfigurationError(name.lower(), "Wildcard weight configuration must be a mapping.")
    if set(config.WILDCARD_BASE_WEIGHTS) != set(config.WILDCARD_DIMENSION_ORDER):
        raise ConfigurationError("wildcard_base_weights", "Wildcard base weights must cover D1-D9 exactly.")
    if set(config.WILDCARD_MULTIPLIERS) != set(config.WILDCARD_DIMENSION_ORDER):
        raise ConfigurationError("wildcard_multipliers", "Wildcard multipliers must cover D1-D9 exactly.")
    if set(config.WILDCARD_EFFECTIVE_WEIGHTS) != set(config.WILDCARD_DIMENSION_ORDER):
        raise ConfigurationError("wildcard_effective_weights", "Wildcard effective weights must cover D1-D9 exactly.")
    if set(config.WILDCARD_NORMALIZED_WEIGHTS) != set(config.WILDCARD_DIMENSION_ORDER):
        raise ConfigurationError("wildcard_normalized_weights", "Wildcard normalized weights must cover D1-D9 exactly.")
    _validate_numeric_mapping(config.WILDCARD_BASE_WEIGHTS, "wildcard_base_weights")
    _validate_numeric_mapping(config.WILDCARD_MULTIPLIERS, "wildcard_multipliers")
    _validate_numeric_mapping(config.WILDCARD_EFFECTIVE_WEIGHTS, "wildcard_effective_weights")
    _validate_numeric_mapping(config.WILDCARD_NORMALIZED_WEIGHTS, "wildcard_normalized_weights")
    if not isinstance(config.WILDCARD_WEIGHT_DENOMINATOR, (int, float)) or isinstance(config.WILDCARD_WEIGHT_DENOMINATOR, bool) or not math.isfinite(float(config.WILDCARD_WEIGHT_DENOMINATOR)) or config.WILDCARD_WEIGHT_DENOMINATOR <= 0:
        raise ConfigurationError("wildcard_weight_denominator", "Wildcard weight denominator must be a positive finite number.")
    if any(config.WILDCARD_BASE_WEIGHTS[dimension] <= 0 or config.WILDCARD_MULTIPLIERS[dimension] <= 0 for dimension in config.WILDCARD_DIMENSION_ORDER):
        raise ConfigurationError("wildcard_weights", "Wildcard base weights and multipliers must be positive.")
    for dimension in config.WILDCARD_DIMENSION_ORDER:
        expected_effective = config.WILDCARD_BASE_WEIGHTS[dimension] * config.WILDCARD_MULTIPLIERS[dimension]
        expected_normalized = expected_effective / config.WILDCARD_WEIGHT_DENOMINATOR
        if abs(config.WILDCARD_EFFECTIVE_WEIGHTS[dimension] - expected_effective) > 1e-12:
            raise ConfigurationError(f"wildcard_effective_weights.{dimension}", "Wildcard effective weight does not match base weight times multiplier.")
        if abs(config.WILDCARD_NORMALIZED_WEIGHTS[dimension] - expected_normalized) > 1e-12:
            raise ConfigurationError(f"wildcard_normalized_weights.{dimension}", "Wildcard normalized weight does not match the configured denominator.")
    if config.WILDCARD_D10_PARTICIPATES is not False:
        raise ConfigurationError("wildcard_d10_participates", "Wildcard D10 participation must be explicitly false.")
    required_thresholds = {"difference", "complementarity", "friction_exclusive", "hard_friction_count"}
    if not isinstance(config.WILDCARD_THRESHOLDS, Mapping):
        raise ConfigurationError("wildcard_thresholds", "Wildcard thresholds must be a mapping.")
    if set(config.WILDCARD_THRESHOLDS) != required_thresholds:
        raise ConfigurationError("wildcard_thresholds", "Wildcard thresholds are incomplete.")
    for key in ("difference", "complementarity", "friction_exclusive"):
        value = config.WILDCARD_THRESHOLDS[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or not 0.0 <= float(value) <= 1.0:
            raise ConfigurationError(f"wildcard_thresholds.{key}", "Wildcard score thresholds must be finite values in [0,1].")
    if config.WILDCARD_THRESHOLDS["hard_friction_count"] != 0:
        raise ConfigurationError("wildcard_thresholds.hard_friction_count", "Wildcard hard-friction count threshold must be zero.")


def config_payload() -> dict[str, Any]:
    return {
        "versions": dict(config.VERSIONS),
        "question_weights": dict(config.QUESTION_WEIGHTS),
        "questions": list(config.QUESTIONS),
        "signal_map": config.SIGNAL_MAP,
        "global_component_weights": dict(config.GLOBAL_COMPONENT_WEIGHTS),
        "thresholds": dict(config.THRESHOLDS),
        "chemistry_thresholds": dict(config.CHEMISTRY_THRESHOLDS),
        "phase_adjustment": dict(config.PHASE_ADJUSTMENT),
        "narrative_limits": dict(config.NARRATIVE_LIMITS),
        "individual_thresholds": dict(config.INDIVIDUAL_THRESHOLDS),
        "pair_policy_thresholds": dict(config.PAIR_POLICY_THRESHOLDS),
        "wildcard_thresholds": dict(config.WILDCARD_THRESHOLDS),
        "wildcard_deltas": {name: dict(delta) for name, delta in config.WILDCARD_DELTAS.items()},
        "wildcard_scoring": {
            "config_version": config.WILDCARD_SCORING_CONFIG_VERSION,
            "dimension_order": list(config.WILDCARD_DIMENSION_ORDER),
            "base_weights": dict(config.WILDCARD_BASE_WEIGHTS),
            "multipliers": dict(config.WILDCARD_MULTIPLIERS),
            "effective_weights": dict(config.WILDCARD_EFFECTIVE_WEIGHTS),
            "normalized_weights": dict(config.WILDCARD_NORMALIZED_WEIGHTS),
            "weight_denominator": config.WILDCARD_WEIGHT_DENOMINATOR,
            "d10_participates": config.WILDCARD_D10_PARTICIPATES,
        },
        "continuous_signal_names": list(config.CONTINUOUS_SIGNAL_NAMES),
        "contrast_weights": dict(config.CONTRAST_WEIGHTS),
        "contrast_normalized_weights": dict(config.CONTRAST_NORMALIZED_WEIGHTS),
        "profile_weights": dict(config.PROFILE_WEIGHTS),
        "matrices": {"D1": config.D1_MATRIX, "D3": config.D3_MATRIX, "D6": config.D6_MATRIX, "D7": config.D7_MATRIX, "D10": config.D10_MATRIX},
        "mode_base_weights": dict(config.MODE_BASE_WEIGHTS),
        "mode_multipliers": config.MODE_MULTIPLIERS,
        "friction_multipliers": dict(config.FRICTION_MULTIPLIERS),
        "complementarity_multipliers": dict(config.COMPLEMENTARITY_MULTIPLIERS),
        "feature_weights": {"D4": dict(config.D4_FEATURE_WEIGHTS), "D5": dict(config.D5_FEATURE_WEIGHTS), "D8": dict(config.D8_FEATURE_WEIGHTS), "D9": dict(config.D9_FEATURE_WEIGHTS)},
        "pair_sets": {"D2_productive": [sorted(pair) for pair in config.D2_PRODUCTIVE_PAIRS], "D2_interference": [sorted(pair) for pair in config.D2_INTERFERENCE_PAIRS], "D5_productive": [sorted(pair) for pair in config.D5_PRODUCTIVE_PAIRS], "D8_productive": [sorted(pair) for pair in config.D8_PRODUCTIVE_PAIRS], "D8_hard": [sorted(pair) for pair in config.D8_HARD_PAIRS], "D9_productive": [sorted(pair) for pair in config.D9_PRODUCTIVE_PAIRS]},
        "libraries": {"pulls": sorted(config.PULL_LIBRARY), "drains": sorted(config.DRAIN_LIBRARY)},
        "contrast_prototypes": {key: list(value) for key, value in config.CONTRAST_PROTOTYPES.items()},
        "forbidden_claims": list(config.FORBIDDEN_CLAIMS),
        "generic_terms": sorted(config.NARRATIVE_GENERIC_TERMS),
        "claim_terms": {dimension: sorted(terms) for dimension, terms in config.NARRATIVE_CLAIM_TERMS.items()},
        "tie_breaks": {"D2": config.D2_TIE_ORDER, "D9": config.D9_TIE_ORDER, "wildcard": config.WILDCARD_ORDER},
    }


def config_hash() -> str:
    canonical = json.dumps(config_payload(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_configuration() -> None:
    if not isinstance(config.VERSIONS, Mapping):
        raise ConfigurationError("versions", "Canonical version configuration must be a mapping.")
    required_versions = {"questionnaire", "signal_model", "dimension_model", "scoring_model", "narrative_prompt", "completion_amendment"}
    if set(config.VERSIONS) != required_versions:
        raise ConfigurationError("versions", "Canonical version keys are incomplete.")
    if not isinstance(config.QUESTION_WEIGHTS, Mapping):
        raise ConfigurationError("question_weights", "Question weights must be a mapping.")
    if abs(sum(config.QUESTION_WEIGHTS.values()) - 10.05) > 1e-12:
        raise ConfigurationError("question_weights", "Question weights must sum to 10.05 exactly in configured precision.")
    for mode in RelationshipMode:
        weights = effective_mode_weights(mode)
        if abs(sum(weights[dimension] for dimension in config.DIMENSION_ORDER) - 1.0) > 1e-12:
            raise ConfigurationError(f"mode_weights.{mode.value}", "D1-D9 normalized weights must sum to 1.")
    validate_wildcard_configuration()
    for matrix_name in ("D1_MATRIX", "D3_MATRIX", "D6_MATRIX", "D7_MATRIX", "D10_MATRIX"):
        matrix = getattr(config, matrix_name)
        if not isinstance(matrix, Mapping) or not matrix:
            raise ConfigurationError(matrix_name, "Canonical matrix configuration is required.")
        for row, values in matrix.items():
            if not isinstance(values, Mapping):
                raise ConfigurationError(f"{matrix_name}.{row}", "Canonical matrix rows must be mappings.")
            for column in matrix:
                if column not in values:
                    raise ConfigurationError(f"{matrix_name}.{row}.{column}", "Matrix is missing a canonical entry.")
    if not isinstance(config.CONTRAST_WEIGHTS, Mapping) or not isinstance(config.CONTRAST_WEIGHT_DENOMINATOR, (int, float)) or isinstance(config.CONTRAST_WEIGHT_DENOMINATOR, bool) or not math.isfinite(float(config.CONTRAST_WEIGHT_DENOMINATOR)) or set(config.CONTRAST_WEIGHTS) != set(config.DIMENSION_ORDER) or abs(config.CONTRAST_WEIGHT_DENOMINATOR - 10.30) > 1e-12:
        raise ConfigurationError("contrast_weights", "Contrast weights must cover D1-D9 and use the canonical 10.30 denominator.")
    if not isinstance(config.NARRATIVE_CLAIM_TERMS, Mapping) or set(config.NARRATIVE_CLAIM_TERMS) != set(config.DIMENSION_ORDER) | {"D10"}:
        raise ConfigurationError("narrative_claim_terms", "Narrative claim vocabulary must cover D1-D10 exactly.")
    for dimension, terms in config.NARRATIVE_CLAIM_TERMS.items():
        if not isinstance(terms, (set, frozenset)) or not terms or any(not isinstance(term, str) or not term for term in terms):
            raise ConfigurationError(f"narrative_claim_terms.{dimension}", "Narrative claim vocabulary must contain non-empty string terms.")
    required_prototypes = {"HIGH_ENERGY", "VERY_QUIET", "HIGHLY_STRUCTURED", "HIGHLY_SPONTANEOUS"}
    if not isinstance(config.CONTRAST_PROTOTYPES, Mapping):
        raise ConfigurationError("contrast_prototypes", "Contrast prototype configuration must be a mapping.")
    if set(config.CONTRAST_PROTOTYPES) != required_prototypes:
        raise ConfigurationError("contrast_prototypes", "Contrast prototype configuration must contain the four canonical prototypes.")
    option_ids = {option_id for question in config.QUESTIONS for option_id in question["options"]}
    for prototype, answers in config.CONTRAST_PROTOTYPES.items():
        if not isinstance(answers, tuple) or len(answers) != 10 or any(answer not in option_ids for answer in answers):
            raise ConfigurationError(f"contrast_prototypes.{prototype}", "Contrast prototypes must contain ten canonical answer IDs.")
    for mapping_name in ("THRESHOLDS", "CHEMISTRY_THRESHOLDS", "PAIR_POLICY_THRESHOLDS", "INDIVIDUAL_THRESHOLDS"):
        mapping = getattr(config, mapping_name)
        if not isinstance(mapping, Mapping) or not mapping:
            raise ConfigurationError(mapping_name, "Canonical threshold configuration is required.")
        for key, value in mapping.items():
            values = value if isinstance(value, tuple) else (value,)
            if any(isinstance(item, bool) or not isinstance(item, (int, float)) or not math.isfinite(float(item)) for item in values):
                raise ConfigurationError(f"{mapping_name}.{key}", "Thresholds must be finite numeric values.")
