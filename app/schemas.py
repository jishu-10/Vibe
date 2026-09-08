from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class VibeProfileComputeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(min_length=1, max_length=64)
    answers: dict[str, str]
    profile_version: str | None = Field(default=None, max_length=128)
    idempotency_key: str | None = Field(default=None, max_length=128)


class VibeProfileRefreshRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(min_length=1, max_length=64)


class VibeProfileRead(BaseModel):
    user_id: str
    profile_version: str
    facts: dict[str, Any]
    evidence: list[dict[str, Any]]
    confidence: dict[str, Any]
    profile_narrative: dict[str, Any] | None
    engine_versions: dict[str, str]


class VibePairAnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_a_id: str = Field(min_length=1, max_length=64)
    user_b_id: str = Field(min_length=1, max_length=64)
    relationship_mode: str


class VibeApproachRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pair_result_id: str
    relationship_mode: str


class VibePairPublicRead(BaseModel):
    pair_result_id: str
    relationship_mode: str
    chemistry: str
    why_you_two: dict[str, Any]
    confidence: str


class VibeApproachRead(BaseModel):
    pair_result_id: str
    relationship_mode: str
    approach: dict[str, Any]


class VibeEngineVersionsRead(BaseModel):
    versions: dict[str, str]
    config_hash: str
