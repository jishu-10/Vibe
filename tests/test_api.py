from __future__ import annotations

from fastapi.testclient import TestClient

from app.api import deps
from app.core.config import Settings
from app.main import app
from app.services.vibe_service import analyze_pair_on_demand


def _complete_answers() -> dict[str, str]:
    return {f"Q{i}": f"Q{i}_A" for i in range(1, 11)}


def test_vibe_versions_are_public_without_internal_scores(client: TestClient) -> None:
    response = client.get("/v1/vibe/engine/versions")
    assert response.status_code == 200
    assert response.json()["versions"] == {
        "questionnaire": "1.0",
        "signal_model": "1.0",
        "dimension_model": "1.0",
        "scoring_model": "1.2.0",
        "narrative_prompt": "1.0",
        "completion_amendment": "1.0",
    }
    assert "final_score_internal" not in response.json()


def test_incomplete_profile_fails_closed(client: TestClient) -> None:
    response = client.post(
        "/api/v1/vibe/profile/compute",
        json={"user_id": "api_a", "answers": {"Q1": "Q1_A"}},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "INCOMPLETE_ASSESSMENT"


def test_unknown_option_fails_closed(client: TestClient) -> None:
    answers = _complete_answers()
    answers["Q1"] = "Q1_Z"
    response = client.post(
        "/api/v1/vibe/profile/compute",
        json={"user_id": "api_a", "answers": answers},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_ANSWER_CODE"


def test_profile_wildcard_and_contrast_are_materialized(client: TestClient) -> None:
    response = client.post(
        "/api/v1/vibe/profile/compute",
        json={"user_id": "api_a", "answers": _complete_answers()},
    )
    assert response.status_code == 201
    body = response.json()
    assert "how_you_are_with_different_people" in body["facts"]
    assert len(body["facts"]["how_you_are_with_different_people"]) == 4


def test_pair_requires_stored_profiles_and_explicit_valid_mode(client: TestClient) -> None:
    response = client.post(
        "/api/v1/vibe/pair/analyze",
        json={"user_a_id": "missing_a", "user_b_id": "missing_b", "relationship_mode": "DATE"},
    )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "PROFILE_NOT_FOUND"

    invalid = client.post(
        "/api/v1/vibe/pair/analyze",
        json={"user_a_id": "missing_a", "user_b_id": "missing_b", "relationship_mode": "ROOMMATE"},
    )
    assert invalid.status_code == 422
    assert invalid.json()["detail"]["code"] == "INVALID_MODE"


def test_explicit_pair_trigger_and_optional_approach_are_publicly_bounded(client: TestClient) -> None:
    for user_id, answers in (("api_a", _complete_answers()), ("api_b", {**_complete_answers(), "Q4": "Q4_B"})):
        response = client.post("/v1/vibe/profile/compute", json={"user_id": user_id, "answers": answers})
        assert response.status_code == 201
    profile = client.get("/v1/vibe/profile/api_a")
    assert profile.status_code == 200
    assert "chemistry" not in profile.json()
    assert "contrast_score" not in str(profile.json())
    assert "final_score_internal" not in str(profile.json())
    pair = client.post("/v1/vibe/pair/analyze", json={"user_a_id": "api_a", "user_b_id": "api_b", "relationship_mode": "DATE"})
    assert pair.status_code == 201
    body = pair.json()
    assert set(body) == {"pair_result_id", "relationship_mode", "chemistry", "why_you_two", "confidence"}
    assert "final_score_internal" not in str(body)
    approach = client.post("/v1/vibe/pair/approach", json={"pair_result_id": body["pair_result_id"], "relationship_mode": "DATE"})
    assert approach.status_code == 201
    assert set(approach.json()["approach"]) == {"tone", "opener_type", "works", "avoid", "better_opener"}


def test_similarity_routes_are_removed() -> None:
    def route_paths(routes):
        for route in routes:
            path = getattr(route, "path", None)
            if path is not None:
                yield path
            nested = getattr(route, "routes", None)
            if nested is not None:
                yield from route_paths(nested)
            included = getattr(route, "original_router", None)
            if included is not None:
                yield from route_paths(included.routes)

    paths = set(route_paths(app.routes))
    assert not any("/similarity" in path for path in paths)


def test_profile_version_conflict_is_optimistic_and_preserves_current_data(client: TestClient) -> None:
    initial = client.post("/v1/vibe/profile/compute", json={"user_id": "versioned", "answers": _complete_answers()})
    assert initial.status_code == 201
    old_version = initial.json()["profile_version"]
    changed_answers = {**_complete_answers(), "Q4": "Q4_B"}

    matching = client.post(
        "/v1/vibe/profile/compute",
        json={"user_id": "versioned", "answers": changed_answers, "profile_version": old_version},
    )
    assert matching.status_code == 201
    new_version = matching.json()["profile_version"]
    assert new_version != old_version

    stale = client.post(
        "/v1/vibe/profile/compute",
        json={"user_id": "versioned", "answers": {**_complete_answers(), "Q4": "Q4_C"}, "profile_version": old_version},
    )
    assert stale.status_code == 409
    assert stale.json()["detail"]["code"] == "PROFILE_VERSION_CONFLICT"
    current = client.get("/v1/vibe/profile/versioned")
    assert current.status_code == 200
    assert current.json()["profile_version"] == new_version


def test_unauthorized_profile_and_pair_operations_fail_before_data_access(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(deps, "get_settings", lambda: Settings(environment="production", vibe_service_token="secret"))
    profile = client.get("/v1/vibe/profile/unauthorized")
    pair = client.post("/v1/vibe/pair/analyze", json={"user_a_id": "a", "user_b_id": "b", "relationship_mode": "DATE"})
    assert profile.status_code == 403
    assert pair.status_code == 403
