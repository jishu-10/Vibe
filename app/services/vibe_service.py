"""Application persistence boundary for the canonical Vibe Engine."""

from __future__ import annotations

import json
import uuid
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.models import User, VibePairResult, VibeProfile
from app.vibe.config.v1_1_0 import engine_versions
from app.vibe.contracts import VibeError, ensure_relationship_mode
from app.vibe.narrative import render_approach, render_pair_fallback
from app.vibe.pair.engine import analyze_pair, public_pair_result
from app.vibe.pair.modes import config_hash
from app.vibe.cache import pair_cache_key
from app.vibe.profile import build_profile, profile_version


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_user(db: Session, user_id: str) -> User:
    user = db.get(User, user_id)
    if user is None:
        user = User(id=user_id)
        db.add(user)
        db.flush()
    return user


def _profile_to_dict(row: VibeProfile) -> dict[str, Any]:
    return {
        "user_id": row.user_id,
        "profile_version": row.profile_version,
        "answers": row.answers,
        "signals": row.signals,
        "derived": row.derived,
        "facts": row.facts,
        "evidence": row.evidence,
        "confidence": row.confidence,
        "profile_narrative": row.profile_narrative,
        "engine_versions": row.engine_versions,
        "config_hash": row.config_hash,
    }


def public_profile(profile: Mapping[str, Any]) -> dict[str, Any]:
    derived = profile["derived"]
    contrasts = [
        {
            "prototype": item["prototype"],
            "primary_dimension": item.get("primary_dimension"),
            "evidence_dimensions": [evidence["dimension"] for evidence in item.get("evidence", [])],
            "bounded": bool(item.get("omission_threshold")),
        }
        for item in profile["facts"]["how_you_are_with_different_people"]
    ]
    wildcard = profile["facts"].get("wildcard")
    facts = {
        "your_vibe": profile["facts"]["your_vibe"],
        "social_rhythm": {key: derived["D4"][key] for key in ("opening", "warming", "peak", "recovery")},
        "connection_style": {"selected_modes": derived["D2"]["selected_modes"]},
        "energy_signature": {"primary": derived["D9"]["primary"], "secondary": derived["D9"]["secondary"]},
        "what_pulls_you_in": profile["facts"]["what_pulls_you_in"],
        "what_drains_you": profile["facts"]["what_drains_you"],
        "current_phase": {"category": derived["D10"]["category"]},
        "how_you_are_with_different_people": contrasts,
        "wildcard": {"archetype": wildcard["archetype"]} if wildcard else None,
    }
    evidence = [
        {"evidence_id": item["evidence_id"], "dimension": item["dimension"], "answer_paths": item["answer_paths"]}
        for item in profile["evidence"]
    ]
    return {
        "user_id": profile["user_id"],
        "profile_version": profile["profile_version"],
        "facts": facts,
        "evidence": evidence,
        "confidence": profile["confidence"],
        "profile_narrative": profile.get("profile_narrative"),
        "engine_versions": profile["engine_versions"],
    }


def _profile_update_values(profile: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "profile_version": profile["profile_version"],
        "answers": profile["answers"],
        "signals": profile["signals"],
        "derived": profile["derived"],
        "facts": profile["facts"],
        "evidence": profile["evidence"],
        "confidence": profile["confidence"],
        "profile_narrative": profile.get("profile_narrative"),
        "engine_versions": profile["engine_versions"],
        "config_hash": profile["config_hash"],
        "generated_at": _now(),
    }


def _profile_version_conflict(user_id: str, expected: str | None, current: str | None) -> VibeError:
    return VibeError(
        "PROFILE_VERSION_CONFLICT",
        f"profile.{user_id}.profile_version",
        f"Expected profile version {expected!r}, but the stored profile is {current!r}.",
        409,
    )


def compute_profile(
    db: Session,
    user_id: str,
    answers: Mapping[str, str],
    *,
    expected_profile_version: str | None = None,
) -> dict[str, Any]:
    _ensure_user(db, user_id)
    existing = db.get(VibeProfile, user_id)
    if existing is not None and expected_profile_version is not None and existing.profile_version != expected_profile_version:
        raise _profile_version_conflict(user_id, expected_profile_version, existing.profile_version)
    if existing is not None and existing.profile_version == profile_version(answers) and existing.engine_versions == engine_versions() and existing.config_hash == config_hash():
        return _profile_to_dict(existing)
    profile = build_profile(user_id, answers)
    values = _profile_update_values(profile)
    if existing is None:
        existing = VibeProfile(user_id=user_id)
        db.add(existing)
        for key, value in values.items():
            setattr(existing, key, value)
    elif expected_profile_version is not None:
        result = db.execute(
            update(VibeProfile)
            .where(VibeProfile.user_id == user_id, VibeProfile.profile_version == expected_profile_version)
            .values(**values)
        )
        if result.rowcount != 1:
            db.rollback()
            current = db.get(VibeProfile, user_id)
            raise _profile_version_conflict(user_id, expected_profile_version, current.profile_version if current else None)
    else:
        for key, value in values.items():
            setattr(existing, key, value)
    db.execute(delete(VibePairResult).where((VibePairResult.sorted_user_a_id == user_id) | (VibePairResult.sorted_user_b_id == user_id)))
    db.commit()
    return profile


def get_profile(db: Session, user_id: str) -> dict[str, Any]:
    row = db.get(VibeProfile, user_id)
    if row is None:
        raise VibeError("PROFILE_NOT_FOUND", f"profile.{user_id}", "Profile does not exist.", 404)
    if row.engine_versions != engine_versions() or row.config_hash != config_hash():
        return compute_profile(db, user_id, row.answers)
    return _profile_to_dict(row)


def refresh_profile(db: Session, user_id: str) -> dict[str, Any]:
    current = get_profile(db, user_id)
    return compute_profile(db, user_id, current["answers"])


def analyze_pair_on_demand(db: Session, user_a_id: str, user_b_id: str, mode: str) -> tuple[str, dict[str, Any], dict[str, Any]]:
    selected_mode = ensure_relationship_mode(mode).value
    profile_a = get_profile(db, user_a_id)
    profile_b = get_profile(db, user_b_id)
    cache_key = pair_cache_key(user_a_id, user_b_id, selected_mode, profile_a, profile_b)
    cached = db.scalar(select(VibePairResult).where(VibePairResult.cache_key == cache_key))
    if cached is not None:
        if cached.engine_versions == engine_versions() and cached.deterministic_result.get("config_hash") == config_hash():
            replay = dict(cached.deterministic_result)
            replay["observability"] = {"request_id": str(uuid.uuid4()), "cache_hit": True, "spec_error_path": cached.spec_error_path, "stored_request_id": cached.request_id}
            return cached.id, replay, cached.public_response
        db.delete(cached)
        db.flush()
    result = analyze_pair(profile_a, profile_b, selected_mode)
    pair_result_id = str(uuid.uuid4())
    request_id = str(uuid.uuid4())
    narrative = render_pair_fallback(result)
    public = public_pair_result(pair_result_id, result, narrative)
    sorted_a, sorted_b = sorted((user_a_id, user_b_id))
    row = VibePairResult(
        id=pair_result_id,
        sorted_user_a_id=sorted_a,
        sorted_user_b_id=sorted_b,
        request_user_a_id=user_a_id,
        request_user_b_id=user_b_id,
        relationship_mode=result["relationship_mode"],
        cache_key=cache_key,
        user_a_profile_version=profile_a["profile_version"],
        user_b_profile_version=profile_b["profile_version"],
        engine_versions=result["engine_versions"],
        deterministic_result=result,
        public_response=public,
        request_id=request_id,
        cache_hit=False,
        spec_error_path=result.get("spec_error_path"),
        created_at=_now(),
    )
    db.add(row)
    db.commit()
    returned = dict(result)
    returned["observability"] = {"request_id": request_id, "cache_hit": False, "spec_error_path": result.get("spec_error_path"), "stored_request_id": request_id}
    return pair_result_id, returned, public


def generate_approach(db: Session, pair_result_id: str, mode: str) -> dict[str, Any]:
    row = db.get(VibePairResult, pair_result_id)
    if row is None:
        raise VibeError("PAIR_RESULT_NOT_FOUND", f"pair_result.{pair_result_id}", "Pair result does not exist.", 404)
    if row.relationship_mode != mode:
        raise VibeError("INVALID_MODE", "relationship_mode", "Approach mode does not match the pair result.", 422)
    approach = render_approach(row.deterministic_result)
    row.approach = approach
    db.commit()
    return {"pair_result_id": row.id, "relationship_mode": row.relationship_mode, "approach": approach}


def invalidate_all_pairs(db: Session) -> None:
    db.execute(delete(VibePairResult))
    db.commit()
