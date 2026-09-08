from __future__ import annotations

from app.vibe.cache import pair_cache_key
from app.vibe.config.v1_1_0 import QUESTIONS, SIGNAL_MAP
from app.vibe.profile import build_partial_profile
from app.vibe.questionnaire import questionnaire_schema
from app.vibe.signal_map import map_answers_to_signals


def _answers() -> dict[str, str]:
    return {f"Q{i}": f"Q{i}_A" for i in range(1, 11)}


def test_question_bank_has_exactly_ten_questions_and_forty_option_ids() -> None:
    schema = questionnaire_schema()
    assert [item["question_id"] for item in schema] == [f"Q{i}" for i in range(1, 11)]
    assert sum(len(item["options"]) for item in schema) == 40
    assert set(SIGNAL_MAP) == {f"Q{i}" for i in range(1, 11)}
    assert all(set(mapping) == {f"Q{i}_A", f"Q{i}_B", f"Q{i}_C", f"Q{i}_D"} for i, mapping in enumerate(SIGNAL_MAP.values(), start=1))
    assert [question["id"] for question in QUESTIONS] == [f"Q{i}" for i in range(1, 11)]


def test_complete_answer_object_maps_every_question() -> None:
    mapped = map_answers_to_signals(_answers())
    assert set(mapped["question_categories"]) == {f"Q{i}" for i in range(1, 11)}
    assert set(mapped["per_question"]) == {f"Q{i}" for i in range(1, 11)}
    assert mapped["signal_model_version"] == "1.0"


def test_pair_cache_key_is_symmetric_and_mode_versioned() -> None:
    a = build_partial_profile("a", _answers())
    b = build_partial_profile("b", {**_answers(), "Q2": "Q2_C"})
    assert pair_cache_key("a", "b", "DATE", a, b) == pair_cache_key("b", "a", "DATE", b, a)
    assert pair_cache_key("a", "b", "DATE", a, b) != pair_cache_key("a", "b", "FRIEND", a, b)
    b_changed = build_partial_profile("b", {**_answers(), "Q2": "Q2_D"})
    assert pair_cache_key("a", "b", "DATE", a, b) != pair_cache_key("a", "b", "DATE", a, b_changed)

