"""Static answer -> raw-signal mapping. No inference is performed here."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.vibe.config.v1_1_0 import CONTINUOUS_SIGNAL_NAMES, SIGNAL_MAP, SIGNAL_MODEL_VERSION
from app.vibe.contracts import ConfigurationError
from app.vibe.pair.modes import validate_configuration
from app.vibe.questionnaire import validate_answers
from app.vibe.signals import merge_signal_values, validate_raw_signal_representation


def map_answers_to_signals(answers: Mapping[str, str]) -> dict[str, Any]:
    validate_configuration()
    validated = validate_answers(answers)
    question_categories: dict[str, str] = {}
    per_question: dict[str, dict[str, Any]] = {}
    for question_id, option_id in validated.items():
        question_map = SIGNAL_MAP.get(question_id)
        if question_map is None or option_id not in question_map:
            raise ConfigurationError(
                f"signal_map.{question_id}.{option_id}",
                "No canonical mapping exists for a validated answer.",
            )
        mapped = question_map[option_id]
        category = mapped.get("category")
        if not isinstance(category, str) or not category:
            raise ConfigurationError(
                f"signal_map.{question_id}.{option_id}.category",
                "Mapped category is missing or invalid.",
            )
        question_categories[question_id] = category
        per_question[question_id] = dict(mapped["signals"])

    signals = merge_signal_values(per_question)
    # The canonical stored continuous representation is complete.  A zero here
    # means that no selected answer emitted that coordinate; it is not a
    # runtime repair of malformed persisted data.
    for signal in CONTINUOUS_SIGNAL_NAMES:
        signals.setdefault(signal, 0.0)
    representation = {
        "signal_model_version": SIGNAL_MODEL_VERSION,
        "signals": signals,
        "question_categories": question_categories,
        "per_question": per_question,
    }
    validate_raw_signal_representation(representation)
    return representation
