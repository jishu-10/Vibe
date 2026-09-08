"""On-demand deterministic pair engine."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.vibe.config.v1_1_0 import engine_versions
from app.vibe.contracts import DimensionResult, RelationshipMode, SpecificationGap, ensure_relationship_mode
from app.vibe.narrative import build_claim_contract
from app.vibe.pair.aggregate import classify, component_scores, final_scores, friction_counts
from app.vibe.pair.dimensions import compare_all_dimensions
from app.vibe.pair.evidence import confidence_label, select_evidence
from app.vibe.pair.modes import config_hash, effective_mode_weights, validate_configuration


def _versions(profile: Mapping[str, Any]) -> Mapping[str, str]:
    value = profile.get("engine_versions")
    if not isinstance(value, Mapping):
        raise SpecificationGap("pair.engine_versions", "Pair analysis requires versioned profile metadata.")
    return value


def assert_compatible_versions(a: Mapping[str, Any], b: Mapping[str, Any]) -> None:
    expected = engine_versions()
    versions_a = _versions(a)
    versions_b = _versions(b)
    if (
        dict(versions_a) != dict(expected)
        or dict(versions_b) != dict(expected)
        or dict(versions_a) != dict(versions_b)
        or a.get("config_hash") != config_hash()
        or b.get("config_hash") != config_hash()
        or a.get("config_hash") != b.get("config_hash")
    ):
        from app.vibe.contracts import VibeError

        raise VibeError("VERSION_MISMATCH", "pair.engine_versions", "Pair profiles use incompatible model versions.", 409)


def analyze_pair(a: Mapping[str, Any], b: Mapping[str, Any], mode: str | RelationshipMode) -> dict[str, Any]:
    validate_configuration()
    selected_mode = ensure_relationship_mode(mode)
    assert_compatible_versions(a, b)
    weights = effective_mode_weights(selected_mode)
    derived_a = a["derived"]
    derived_b = b["derived"]
    if not isinstance(derived_a, Mapping) or not isinstance(derived_b, Mapping):
        raise SpecificationGap("pair.derived", "Pair analysis requires both deterministic dimension representations.")
    results = compare_all_dimensions(derived_a, derived_b)
    components = component_scores(results, weights)
    phase_adjustment = results["D10"].interaction_score
    scores = final_scores(components, phase_adjustment)
    counts = friction_counts(results)
    classification, fallback_used = classify(components, scores, counts)
    selected_evidence, pair_confidence = select_evidence(results, weights, derived_a, derived_b)
    internal = {
        "classification": classification.value,
        "relationship_mode": selected_mode.value,
        **components,
        **scores,
        "phase_adjustment": phase_adjustment,
        **counts,
        "fallback_used": fallback_used,
        "confidence": {"value": pair_confidence, "label": confidence_label(pair_confidence).value},
        "evidence": [item.as_dict() for item in selected_evidence],
        "dimension_results": {dimension: result.as_dict() for dimension, result in results.items()},
        "engine_versions": engine_versions(),
        "config_hash": config_hash(),
        "profile_versions": {"user_a": a["profile_version"], "user_b": b["profile_version"]},
        "request_id": None,
        "cache_hit": False,
        "spec_error_path": None,
    }
    internal["claim_contract"] = build_claim_contract(internal)
    internal["trace"] = {
        "dimensions": {dimension: {"answer_paths_a": list(a["derived"][dimension].get("answer_paths", ())), "answer_paths_b": list(b["derived"][dimension].get("answer_paths", ())), "signal_paths_a": sorted(set(a["derived"][dimension].get("features", {})) | set(a["derived"][dimension].get("scores", {}))), "signal_paths_b": sorted(set(b["derived"][dimension].get("features", {})) | set(b["derived"][dimension].get("scores", {}))), "rule": f"pair.{dimension}", "interaction_score": result.interaction_score, "weight": weights.get(dimension, 0.0), "contribution": result.interaction_score * weights.get(dimension, 0.0), "result": result.as_dict()} for dimension, result in results.items()},
        "components": components,
        "final": scores,
        "classification": classification.value,
        "evidence": [item.as_dict() for item in selected_evidence],
    }
    return internal


def public_pair_result(pair_result_id: str, pair_result: Mapping[str, Any], narrative: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "pair_result_id": pair_result_id,
        "relationship_mode": pair_result["relationship_mode"],
        "chemistry": pair_result["classification"],
        "why_you_two": narrative["why_you_two"],
        "confidence": pair_result["confidence"]["label"],
    }
