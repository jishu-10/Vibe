"""Narrative boundary: facts in, wording out; no scoring authority."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from app.vibe.config import v1_1_0 as config
from app.vibe.contracts import Chemistry, ConfidenceLabel, VibeError


def build_claim_contract(pair_result: Mapping[str, Any]) -> dict[str, Any]:
    evidence = pair_result.get("evidence", [])
    allowed = [item["statement_key"] for item in evidence]
    evidence_by_claim: dict[str, list[str]] = {}
    for item in evidence:
        evidence_by_claim.setdefault(item["statement_key"], []).append(item["evidence_id"])
    confidence = pair_result.get("confidence", {}).get("label", ConfidenceLabel.WEAK.value)
    return {
        "allowed_claims": allowed,
        "evidence_by_claim": evidence_by_claim,
        "claim_terms": {
            statement_key: sorted(
                set(config.NARRATIVE_GENERIC_TERMS)
                | set(config.NARRATIVE_CLAIM_TERMS.get(item.get("dimension", ""), ()))
            )
            for statement_key, item in ((item["statement_key"], item) for item in evidence if isinstance(item, Mapping) and "statement_key" in item)
        },
        "forbidden_claims": list(config.FORBIDDEN_CLAIMS),
        "confidence": confidence,
        "fallback_used": bool(pair_result.get("fallback_used", False)),
        "narrative_prompt_version": config.NARRATIVE_PROMPT_VERSION,
    }


def _normalized_terms(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def validate_llm_output(output: Mapping[str, Any], pair_result: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(output, Mapping):
        raise VibeError("NARRATIVE_RENDER_ERROR", "narrative.output", "Narrative renderer did not return an object.", 502)
    evidence_ids = output.get("evidence_ids")
    if not isinstance(evidence_ids, list) or not evidence_ids:
        raise VibeError("NARRATIVE_RENDER_ERROR", "narrative.evidence_ids", "Narrative must cite deterministic evidence.", 502)
    allowed_ids = {item["evidence_id"] for item in pair_result.get("evidence", [])}
    if any(item not in allowed_ids for item in evidence_ids):
        raise VibeError("NARRATIVE_RENDER_ERROR", "narrative.evidence_ids", "Narrative cited unsupported evidence.", 502)
    claim_keys = output.get("claim_keys")
    claim_contract = pair_result.get("claim_contract")
    if not isinstance(claim_keys, list) or not claim_keys or any(not isinstance(key, str) for key in claim_keys):
        raise VibeError("NARRATIVE_RENDER_ERROR", "narrative.claim_keys", "Narrative must declare deterministic claim keys.", 502)
    allowed_claims = set(claim_contract.get("allowed_claims", ())) if isinstance(claim_contract, Mapping) else {
        item["statement_key"] for item in pair_result.get("evidence", [])
    }
    evidence_by_claim = claim_contract.get("evidence_by_claim", {}) if isinstance(claim_contract, Mapping) else {
        item["statement_key"]: [item["evidence_id"]] for item in pair_result.get("evidence", [])
    }
    claim_terms = claim_contract.get("claim_terms", {}) if isinstance(claim_contract, Mapping) else {}
    evidence_by_id = {item["evidence_id"]: item for item in pair_result.get("evidence", [])}
    for index, claim_key in enumerate(claim_keys):
        if claim_key not in allowed_claims:
            raise VibeError("NARRATIVE_RENDER_ERROR", f"narrative.claim_keys[{index}]", "Narrative declared a claim outside the deterministic claim envelope.", 502)
        claim_evidence = set(evidence_by_claim.get(claim_key, ()))
        if not claim_evidence.intersection(evidence_ids):
            raise VibeError("NARRATIVE_RENDER_ERROR", f"narrative.claim_keys[{index}]", "Narrative claim is not linked to its deterministic evidence.", 502)
    text_parts = [str(output.get("title", "")), str(output.get("explanation", ""))]
    text = " ".join(text_parts).lower()
    forbidden = next((claim for claim in config.FORBIDDEN_CLAIMS if claim.lower() in text), None)
    if forbidden is not None:
        raise VibeError("NARRATIVE_RENDER_ERROR", "narrative.claims", f"Forbidden claim: {forbidden}.", 502)
    if not output.get("title") or not output.get("explanation"):
        raise VibeError("NARRATIVE_RENDER_ERROR", "narrative.text", "Narrative title and explanation are required.", 502)
    # Evidence references identify which deterministic facts may be expressed;
    # they do not authorize arbitrary prose.  Every non-generic content term
    # must remain in the deterministic vocabulary for the cited claim(s).
    cited_claim_terms: set[str] = set(config.NARRATIVE_GENERIC_TERMS)
    for claim_key in claim_keys:
        declared_terms = claim_terms.get(claim_key) if isinstance(claim_terms, Mapping) else None
        if declared_terms is None:
            for evidence_id in evidence_by_claim.get(claim_key, ()):
                evidence = evidence_by_id.get(evidence_id)
                if evidence is not None:
                    cited_claim_terms.update(config.NARRATIVE_CLAIM_TERMS.get(evidence.get("dimension"), ()))
        else:
            cited_claim_terms.update(declared_terms)
    unknown_terms = _normalized_terms(text) - cited_claim_terms
    if unknown_terms:
        raise VibeError("NARRATIVE_RENDER_ERROR", "narrative.claims", "Narrative contains content outside the deterministic claim envelope.", 502)
    confidence_label = pair_result.get("confidence", {}).get("label", "WEAK")
    if confidence_label in {ConfidenceLabel.WEAK.value, ConfidenceLabel.MODERATE.value}:
        strong_marker = next((marker for marker in ("definitely", "will", "always", "guarantees", "you are") if marker in text), None)
        if strong_marker is not None:
            raise VibeError("NARRATIVE_RENDER_ERROR", "narrative.claims", "Low-confidence narrative used an unqualified strong claim.", 502)
    return {"title": str(output["title"]), "explanation": str(output["explanation"]), "claim_keys": list(claim_keys), "evidence_ids": list(evidence_ids)}


def render_pair_fallback(pair_result: Mapping[str, Any]) -> dict[str, Any]:
    """Render only deterministic evidence keys when no LLM is available."""
    evidence = pair_result.get("evidence", [])
    positives = [item for item in evidence if item["kind"] in {"positive", "complementary"}]
    frictions = [item for item in evidence if item["kind"] == "friction"]
    label = pair_result["classification"]
    if positives:
        why = [f"The supplied evidence shows {item['statement_key'].replace('_', ' ').lower()}." for item in positives[:3]]
    else:
        why = ["The available evidence does not support a strong positive overlap claim."]
    potential_difference = None
    if frictions:
        potential_difference = f"The thing to watch is {frictions[0]['statement_key'].replace('_', ' ').lower()}."
    meaning = "This could feel different depending on the context and how the two patterns meet."
    return {
        "why_you_two": {
            "why_you_might_vibe": why,
            "potential_difference": potential_difference,
            "what_that_could_mean": meaning,
        },
        "chemistry": label,
        "confidence": pair_result["confidence"]["label"],
        "evidence_ids": [item["evidence_id"] for item in evidence],
        "generated_by": "deterministic_fallback",
    }


def render_approach(pair_result: Mapping[str, Any]) -> dict[str, Any]:
    evidence = pair_result.get("evidence", [])
    confidence = pair_result["confidence"]["value"]
    qualifier = "You might" if confidence < 0.70 else "You probably"
    evidence_text = [item["statement_key"].replace("_", " ").lower() for item in evidence]
    return {
        "tone": "qualified" if confidence < 0.70 else "direct",
        "opener_type": "evidence_led",
        "works": [f"{qualifier} start from {item}." for item in evidence_text[:2]],
        "avoid": [f"Avoid assuming {item} guarantees an outcome." for item in evidence_text[-1:]],
        "better_opener": "Start with a low-pressure question grounded in the context you already share.",
    }


def render_profile_narrative(profile: Mapping[str, Any]) -> dict[str, Any]:
    """Render bounded profile wording from deterministic facts and evidence only."""
    confidence = profile["confidence"]
    qualifier = "You tend to" if confidence["value"] >= 0.70 else "You may"
    derived = profile["derived"]
    evidence = profile.get("evidence", [])
    evidence_ids = [item["evidence_id"] for item in evidence]
    contrasts = []
    for contrast in profile["facts"]["how_you_are_with_different_people"]:
        if contrast["omission_threshold"]:
            wording = "The available signals do not support a specific high-confidence behavior claim here."
        else:
            wording = f"{qualifier} notice a different rhythm around {contrast['primary_dimension'].replace('D', 'dimension ').lower()} in this kind of person."
        contrasts.append({"prototype": contrast["prototype"], "wording": wording, "evidence_dimensions": [item["dimension"] for item in contrast["evidence"]]})
    return {
        "your_vibe": f"{qualifier} connect through {derived['D1']['category'].replace('_', ' ').lower()} conversation.",
        "social_rhythm": f"{qualifier} warm up {derived['D4']['warming'].replace('_', ' ').lower()} and show up {derived['D4']['peak'].replace('_', ' ').lower()}.",
        "connection_style": f"{qualifier} value {', '.join(derived['D2']['selected_modes']).replace('_', ' ').lower()} connection.",
        "energy_signature": f"{qualifier} bring a {derived['D9']['primary'].replace('_', ' ').lower()} energy signature.",
        "what_pulls_you_in": list(profile["facts"]["what_pulls_you_in"]),
        "what_drains_you": list(profile["facts"]["what_drains_you"]),
        "current_phase": f"You are currently in a {derived['D10']['category'].replace('_', ' ').lower()} phase.",
        "how_you_are_with_different_people": contrasts,
        "wildcard": {"archetype": profile["facts"]["wildcard"]["archetype"]} if profile["facts"].get("wildcard") else None,
        "confidence": confidence,
        "evidence_ids": evidence_ids,
        "generated_by": "deterministic_fallback",
    }
