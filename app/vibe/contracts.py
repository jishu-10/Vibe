"""Typed contracts and fail-closed errors for the Vibe Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping


class RelationshipMode(StrEnum):
    DATE = "DATE"
    FRIEND = "FRIEND"
    HANGOUT = "HANGOUT"


class Chemistry(StrEnum):
    NATURAL_CLICK = "NATURAL_CLICK"
    INTERESTING_CHEMISTRY = "INTERESTING_CHEMISTRY"
    POTENTIAL_FRICTION = "POTENTIAL_FRICTION"


class Relationship(StrEnum):
    ALIGNMENT = "ALIGNMENT"
    COMPLEMENTARITY = "COMPLEMENTARITY"
    NEUTRAL = "NEUTRAL"
    SOFT_FRICTION = "SOFT_FRICTION"
    HARD_FRICTION = "HARD_FRICTION"


class ConfidenceLabel(StrEnum):
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"
    VERY_STRONG = "VERY_STRONG"


class NarrativePermission(StrEnum):
    ALLOWED = "allowed"
    INTERNAL_ONLY = "internal_only"


@dataclass
class VibeError(Exception):
    code: str
    path: str
    detail: str
    http_status: int = 500

    def __str__(self) -> str:
        return f"{self.code} at {self.path}: {self.detail}"


class SpecificationGap(VibeError):
    def __init__(self, path: str, detail: str):
        super().__init__("SPEC_CONTRACT_ERROR", path, detail, 500)


class ConfigurationError(VibeError):
    def __init__(self, path: str, detail: str):
        super().__init__("ENGINE_CONFIG_INVALID", path, detail, 500)


class AnswerValidationError(VibeError):
    def __init__(self, code: str, path: str, detail: str, http_status: int = 422):
        super().__init__(code, path, detail, http_status)


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    dimension: str
    kind: str
    interaction_score: float
    difference_score: float
    confidence: float
    insight_priority: float
    answer_paths: tuple[str, ...]
    statement_key: str
    signal_paths_a: tuple[str, ...] = ()
    signal_paths_b: tuple[str, ...] = ()
    rule: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "dimension": self.dimension,
            "kind": self.kind,
            "interaction_score": self.interaction_score,
            "difference_score": self.difference_score,
            "confidence": self.confidence,
            "insight_priority": self.insight_priority,
            "answer_paths": list(self.answer_paths),
            "statement_key": self.statement_key,
            "signal_paths_a": list(self.signal_paths_a),
            "signal_paths_b": list(self.signal_paths_b),
            "rule": self.rule,
        }


@dataclass(frozen=True)
class DimensionResult:
    dimension: str
    relationship: Relationship
    interaction_score: float
    difference_score: float
    confidence: float
    evidence: tuple[EvidenceItem, ...] = ()
    narrative_permission: NarrativePermission = NarrativePermission.ALLOWED
    trace: Mapping[str, Any] = field(default_factory=dict)
    computed_negative_score: float | None = None
    friction_score: float | None = None
    is_hard_friction: bool | None = None
    high_salience: bool | None = None

    def as_dict(self) -> dict[str, Any]:
        result = {
            "dimension": self.dimension,
            "relationship": self.relationship.value,
            "interaction_score": self.interaction_score,
            "difference_score": self.difference_score,
            "confidence": self.confidence,
            "evidence": [item.as_dict() for item in self.evidence],
            "narrative_permission": self.narrative_permission.value,
            "trace": dict(self.trace),
        }
        if self.computed_negative_score is not None:
            result["computed_negative_score"] = self.computed_negative_score
        if self.friction_score is not None:
            result["friction_score"] = self.friction_score
        if self.is_hard_friction is not None:
            result["is_hard_friction"] = self.is_hard_friction
        if self.high_salience is not None:
            result["high_salience"] = self.high_salience
        return result


def require_mapping(value: Any, *, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AnswerValidationError("INVALID_INPUT", path, "Expected an object.")
    return value


def ensure_relationship_mode(mode: str | RelationshipMode) -> RelationshipMode:
    try:
        return mode if isinstance(mode, RelationshipMode) else RelationshipMode(mode)
    except ValueError as exc:
        raise AnswerValidationError(
            "INVALID_MODE", "relationship_mode", "Mode must be DATE, FRIEND, or HANGOUT.", 422
        ) from exc
