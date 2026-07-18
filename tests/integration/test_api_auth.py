import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

_VALID_PAYLOAD = {
    "source_key": "AUTH_TEST_SOURCE",
    "title": "Auth Test Source",
    "publisher": "Publisher",
    "original_url": "https://example.com/auth-test",
    "source_type": "official_statistics",
    "tier": "A",
    "refresh_interval_days": 90,
}


async def test_get_sources_does_not_require_api_key(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/v1/sources")
    assert response.status_code == 200


async def test_post_source_without_api_key_is_rejected(api_client: AsyncClient) -> None:
    response = await api_client.post("/api/v1/sources", json=_VALID_PAYLOAD)
    assert response.status_code == 401


async def test_post_source_with_wrong_api_key_is_rejected(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/api/v1/sources", json=_VALID_PAYLOAD, headers={"X-API-Key": "wrong-key"}
    )
    assert response.status_code == 401


async def test_post_source_with_correct_api_key_succeeds(
    api_client: AsyncClient, dev_api_key: str
) -> None:
    response = await api_client.post(
        "/api/v1/sources", json=_VALID_PAYLOAD, headers={"X-API-Key": dev_api_key}
    )
    assert response.status_code == 201
    assert response.json()["source_key"] == "AUTH_TEST_SOURCE"


async def test_patch_source_without_api_key_is_rejected(
    api_client: AsyncClient, dev_api_key: str
) -> None:
    create_resp = await api_client.post(
        "/api/v1/sources", json=_VALID_PAYLOAD, headers={"X-API-Key": dev_api_key}
    )
    source_id = create_resp.json()["id"]
    response = await api_client.patch(f"/api/v1/sources/{source_id}", json={"title": "New title"})
    assert response.status_code == 401
