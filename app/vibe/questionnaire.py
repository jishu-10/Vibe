"""Canonical Q1-Q10 questionnaire and strict answer validation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.vibe.config.v1_1_0 import QUESTIONS
from app.vibe.contracts import AnswerValidationError

QUESTION_IDS = tuple(question["id"] for question in QUESTIONS)
QUESTION_OPTIONS = {
    question["id"]: tuple(question["options"].keys()) for question in QUESTIONS
}
OPTION_TO_QUESTION = {
    option_id: question_id
    for question_id, option_ids in QUESTION_OPTIONS.items()
    for option_id in option_ids
}


def questionnaire_schema() -> list[dict[str, Any]]:
    return [
        {
            "question_id": question["id"],
            "title": question["title"],
            "text": question["text"],
            "options": [
                {"option_id": option_id, "text": text}
                for option_id, text in question["options"].items()
            ],
        }
        for question in QUESTIONS
    ]


def validate_answers(answers: Mapping[str, str]) -> dict[str, str]:
    if not isinstance(answers, Mapping):
        raise AnswerValidationError("INVALID_INPUT", "answers", "Answers must be an object.")

    unknown_questions = sorted(set(answers) - set(QUESTION_IDS))
    if unknown_questions:
        raise AnswerValidationError(
            "INVALID_ANSWER_CODE",
            "answers",
            f"Unknown question code(s): {unknown_questions}.",
            400,
        )

    missing = [question_id for question_id in QUESTION_IDS if question_id not in answers]
    if missing:
        raise AnswerValidationError(
            "INCOMPLETE_ASSESSMENT",
            "answers",
            f"Missing answer(s): {missing}.",
            422,
        )

    validated: dict[str, str] = {}
    for question_id in QUESTION_IDS:
        option_id = answers[question_id]
        if not isinstance(option_id, str) or not option_id:
            raise AnswerValidationError(
                "INVALID_ANSWER_CODE",
                f"answers.{question_id}",
                "Answer must be a non-empty option code.",
                400,
            )
        if option_id not in QUESTION_OPTIONS[question_id]:
            raise AnswerValidationError(
                "INVALID_ANSWER_CODE",
                f"answers.{question_id}",
                f"Unknown option code {option_id!r} for {question_id}.",
                400,
            )
        validated[question_id] = option_id
    return validated

