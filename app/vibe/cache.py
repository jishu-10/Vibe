"""Canonical cache identity and invalidation helpers."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from app.vibe.config.v1_1_0 import engine_versions


def pair_cache_key(user_a_id: str, user_b_id: str, relationship_mode: str, profile_a: Mapping[str, Any], profile_b: Mapping[str, Any]) -> str:
    sorted_ids = sorted((user_a_id, user_b_id))
    profile_by_user = {user_a_id: profile_a, user_b_id: profile_b}
    versions = engine_versions()
    payload = {
        "sorted_user_ids": sorted_ids,
        "relationship_mode": relationship_mode,
        "user_a_profile_version": profile_by_user[sorted_ids[0]]["profile_version"],
        "user_b_profile_version": profile_by_user[sorted_ids[1]]["profile_version"],
        "questionnaire_version": versions["questionnaire"],
        "signal_model_version": versions["signal_model"],
        "dimension_model_version": versions["dimension_model"],
        "scoring_model_version": versions["scoring_model"],
        "narrative_prompt_version": versions["narrative_prompt"],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

