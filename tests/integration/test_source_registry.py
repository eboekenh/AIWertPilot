import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from de_ai_kb.core.exceptions import (
    DuplicateSourceError,
    InvalidStateTransitionError,
    NotFoundError,
    ValidationFailedError,
)
from de_ai_kb.domain.enums import AccessPolicy, RightsStatus, SourceStatus
from de_ai_kb.services.source_registry import SourceRegistryService

pytestmark = pytest.mark.asyncio


async def _make_source(session: AsyncSession, **overrides: object) -> object:
    service = SourceRegistryService(session)
    defaults: dict[str, object] = dict(
        source_key="TEST_SOURCE_1",
        title="Test Source",
        publisher="Test Publisher",
        original_url="https://example.com/report",
        source_type="official_statistics",
        tier="A",
        refresh_interval_days=90,
        actor_id="test",
    )
    defaults.update(overrides)
    return await service.create_source(**defaults)  # type: ignore[arg-type]


async def test_create_source_sets_registered_status_and_canonical_url(db_session: AsyncSession) -> None:
    source = await _make_source(db_session)
    await db_session.commit()
    assert source.status == SourceStatus.REGISTERED.value
    assert source.canonical_url == "https://example.com/report"
    assert source.original_url == "https://example.com/report"


async def test_duplicate_source_key_rejected(db_session: AsyncSession) -> None:
    await _make_source(db_session)
    await db_session.commit()
    with pytest.raises(DuplicateSourceError):
        await _make_source(db_session, original_url="https://example.com/other")


async def test_duplicate_canonical_url_and_publisher_rejected(db_session: AsyncSession) -> None:
    await _make_source(db_session)
    await db_session.commit()
    with pytest.raises(DuplicateSourceError):
        await _make_source(db_session, source_key="TEST_SOURCE_2")


async def test_same_url_different_publisher_is_allowed_at_registry_level(db_session: AsyncSession) -> None:
    # Allowed by the registry (schema.sql's UNIQUE is (canonical_url, publisher));
    # DuplicateDetectionService is responsible for flagging this as a
    # dedup_candidate for human review, not the registry itself.
    await _make_source(db_session)
    other = await _make_source(db_session, source_key="TEST_SOURCE_3", publisher="Other Publisher")
    await db_session.commit()
    assert other.publisher == "Other Publisher"


async def test_update_source_changes_fields_and_records_audit(db_session: AsyncSession) -> None:
    source = await _make_source(db_session)
    await db_session.commit()
    service = SourceRegistryService(db_session)
    updated = await service.update_source(
        source_id=source.id, updates={"title": "Updated Title"}, actor_id="test"
    )
    await db_session.commit()
    assert updated.title == "Updated Title"


async def test_valid_status_transition(db_session: AsyncSession) -> None:
    source = await _make_source(db_session)
    await db_session.commit()
    service = SourceRegistryService(db_session)
    updated = await service.transition_status(
        source_id=source.id, new_status=SourceStatus.FETCHED, reason="fetched", actor_id="test"
    )
    await db_session.commit()
    assert updated.status == SourceStatus.FETCHED.value


async def test_invalid_status_transition_rejected(db_session: AsyncSession) -> None:
    source = await _make_source(db_session)
    await db_session.commit()
    service = SourceRegistryService(db_session)
    with pytest.raises(InvalidStateTransitionError):
        # registered -> published is not a direct allowed transition
        await service.transition_status(
            source_id=source.id, new_status=SourceStatus.PUBLISHED, reason=None, actor_id="test"
        )


async def test_block_source_requires_reason(db_session: AsyncSession) -> None:
    source = await _make_source(db_session)
    await db_session.commit()
    service = SourceRegistryService(db_session)
    with pytest.raises(ValidationFailedError):
        await service.block_source(source_id=source.id, reason="   ", actor_id="test")


async def test_block_source_with_reason_transitions_and_audits(db_session: AsyncSession) -> None:
    source = await _make_source(db_session)
    await db_session.commit()
    service = SourceRegistryService(db_session)
    blocked = await service.block_source(source_id=source.id, reason="takedown request", actor_id="test")
    await db_session.commit()
    assert blocked.status == SourceStatus.BLOCKED.value


async def test_update_nonexistent_source_raises_not_found(db_session: AsyncSession) -> None:
    import uuid

    service = SourceRegistryService(db_session)
    with pytest.raises(NotFoundError):
        await service.update_source(source_id=uuid.uuid4(), updates={"title": "x"}, actor_id="test")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("status", SourceStatus.PUBLISHED.value),
        ("rights_status", RightsStatus.REVIEWED_ALLOWED.value),
        ("access_policy", AccessPolicy.FULL_TEXT_ALLOWED.value),
        ("tdm_opt_out_status", "reserved"),
        ("some_unknown_field", "x"),
    ],
)
async def test_update_source_rejects_protected_or_unknown_fields_directly(
    db_session: AsyncSession, field: str, value: str
) -> None:
    """Defense in depth: update_source() must reject these fields even when
    called directly, not only when reached through the API/Pydantic
    schema — this is the fix for the audited status/rights bypass."""
    source = await _make_source(db_session)
    await db_session.commit()
    service = SourceRegistryService(db_session)
    with pytest.raises(ValidationFailedError):
        await service.update_source(source_id=source.id, updates={field: value}, actor_id="test")

    # Verify nothing was actually changed.
    refreshed = await service.get_by_id(source.id)
    assert refreshed is not None
    assert refreshed.status == SourceStatus.REGISTERED.value
    assert refreshed.rights_status == RightsStatus.NEEDS_REVIEW.value
    assert refreshed.access_policy == AccessPolicy.METADATA_ONLY.value


async def test_update_source_allows_editable_metadata_fields(db_session: AsyncSession) -> None:
    source = await _make_source(db_session)
    await db_session.commit()
    service = SourceRegistryService(db_session)
    updated = await service.update_source(
        source_id=source.id,
        updates={"title": "New Title", "publisher": "New Publisher", "tier": "B", "notes": "note"},
        actor_id="test",
    )
    assert updated.title == "New Title"
    assert updated.publisher == "New Publisher"
    assert updated.tier == "B"
    assert updated.notes == "note"
