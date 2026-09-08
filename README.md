# Campus Chemistry - Vibe Engine V1

This repository implements the deterministic Campus Chemistry Vibe Engine contract from the attached zero-gap PDF.

The canonical implementation boundary is:

`Q1-Q10 answers -> static raw signals -> individual dimensions -> versioned profile -> explicit pair trigger -> D1-D10 pair analysis -> components/final internal score/classification -> evidence -> narrative renderer`

Pair analysis is only exposed at `POST /api/v1/vibe/pair/analyze`. Profile reads never calculate chemistry, and public pair responses do not expose internal scores, matrices, multipliers, or raw signal values.

## Key modules

- `app/vibe/config/v1_1_0.py`: versioned canonical mappings, matrices, weights, thresholds, tie-breaks, libraries, amendment `1.0`, and scoring model `1.2.0`.
- `app/vibe/questionnaire.py`, `signal_map.py`, `signals.py`: strict answer validation and static signal extraction.
- `app/vibe/dimensions.py`, `profile.py`: deterministic individual dimensions and profile facts.
- `app/vibe/pair/`: mode weights, matrices, continuous policies, aggregation, classification, evidence, and cache identity.
- `app/vibe/narrative.py`: evidence-bound narrative validation and deterministic fallback wording.
- `app/services/vibe_service.py`: versioned persistence, explicit pair execution, cache invalidation, and API boundary.
- `docs/vibe_engine_requirement_matrix.md`: the complete PDF/amendment requirement/test audit.
- The legacy similarity engine has been removed. Only the Vibe Engine routes and persistence models remain in the active application.

## API

- `POST /api/v1/vibe/profile/compute`
- `GET /api/v1/vibe/profile/{user_id}`
- `POST /api/v1/vibe/pair/analyze`
- `POST /api/v1/vibe/pair/approach`
- `POST /api/v1/vibe/profile/refresh`
- `GET /api/v1/vibe/engine/versions`

## Verification

Run:

```powershell
python -m pytest -p no:cacheprovider -q
```

The suite covers canonical mappings, validation, matrices, mode normalization, score/classification boundaries, symmetry, cache identity and invalidation, Wildcard/contrast/profile-confidence amendment fixtures, explicit pair triggering, authorization, LLM evidence/claim boundaries, public stripping, observability replay, and Vibe-only route isolation.
