import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def _create_source(client: AsyncClient, api_key: str, **overrides: object) -> dict:
    payload = {
        "source_key": "REVIEW_API_SOURCE",
        "title": "Review API Source",
        "publisher": "Publisher",
        "original_url": "https://example.com/review-api",
        "source_type": "official_statistics",
        "tier": "A",
        "refresh_interval_days": 90,
    }
    payload.update(overrides)
    response = await client.post("/api/v1/sources", json=payload, headers={"X-API-Key": api_key})
    assert response.status_code == 201, response.text
    return response.json()


async def _review_items_for(client: AsyncClient, source_id: str) -> list[dict]:
    response = await client.get("/api/v1/review-items", params={"entity_type": "source", "limit": 100})
    return [i for i in response.json()["items"] if i["entity_id"] == source_id]


async def test_list_review_items_empty_when_no_sources(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/v1/review-items")
    assert response.status_code == 200
    assert response.json()["items"] == []


async def test_creating_a_source_via_api_creates_two_review_items(
    api_client: AsyncClient, dev_api_key: str
) -> None:
    source = await _create_source(api_client, dev_api_key)
    items = await _review_items_for(api_client, source["id"])
    assert len(items) == 2
    assert {i["review_type"] for i in items} == {"rights_review", "content_review"}
    assert all(i["status"] == "open" for i in items)


async def test_decision_endpoint_requires_api_key(api_client: AsyncClient, dev_api_key: str) -> None:
    source = await _create_source(api_client, dev_api_key)
    items = await _review_items_for(api_client, source["id"])
    content_item = next(i for i in items if i["review_type"] == "content_review")

    response = await api_client.post(
        f"/api/v1/review-items/{content_item['id']}/decision", json={"status": "approved"}
    )
    assert response.status_code == 401

    response = await api_client.post(
        f"/api/v1/review-items/{content_item['id']}/decision",
        json={"status": "approved", "decision_reason": "ok"},
        headers={"X-API-Key": dev_api_key},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "approved"


async def test_decision_endpoint_rejects_rights_review_approval(
    api_client: AsyncClient, dev_api_key: str
) -> None:
    source = await _create_source(api_client, dev_api_key, source_key="RIGHTS_BYPASS_TEST")
    items = await _review_items_for(api_client, source["id"])
    rights_item = next(i for i in items if i["review_type"] == "rights_review")

    response = await api_client.post(
        f"/api/v1/review-items/{rights_item['id']}/decision",
        json={"status": "approved", "decision_reason": "approved"},
        headers={"X-API-Key": dev_api_key},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_failed"


async def test_rights_decision_endpoint_updates_review_item_and_source(
    api_client: AsyncClient, dev_api_key: str
) -> None:
    source = await _create_source(api_client, dev_api_key, source_key="RIGHTS_DECISION_TEST")
    items = await _review_items_for(api_client, source["id"])
    rights_item = next(i for i in items if i["review_type"] == "rights_review")

    response = await api_client.post(
        f"/api/v1/review-items/{rights_item['id']}/rights-decision",
        json={
            "rights_status": "reviewed_allowed",
            "access_policy": "short_evidence",
            "decision_reason": "publisher licence confirmed",
        },
        headers={"X-API-Key": dev_api_key},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["review_item"]["status"] == "approved"
    assert body["source"]["rights_status"] == "reviewed_allowed"
    assert body["source"]["access_policy"] == "short_evidence"


async def test_rights_decision_endpoint_rejects_invalid_combination(
    api_client: AsyncClient, dev_api_key: str
) -> None:
    source = await _create_source(api_client, dev_api_key, source_key="RIGHTS_INVALID_COMBO_TEST")
    items = await _review_items_for(api_client, source["id"])
    rights_item = next(i for i in items if i["review_type"] == "rights_review")

    response = await api_client.post(
        f"/api/v1/review-items/{rights_item['id']}/rights-decision",
        json={
            "rights_status": "blocked",
            "access_policy": "full_text_allowed",
            "decision_reason": "inconsistent",
        },
        headers={"X-API-Key": dev_api_key},
    )
    assert response.status_code == 422

    get_response = await api_client.get(f"/api/v1/sources/{source['id']}")
    assert get_response.json()["rights_status"] == "needs_review"
    assert get_response.json()["access_policy"] == "metadata_only"


async def test_rights_decision_endpoint_requires_api_key(api_client: AsyncClient, dev_api_key: str) -> None:
    source = await _create_source(api_client, dev_api_key, source_key="RIGHTS_AUTH_TEST")
    items = await _review_items_for(api_client, source["id"])
    rights_item = next(i for i in items if i["review_type"] == "rights_review")

    response = await api_client.post(
        f"/api/v1/review-items/{rights_item['id']}/rights-decision",
        json={"rights_status": "reviewed_allowed", "access_policy": "short_evidence", "decision_reason": "x"},
    )
    assert response.status_code == 401


async def test_rights_decision_endpoint_rejects_blank_decision_reason(
    api_client: AsyncClient, dev_api_key: str
) -> None:
    source = await _create_source(api_client, dev_api_key, source_key="RIGHTS_BLANK_REASON_TEST")
    items = await _review_items_for(api_client, source["id"])
    rights_item = next(i for i in items if i["review_type"] == "rights_review")

    response = await api_client.post(
        f"/api/v1/review-items/{rights_item['id']}/rights-decision",
        json={
            "rights_status": "reviewed_allowed",
            "access_policy": "short_evidence",
            "decision_reason": "   ",
        },
        headers={"X-API-Key": dev_api_key},
    )
    assert response.status_code == 422

    get_response = await api_client.get(f"/api/v1/sources/{source['id']}")
    assert get_response.json()["rights_status"] == "needs_review"


async def test_rights_decision_blocked_outcome_auto_blocks_source(
    api_client: AsyncClient, dev_api_key: str
) -> None:
    source = await _create_source(api_client, dev_api_key, source_key="RIGHTS_AUTO_BLOCK_TEST")
    items = await _review_items_for(api_client, source["id"])
    rights_item = next(i for i in items if i["review_type"] == "rights_review")

    response = await api_client.post(
        f"/api/v1/review-items/{rights_item['id']}/rights-decision",
        json={
            "rights_status": "blocked",
            "access_policy": "blocked",
            "decision_reason": "publisher revoked permission",
        },
        headers={"X-API-Key": dev_api_key},
    )
    assert response.status_code == 200, response.text
    assert response.json()["source"]["status"] == "blocked"

    get_response = await api_client.get(f"/api/v1/sources/{source['id']}")
    assert get_response.json()["status"] == "blocked"


async def test_list_review_items_filter_by_status(api_client: AsyncClient, dev_api_key: str) -> None:
    source = await _create_source(api_client, dev_api_key)
    items = await _review_items_for(api_client, source["id"])
    assert len(items) == 2

    response = await api_client.get("/api/v1/review-items", params={"status": "open"})
    body = response.json()
    assert body["total"] == 2
    assert all(item["status"] == "open" for item in body["items"])
