"""Individual Vibe representation and deterministic profile facts."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from app.vibe.config.v1_1_0 import (
    DIMENSION_MODEL_VERSION,
    NARRATIVE_PROMPT_VERSION,
    PULL_LIBRARY,
    DRAIN_LIBRARY,
    QUESTIONNAIRE_VERSION,
    SIGNAL_MODEL_VERSION,
    engine_versions,
)
from app.vibe.contracts import ConfidenceLabel
from app.vibe.confidence import profile_confidence, section_confidence
from app.vibe.contrast import build_contrast_analysis
from app.vibe.dimensions import derive_dimensions
from app.vibe.narrative import render_profile_narrative
from app.vibe.pair.modes import config_hash
from app.vibe.questionnaire import validate_answers
from app.vibe.signal_map import map_answers_to_signals
from app.vibe.wildcard import select_wildcard


def profile_version(answers: Mapping[str, str]) -> str:
    canonical = json.dumps(
        {
            "answers": {key: answers[key] for key in sorted(answers)},
            "questionnaire_version": QUESTIONNAIRE_VERSION,
            "signal_model_version": SIGNAL_MODEL_VERSION,
            "dimension_model_version": DIMENSION_MODEL_VERSION,
            "config_hash": config_hash(),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _profile_signal_view(raw: Mapping[str, Any], derived: Mapping[str, Any]) -> dict[str, Any]:
    view: dict[str, Any] = dict(raw["signals"])
    view.update(derived["metrics"])
    view["Q6_category"] = raw["question_categories"]["Q6"]
    view["planning_style"] = derived["D6"]["planning_style"]
    view["current_phase"] = derived["D6"]["current_phase"]
    return view


def _pulls(view: Mapping[str, Any]) -> list[str]:
    # The contract fixes eligibility and a fixed code tie order. The first
    # predicate signal is used as deterministic evidence strength for ranking.
    signal_order = {
        "BANTER_WITHOUT_FORCING": ("humor_connection", "playful_affection"),
        "REAL_CONVERSATION": ("emotional_depth", "intellectual_depth"),
        "EASY_FLOW": ("conversation_ease",),
        "ATTENTIVE_PEOPLE": ("attentional_affection",),
        "PATIENT_ENTRY": ("social_selectivity", "warmup_speed"),
        "PLAYFUL_WARMTH": ("humor_connection", "social_presence"),
        "SPACE_WITH_PRESENCE": ("solitary_recovery", "attentional_presence"),
        "FLEXIBLE_PLANNING": ("flexibility", "spontaneity"),
    }
    eligible = [code for code, predicate in PULL_LIBRARY.items() if predicate(view)]
    return sorted(eligible, key=lambda code: (-max(float(view[name]) for name in signal_order[code]), -sum(float(view[name]) for name in signal_order[code]), code))[:4]


def _drains(view: Mapping[str, Any]) -> list[str]:
    signal_order = {
        "CONSTANT_SOCIAL_DEMAND": ("social_energy", "solitary_recovery"),
        "FORCED_OPENING": ("social_selectivity", "warmup_speed"),
        "LAST_MINUTE_CHANGE": ("structure_preference",),
        "OVERLY_CONTROLLED_PLANS": ("spontaneity",),
        "LIGHT_TALK_ONLY": ("connection_depth",),
        "NO_BANTER": ("humor_connection",),
        "IMMEDIATE_EMOTIONAL_DEMAND": ("processing_delay",),
    }
    eligible = [code for code, predicate in DRAIN_LIBRARY.items() if predicate(view)]
    return sorted(eligible, key=lambda code: (-max(float(view[name]) for name in signal_order[code]), code))[:4]


def _confidence_units(derived: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    units: dict[str, list[dict[str, Any]]] = {}
    for dimension in (f"D{i}" for i in range(1, 11)):
        paths = tuple(derived[dimension].get("answer_paths", ()))
        units[dimension] = [
            {"source": path, "polarity": "SUPPORT", "strength_value": 1.0, "answer_path": path}
            for path in paths
        ]
    return units


def build_partial_profile(user_id: str, answers: Mapping[str, str]) -> dict[str, Any]:
    validated = validate_answers(answers)
    raw = map_answers_to_signals(validated)
    derived = derive_dimensions(raw)
    view = _profile_signal_view(raw, derived)
    confidence_units = _confidence_units(derived)
    section_values = {dimension: section_confidence(units) for dimension, units in confidence_units.items()}
    confidence_value, confidence_label = profile_confidence(section_values)
    evidence = [
        {
            "evidence_id": f"profile:{dimension}",
            "dimension": dimension,
            "answer_paths": list(fact.get("answer_paths", ())),
            "signal_paths": sorted(set(fact.get("features", {})) | set(fact.get("scores", {})) | {key for key in ("category", "primary", "secondary", "planning_style", "current_phase") if key in fact}),
            "rule": f"dimensions.{dimension}",
            "fact": fact,
            "confidence_units": confidence_units[dimension],
            "section_confidence": section_values[dimension],
        }
        for dimension, fact in derived.items()
        if dimension.startswith("D")
    ]
    facts = {
        "your_vibe": {"conversation_orientation": derived["D1"]["category"], "connection_style": derived["D2"]["selected_modes"], "affection_style": derived["D3"]["category"], "interaction_pace": derived["D8"]["category"]},
        "social_rhythm": derived["D4"],
        "connection_style": derived["D2"],
        "energy_signature": derived["D9"],
        "what_pulls_you_in": _pulls(view),
        "what_drains_you": _drains(view),
        "current_phase": derived["D10"],
        "how_you_are_with_different_people": [],
        "wildcard": None,
    }
    return {
        "user_id": user_id,
        "profile_version": profile_version(validated),
        "answers": validated,
        "signals": raw,
        "derived": derived,
        "facts": facts,
        "evidence": evidence,
        "confidence": {"value": confidence_value, "label": confidence_label.value, "sections": section_values},
        "confidence_units": confidence_units,
        "engine_versions": engine_versions(),
        "config_hash": config_hash(),
    }


def build_profile(user_id: str, answers: Mapping[str, str]) -> dict[str, Any]:
    profile = build_partial_profile(user_id, answers)
    contrasts = build_contrast_analysis(profile)
    wildcard = select_wildcard(profile)
    profile["facts"]["how_you_are_with_different_people"] = contrasts
    profile["facts"]["wildcard"] = wildcard
    profile["profile_narrative"] = render_profile_narrative(profile)
    return profile
