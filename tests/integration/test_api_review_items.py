import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def _create_source_with_review_items(client: AsyncClient, api_key: str) -> str:
    response = await client.post(
        "/api/v1/sources",
        json={
            "source_key": "REVIEW_API_SOURCE",
            "title": "Review API Source",
            "publisher": "Publisher",
            "original_url": "https://example.com/review-api",
            "source_type": "official_statistics",
            "tier": "A",
            "refresh_interval_days": 90,
        },
        headers={"X-API-Key": api_key},
    )
    return response.json()["id"]


async def test_list_review_items_empty_when_no_sources(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/v1/review-items")
    assert response.status_code == 200
    assert response.json()["items"] == []


async def test_decision_endpoint_requires_api_key(api_client: AsyncClient, dev_api_key: str) -> None:
    from de_ai_kb.services.review import ReviewService

    # Creating a source via the API does not itself create review items in
    # this release (that happens via the seed-import path); create one
    # directly through the service against the same test DB for this test.
    source_id = await _create_source_with_review_items(api_client, dev_api_key)

    from de_ai_kb.core.config import get_settings
    from de_ai_kb.db.session import get_sessionmaker

    session_factory = get_sessionmaker(get_settings().test_database_url)
    async with session_factory() as session:
        import uuid

        service = ReviewService(session)
        items = await service.create_standard_source_review_items(
            source_id=uuid.UUID(source_id), actor_id="test"
        )
        await session.commit()
        item_id = str(items[0].id)

    response = await api_client.post(f"/api/v1/review-items/{item_id}/decision", json={"status": "approved"})
    assert response.status_code == 401

    response = await api_client.post(
        f"/api/v1/review-items/{item_id}/decision",
        json={"status": "approved", "decision_reason": "ok"},
        headers={"X-API-Key": dev_api_key},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "approved"


async def test_list_review_items_filter_by_status(api_client: AsyncClient, dev_api_key: str) -> None:
    from de_ai_kb.core.config import get_settings
    from de_ai_kb.db.session import get_sessionmaker
    from de_ai_kb.services.review import ReviewService

    source_id = await _create_source_with_review_items(api_client, dev_api_key)

    session_factory = get_sessionmaker(get_settings().test_database_url)
    async with session_factory() as session:
        import uuid

        service = ReviewService(session)
        await service.create_standard_source_review_items(
            source_id=uuid.UUID(source_id), actor_id="test"
        )
        await session.commit()

    response = await api_client.get("/api/v1/review-items", params={"status": "open"})
    body = response.json()
    assert body["total"] == 2
    assert all(item["status"] == "open" for item in body["items"])
