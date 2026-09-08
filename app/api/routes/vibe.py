from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_vibe_service_authorization
from app.schemas import (
    VibeApproachRead,
    VibeApproachRequest,
    VibeEngineVersionsRead,
    VibePairAnalyzeRequest,
    VibePairPublicRead,
    VibeProfileComputeRequest,
    VibeProfileRefreshRequest,
    VibeProfileRead,
)
from app.services.vibe_service import analyze_pair_on_demand, compute_profile, generate_approach, get_profile, public_profile, refresh_profile
from app.vibe.config.v1_1_0 import engine_versions
from app.vibe.contracts import VibeError
from app.vibe.pair.modes import config_hash

router = APIRouter(prefix="/vibe", tags=["vibe-engine"], dependencies=[Depends(require_vibe_service_authorization)])


def _raise(error: VibeError) -> None:
    raise HTTPException(status_code=error.http_status, detail={"code": error.code, "path": error.path, "message": error.detail})


@router.post("/profile/compute", response_model=VibeProfileRead, status_code=201)
def compute_vibe_profile(payload: VibeProfileComputeRequest, db: Session = Depends(get_db)) -> dict:
    try:
        profile = compute_profile(db, payload.user_id, payload.answers, expected_profile_version=payload.profile_version)
    except VibeError as error:
        _raise(error)
    return public_profile(profile)


@router.get("/profile/{user_id}", response_model=VibeProfileRead)
def read_vibe_profile(user_id: str, db: Session = Depends(get_db)) -> dict:
    try:
        profile = get_profile(db, user_id)
    except VibeError as error:
        _raise(error)
    return public_profile(profile)


@router.post("/pair/analyze", response_model=VibePairPublicRead, status_code=201)
def analyze_vibe_pair(payload: VibePairAnalyzeRequest, db: Session = Depends(get_db)) -> dict:
    try:
        _, _, public = analyze_pair_on_demand(db, payload.user_a_id, payload.user_b_id, payload.relationship_mode)
    except VibeError as error:
        _raise(error)
    return public


@router.post("/pair/approach", response_model=VibeApproachRead, status_code=201)
def approach_vibe_pair(payload: VibeApproachRequest, db: Session = Depends(get_db)) -> dict:
    try:
        return generate_approach(db, payload.pair_result_id, payload.relationship_mode)
    except VibeError as error:
        _raise(error)


@router.post("/profile/refresh", response_model=VibeProfileRead, status_code=201)
def refresh_vibe_profile(payload: VibeProfileRefreshRequest, db: Session = Depends(get_db)) -> dict:
    try:
        return public_profile(refresh_profile(db, payload.user_id))
    except VibeError as error:
        _raise(error)


@router.get("/engine/versions", response_model=VibeEngineVersionsRead)
def read_vibe_versions() -> dict:
    return {"versions": engine_versions(), "config_hash": config_hash()}
