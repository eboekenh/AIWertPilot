import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def _create_source(client: AsyncClient, api_key: str, **overrides: object) -> dict:
    payload = {
        "source_key": "API_SOURCE",
        "title": "API Source",
        "publisher": "Publisher A",
        "original_url": "https://example.com/api-source",
        "source_type": "official_statistics",
        "tier": "A",
        "topic_tags": ["adoption"],
        "refresh_interval_days": 90,
    }
    payload.update(overrides)
    response = await client.post("/api/v1/sources", json=payload, headers={"X-API-Key": api_key})
    assert response.status_code == 201, response.text
    return response.json()


async def test_create_and_get_source(api_client: AsyncClient, dev_api_key: str) -> None:
    created = await _create_source(api_client, dev_api_key)
    response = await api_client.get(f"/api/v1/sources/{created['id']}")
    assert response.status_code == 200
    assert response.json()["source_key"] == "API_SOURCE"


async def test_get_nonexistent_source_returns_404(api_client: AsyncClient) -> None:
    import uuid

    response = await api_client.get(f"/api/v1/sources/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


async def test_duplicate_source_key_returns_409(api_client: AsyncClient, dev_api_key: str) -> None:
    await _create_source(api_client, dev_api_key)
    response = await api_client.post(
        "/api/v1/sources",
        json={
            "source_key": "API_SOURCE",
            "title": "Different title",
            "publisher": "Publisher B",
            "original_url": "https://example.com/other",
            "source_type": "official_statistics",
            "tier": "A",
            "refresh_interval_days": 90,
        },
        headers={"X-API-Key": dev_api_key},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "duplicate_source"


async def test_list_pagination(api_client: AsyncClient, dev_api_key: str) -> None:
    for i in range(5):
        await _create_source(
            api_client,
            dev_api_key,
            source_key=f"PAGE_SOURCE_{i}",
            original_url=f"https://example.com/page-{i}",
        )
    response = await api_client.get("/api/v1/sources", params={"limit": 2, "offset": 0})
    body = response.json()
    assert body["total"] == 5
    assert len(body["items"]) == 2
    assert body["limit"] == 2
    assert body["offset"] == 0


async def test_list_filter_by_tier_and_publisher(api_client: AsyncClient, dev_api_key: str) -> None:
    await _create_source(api_client, dev_api_key, source_key="TIER_A", tier="A", publisher="Destatis")
    await _create_source(
        api_client,
        dev_api_key,
        source_key="TIER_C",
        tier="C",
        publisher="Bitkom",
        original_url="https://example.com/tier-c",
    )
    response = await api_client.get("/api/v1/sources", params={"tier": "A"})
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["source_key"] == "TIER_A"

    response = await api_client.get("/api/v1/sources", params={"publisher": "Bit"})
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["source_key"] == "TIER_C"


async def test_list_filter_by_topic(api_client: AsyncClient, dev_api_key: str) -> None:
    await _create_source(api_client, dev_api_key, source_key="TOPIC_A", topic_tags=["adoption", "barriers"])
    await _create_source(
        api_client,
        dev_api_key,
        source_key="TOPIC_B",
        topic_tags=["training"],
        original_url="https://example.com/topic-b",
    )
    response = await api_client.get("/api/v1/sources", params={"topic": "barriers"})
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["source_key"] == "TOPIC_A"


async def test_patch_source_updates_title(api_client: AsyncClient, dev_api_key: str) -> None:
    created = await _create_source(api_client, dev_api_key)
    response = await api_client.patch(
        f"/api/v1/sources/{created['id']}",
        json={"title": "Updated via PATCH"},
        headers={"X-API-Key": dev_api_key},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated via PATCH"


async def test_freshness_endpoint_reports_unknown_for_never_verified(
    api_client: AsyncClient, dev_api_key: str
) -> None:
    await _create_source(api_client, dev_api_key)
    response = await api_client.get("/api/v1/research/freshness", params={"state": "unknown"})
    assert response.status_code == 200
    body = response.json()
    assert any(item["source_key"] == "API_SOURCE" for item in body)
    assert all(item["freshness_state"] == "unknown" for item in body)


@pytest.mark.parametrize(
    "field_and_value",
    [
        {"status": "published"},
        {"rights_status": "reviewed_allowed"},
        {"access_policy": "full_text_allowed"},
    ],
)
async def test_patch_source_rejects_lifecycle_and_rights_fields(
    api_client: AsyncClient, dev_api_key: str, field_and_value: dict
) -> None:
    created = await _create_source(api_client, dev_api_key)
    response = await api_client.patch(
        f"/api/v1/sources/{created['id']}", json=field_and_value, headers={"X-API-Key": dev_api_key}
    )
    assert response.status_code == 422

    unchanged = await api_client.get(f"/api/v1/sources/{created['id']}")
    assert unchanged.json()["status"] == "registered"
    assert unchanged.json()["rights_status"] == "needs_review"
    assert unchanged.json()["access_policy"] == "metadata_only"


async def test_patch_source_rejects_unknown_field(api_client: AsyncClient, dev_api_key: str) -> None:
    created = await _create_source(api_client, dev_api_key)
    response = await api_client.patch(
        f"/api/v1/sources/{created['id']}",
        json={"totally_unknown_field": "x"},
        headers={"X-API-Key": dev_api_key},
    )
    assert response.status_code == 422


async def test_transition_endpoint_valid_transition_succeeds(
    api_client: AsyncClient, dev_api_key: str
) -> None:
    created = await _create_source(api_client, dev_api_key, source_key="TRANSITION_VALID")
    response = await api_client.post(
        f"/api/v1/sources/{created['id']}/transition",
        json={"new_status": "fetched", "reason": "content retrieved"},
        headers={"X-API-Key": dev_api_key},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "fetched"


async def test_transition_endpoint_invalid_transition_returns_409(
    api_client: AsyncClient, dev_api_key: str
) -> None:
    created = await _create_source(api_client, dev_api_key, source_key="TRANSITION_INVALID")
    response = await api_client.post(
        f"/api/v1/sources/{created['id']}/transition",
        json={"new_status": "published"},  # registered -> published is not allowed directly
        headers={"X-API-Key": dev_api_key},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "invalid_state_transition"


async def test_transition_endpoint_requires_api_key(api_client: AsyncClient, dev_api_key: str) -> None:
    created = await _create_source(api_client, dev_api_key, source_key="TRANSITION_AUTH")
    response = await api_client.post(
        f"/api/v1/sources/{created['id']}/transition", json={"new_status": "fetched"}
    )
    assert response.status_code == 401


async def test_transition_endpoint_creates_audit_event(api_client: AsyncClient, dev_api_key: str) -> None:
    from de_ai_kb.core.config import get_settings
    from de_ai_kb.db.session import get_sessionmaker
    from de_ai_kb.repositories.audit import AuditEventRepository

    created = await _create_source(api_client, dev_api_key, source_key="TRANSITION_AUDIT")
    response = await api_client.post(
        f"/api/v1/sources/{created['id']}/transition",
        json={"new_status": "fetched", "reason": "audited"},
        headers={"X-API-Key": dev_api_key},
    )
    assert response.status_code == 200

    session_factory = get_sessionmaker(get_settings().test_database_url)
    async with session_factory() as session:
        import uuid

        repo = AuditEventRepository(session)
        events = await repo.list_for_entity(entity_type="source", entity_id=uuid.UUID(created["id"]))
    assert any(e.action == "source.status_transition" for e in events)


async def test_block_endpoint_missing_reason_returns_422(api_client: AsyncClient, dev_api_key: str) -> None:
    created = await _create_source(api_client, dev_api_key, source_key="BLOCK_MISSING_REASON")
    response = await api_client.post(
        f"/api/v1/sources/{created['id']}/block", json={}, headers={"X-API-Key": dev_api_key}
    )
    assert response.status_code == 422


async def test_block_endpoint_blank_reason_returns_422(api_client: AsyncClient, dev_api_key: str) -> None:
    created = await _create_source(api_client, dev_api_key, source_key="BLOCK_BLANK_REASON")
    response = await api_client.post(
        f"/api/v1/sources/{created['id']}/block",
        json={"reason": "   "},
        headers={"X-API-Key": dev_api_key},
    )
    assert response.status_code == 422


async def test_block_endpoint_with_reason_blocks_and_audits(
    api_client: AsyncClient, dev_api_key: str
) -> None:
    from de_ai_kb.core.config import get_settings
    from de_ai_kb.db.session import get_sessionmaker
    from de_ai_kb.repositories.audit import AuditEventRepository

    created = await _create_source(api_client, dev_api_key, source_key="BLOCK_VALID")
    response = await api_client.post(
        f"/api/v1/sources/{created['id']}/block",
        json={"reason": "takedown request from publisher"},
        headers={"X-API-Key": dev_api_key},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "blocked"

    session_factory = get_sessionmaker(get_settings().test_database_url)
    async with session_factory() as session:
        import uuid

        repo = AuditEventRepository(session)
        events = await repo.list_for_entity(entity_type="source", entity_id=uuid.UUID(created["id"]))
    assert any(e.action == "source.status_transition" for e in events)


async def test_block_endpoint_requires_api_key(api_client: AsyncClient, dev_api_key: str) -> None:
    created = await _create_source(api_client, dev_api_key, source_key="BLOCK_AUTH")
    response = await api_client.post(f"/api/v1/sources/{created['id']}/block", json={"reason": "x"})
    assert response.status_code == 401
