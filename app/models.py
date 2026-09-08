from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

class VibeProfile(Base):
    """Current versioned deterministic profile for the Vibe Engine."""

    __tablename__ = "vibe_profiles"

    user_id = Column(String(64), ForeignKey("users.id"), primary_key=True)
    profile_version = Column(String(128), nullable=False)
    answers = Column(JSON, nullable=False)
    signals = Column(JSON, nullable=False)
    derived = Column(JSON, nullable=False)
    facts = Column(JSON, nullable=False)
    evidence = Column(JSON, nullable=False)
    confidence = Column(JSON, nullable=False)
    profile_narrative = Column(JSON, nullable=True)
    engine_versions = Column(JSON, nullable=False)
    config_hash = Column(String(128), nullable=False)
    generated_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    user = relationship("User", foreign_keys=[user_id])


class VibePairResult(Base):
    """Explicitly-triggered pair result and deterministic replay trace."""

    __tablename__ = "vibe_pair_results"

    id = Column(String(36), primary_key=True, default=new_uuid)
    sorted_user_a_id = Column(String(64), ForeignKey("users.id"), nullable=False)
    sorted_user_b_id = Column(String(64), ForeignKey("users.id"), nullable=False)
    request_user_a_id = Column(String(64), nullable=False)
    request_user_b_id = Column(String(64), nullable=False)
    relationship_mode = Column(String(16), nullable=False)
    cache_key = Column(String(128), unique=True, nullable=False)
    user_a_profile_version = Column(String(128), nullable=False)
    user_b_profile_version = Column(String(128), nullable=False)
    engine_versions = Column(JSON, nullable=False)
    deterministic_result = Column(JSON, nullable=False)
    public_response = Column(JSON, nullable=False)
    approach = Column(JSON, nullable=True)
    request_id = Column(String(36), nullable=True)
    cache_hit = Column(Boolean, nullable=False, default=False)
    spec_error_path = Column(String(256), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    sorted_user_a = relationship("User", foreign_keys=[sorted_user_a_id])
    sorted_user_b = relationship("User", foreign_keys=[sorted_user_b_id])
