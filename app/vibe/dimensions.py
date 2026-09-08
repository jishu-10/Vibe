"""Deterministic individual dimension calculations."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.vibe.config.v1_1_0 import D2_TIE_ORDER, D9_TIE_ORDER, INDIVIDUAL_THRESHOLDS
from app.vibe.contracts import ConfigurationError, SpecificationGap
from app.vibe.signals import assert_continuous_signal, weighted_signal_average


def _s(raw: Mapping[str, Any], name: str) -> float:
    signals = raw.get("signals")
    if not isinstance(signals, Mapping) or name not in signals:
        raise SpecificationGap(f"dimensions.required_signal.{name}", "Derived dimension calculation requires the complete canonical signal vector.")
    value = signals[name]
    return assert_continuous_signal(value, f"signals.{name}")


def _category(raw: Mapping[str, Any], question_id: str) -> str:
    try:
        value = raw["question_categories"][question_id]
    except KeyError as exc:
        raise ConfigurationError(f"question_categories.{question_id}", "Missing canonical question category.") from exc
    if not isinstance(value, str):
        raise ConfigurationError(f"question_categories.{question_id}", "Category must be a string enum.")
    return value


def _sort_modes(scores: Mapping[str, float], tie_order: tuple[str, ...]) -> list[tuple[str, float]]:
    order = {name: index for index, name in enumerate(tie_order)}
    return sorted(scores.items(), key=lambda item: (-item[1], order[item[0]]))


def _band(value: float, thresholds: tuple[float, ...], labels: tuple[str, ...]) -> str:
    if len(labels) != len(thresholds) + 1:
        raise ConfigurationError("dimensions.band", "Threshold and label bands are not aligned.")
    for threshold, label in zip(thresholds, labels[:-1], strict=True):
        if value < threshold:
            return label
    return labels[-1]


def derive_dimensions(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Return all individual dimensions and supporting metrics without rounding."""

    signals = raw.get("signals")
    if not isinstance(signals, Mapping):
        raise ConfigurationError("dimensions.raw", "Raw signal representation is missing.")

    social_energy = 0.50 * _s(raw, "social_energy") + 0.25 * _s(raw, "energy_contribution") + 0.25 * _s(raw, "social_replenishment")
    social_density = 0.60 * _s(raw, "social_density") + 0.40 * _s(raw, "social_replenishment")
    social_selectivity = 0.40 * (1.0 - max(_s(raw, "group_orientation"), _s(raw, "one_to_one_preference"))) + 0.60 * _s(raw, "social_selectivity")
    connection_depth = max(_s(raw, "intellectual_depth"), _s(raw, "emotional_depth"))
    connection_depth_type = "INTELLECTUAL" if _s(raw, "intellectual_depth") >= _s(raw, "emotional_depth") else "EMOTIONAL"
    humor_connection = 0.50 * _s(raw, "humor_connection") + 0.25 * _s(raw, "humor_presence") + 0.25 * _s(raw, "playful_affection")
    introspection = 0.75 * _s(raw, "introspection") + 0.25 * _s(raw, "processing_delay")

    q2_category = _category(raw, "Q2")
    q3_category = _category(raw, "Q3")
    q4_category = _category(raw, "Q4")
    q5_category = _category(raw, "Q5")
    q6_category = _category(raw, "Q6")
    q7_category = _category(raw, "Q7")
    q8_category = _category(raw, "Q8")
    q9_category = _category(raw, "Q9")

    connection_modes = {
        "DEPTH_LED": 0.60 * connection_depth + 0.20 * _s(raw, "introspection") + 0.20 * _s(raw, "reflection"),
        "EMOTION_LED": 0.70 * _s(raw, "emotional_depth") + 0.30 * _s(raw, "direct_expression"),
        "HUMOR_LED": 0.50 * _s(raw, "humor_connection") + 0.35 * _s(raw, "playful_affection") + 0.15 * _s(raw, "humor_affection"),
        "ATTENTION_LED": 0.40 * _s(raw, "attentional_affection") + 0.25 * _s(raw, "listening") + 0.20 * _s(raw, "memory_for_detail") + 0.15 * _s(raw, "attentional_presence"),
        "PRESENCE_LED": 0.70 * _s(raw, "reliability_affection") + 0.30 * _s(raw, "behavioral_expression"),
        "DIRECT": 0.50 * _s(raw, "direct_expression") + 0.50 * _s(raw, "direct_affection"),
        "EASE_LED": 0.70 * _s(raw, "conversation_ease") + 0.30 * (1.0 - _s(raw, "processing_delay")),
    }
    qualifying_modes = [item for item in _sort_modes(connection_modes, D2_TIE_ORDER) if item[1] >= INDIVIDUAL_THRESHOLDS["connection_mode_qualifying"]]
    selected_modes = qualifying_modes[:2] if qualifying_modes else _sort_modes(connection_modes, D2_TIE_ORDER)[:1]

    if _s(raw, "processing_variability") >= INDIVIDUAL_THRESHOLDS["pace_variable"]:
        interaction_pace = "VARIABLE"
    elif _s(raw, "action_orientation") >= INDIVIDUAL_THRESHOLDS["pace_action_orientation"] and _s(raw, "processing_delay") <= INDIVIDUAL_THRESHOLDS["pace_action_delay_max"]:
        interaction_pace = "ACTION_FIRST"
    elif _s(raw, "processing_delay") >= INDIVIDUAL_THRESHOLDS["pace_process_delay"] and _s(raw, "introspection") >= INDIVIDUAL_THRESHOLDS["pace_introspection"]:
        interaction_pace = "PROCESS_FIRST"
    elif _s(raw, "initial_observation") >= INDIVIDUAL_THRESHOLDS["pace_observation"] and _s(raw, "warmup_speed") <= INDIVIDUAL_THRESHOLDS["pace_warmup_observation_max"]:
        interaction_pace = "OBSERVATIONAL"
    elif _s(raw, "initial_openness") >= INDIVIDUAL_THRESHOLDS["pace_openness"] and _s(raw, "warmup_speed") >= INDIVIDUAL_THRESHOLDS["pace_warmup_immediate"]:
        interaction_pace = "IMMEDIATE"
    else:
        interaction_pace = "GRADUAL"

    energy_scores = {
        "ENERGIZER": 0.40 * _s(raw, "social_energy") + 0.30 * _s(raw, "energy_contribution") + 0.20 * _s(raw, "social_presence") + 0.10 * (1.0 - _s(raw, "solitary_recovery")),
        "RELAXED": 0.55 * _s(raw, "relaxed_presence") + 0.25 * (1.0 - _s(raw, "energy_contribution")) + 0.20 * _s(raw, "social_energy"),
        "PLAYFUL": 0.55 * _s(raw, "humor_presence") + 0.25 * _s(raw, "playful_affection") + 0.20 * _s(raw, "social_presence"),
        "TUNED_IN": 0.55 * _s(raw, "attentional_presence") + 0.25 * _s(raw, "attentional_affection") + 0.20 * (1.0 - _s(raw, "social_energy")),
        "UNDERSTATED": 0.45 * (1.0 - _s(raw, "social_presence")) + 0.30 * (1.0 - _s(raw, "energy_contribution")) + 0.25 * _s(raw, "solitary_recovery"),
        "INTENSE": 0.50 * _s(raw, "social_energy") + 0.25 * _s(raw, "introspection") + 0.25 * _s(raw, "direct_expression"),
        "SOCIAL_CATALYST": 0.45 * _s(raw, "social_energy") + 0.30 * _s(raw, "social_presence") + 0.25 * _s(raw, "energy_contribution"),
    }
    sorted_energy = _sort_modes(energy_scores, D9_TIE_ORDER)
    primary_energy, primary_energy_score = sorted_energy[0]
    secondary_energy = None
    if len(sorted_energy) > 1 and sorted_energy[1][1] >= INDIVIDUAL_THRESHOLDS["energy_secondary_score"] and primary_energy_score - sorted_energy[1][1] <= INDIVIDUAL_THRESHOLDS["energy_secondary_delta"]:
        secondary_energy = sorted_energy[1][0]

    opening_map = {
        "IMMEDIATE_OPEN": "IMMEDIATE",
        "SELECTIVE_OPEN": "SELECTIVE",
        "OBSERVATIONAL": "OBSERVATIONAL",
        "SLOW_START": "SLOW",
    }
    warmup_score = _s(raw, "warmup_speed")
    warming = "FAST_WARM" if warmup_score >= INDIVIDUAL_THRESHOLDS["rhythm_warm_fast"] else "MODERATE_WARM" if warmup_score >= INDIVIDUAL_THRESHOLDS["rhythm_warm_moderate"] else "SLOW_WARM"
    peaks = {
        "PLAYFUL": _s(raw, "humor_connection") >= INDIVIDUAL_THRESHOLDS["rhythm_peak_humor"],
        "SOCIAL": _s(raw, "social_energy") >= INDIVIDUAL_THRESHOLDS["rhythm_peak_social"],
        "DEEP": connection_depth >= INDIVIDUAL_THRESHOLDS["rhythm_peak_depth"],
        "TUNED_IN": _s(raw, "attentional_presence") >= INDIVIDUAL_THRESHOLDS["rhythm_peak_attention"],
        "RELAXED": _s(raw, "relaxed_presence") >= INDIVIDUAL_THRESHOLDS["rhythm_peak_relaxed"],
    }
    peak_order = ("DEEP", "PLAYFUL", "SOCIAL", "TUNED_IN", "RELAXED")
    peak = next((label for label in peak_order if peaks[label]), "RELAXED")

    display_tag = f"{q8_category}_{q5_category}" if q8_category != "STRUCTURED" or q5_category != "PRESSURED" else "PRESSURED_STRUCTURED"
    if q8_category != "STRUCTURED" and q5_category == "PRESSURED":
        display_tag = f"PRESSURED_{q8_category}"
    elif q5_category != "PRESSURED":
        display_tag = f"{q8_category}_{q5_category}"

    derived = {
        "metrics": {
            "social_energy": social_energy,
            "social_energy_label": _band(social_energy, INDIVIDUAL_THRESHOLDS["social_energy"], ("LOW", "LOW_MODERATE", "MODERATE", "HIGH", "VERY_HIGH")),
            "social_density": social_density,
            "social_density_label": _band(social_density, INDIVIDUAL_THRESHOLDS["social_density"], ("LOW", "MODERATE", "HIGH")),
            "social_selectivity": social_selectivity,
            "social_selectivity_label": _band(social_selectivity, INDIVIDUAL_THRESHOLDS["social_selectivity"], ("OPEN", "MODERATE", "SELECTIVE")),
            "connection_depth": connection_depth,
            "connection_depth_type": connection_depth_type,
            "humor_connection": humor_connection,
            "humor_connection_label": _band(humor_connection, INDIVIDUAL_THRESHOLDS["humor_connection"], ("LOW", "MODERATE", "HIGH", "VERY_HIGH")),
            "introspection": introspection,
            "introspection_label": _band(introspection, INDIVIDUAL_THRESHOLDS["introspection"], ("ACTION_ORIENTED", "MODERATE", "HIGHLY_INTERNAL")),
            "social_recovery": q9_category,
        },
        "D1": {"category": q2_category, "answer_paths": ["Q2"]},
        "D2": {"scores": connection_modes, "selected_modes": [name for name, _ in selected_modes], "selected_scores": {name: score for name, score in selected_modes}, "answer_paths": ["Q2", "Q6", "Q7", "Q10"]},
        "D3": {"category": q7_category, "answer_paths": ["Q7"]},
        "D4": {"opening": opening_map[q3_category], "warming": warming, "peak": peak, "recovery": q9_category, "features": {name: _s(raw, name) for name in ("social_energy", "social_density", "initial_openness", "warmup_speed", "energy_contribution", "social_replenishment")}, "answer_paths": ["Q1", "Q3", "Q4", "Q9"]},
        "D5": {"category": q6_category, "features": {name: _s(raw, name) for name in ("direct_expression", "processing_delay", "action_response", "context_sensitivity")}, "answer_paths": ["Q6", "Q10", "Q3"]},
        "D6": {"planning_style": q8_category, "current_phase": q5_category, "display_tag": display_tag, "answer_paths": ["Q8", "Q5"]},
        "D7": {"category": q9_category, "answer_paths": ["Q9", "Q1", "Q4"]},
        "D8": {"category": interaction_pace, "features": {name: _s(raw, name) for name in ("initial_openness", "warmup_speed", "processing_delay", "introspection", "action_orientation")}, "answer_paths": ["Q3", "Q6", "Q10"]},
        "D9": {"primary": primary_energy, "secondary": secondary_energy, "scores": energy_scores, "features": {name: _s(raw, name) for name in ("social_presence", "energy_contribution", "relaxed_presence", "humor_presence", "attentional_presence")}, "answer_paths": ["Q1", "Q4", "Q9", "Q10"]},
        "D10": {"category": q5_category, "answer_paths": ["Q5"]},
    }
    return derived
