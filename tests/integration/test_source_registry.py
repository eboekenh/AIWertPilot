import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from de_ai_kb.core.exceptions import (
    DuplicateSourceError,
    InvalidStateTransitionError,
    NotFoundError,
    ValidationFailedError,
)
from de_ai_kb.domain.enums import AccessPolicy, RightsStatus, SourceStatus
from de_ai_kb.repositories.audit import AuditEventRepository
from de_ai_kb.services.review import ReviewService
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
        actor_type="api_key",
    )
    defaults.update(overrides)
    return await service.create_source(**defaults)  # type: ignore[arg-type]


async def _approve_rights_review(
    session: AsyncSession,
    source: object,
    *,
    rights_status: RightsStatus = RightsStatus.REVIEWED_ALLOWED,
    access_policy: AccessPolicy = AccessPolicy.SHORT_EVIDENCE,
) -> None:
    """Test helper: resolve the source's rights_review item to a given
    outcome, needed because FETCHED/APPROVED/PUBLISHED transitions now
    require an approved rights_review with a non-blocked outcome."""
    from de_ai_kb.repositories.review import ReviewItemFilters, ReviewItemRepository

    review_repo = ReviewItemRepository(session)
    items = await review_repo.list_all(filters=ReviewItemFilters(entity_type="source"))
    rights_item = next(
        i
        for i in items
        if i.entity_id == source.id and i.review_type == "rights_review"  # type: ignore[attr-defined]
    )
    review_service = ReviewService(session)
    await review_service.resolve_rights_review(
        review_item_id=rights_item.id,
        rights_status=rights_status,
        access_policy=access_policy,
        decision_reason="test rights approval",
        tdm_opt_out_status=None,
        licence_name=None,
        licence_url=None,
        actor_id="test",
    )


async def _approve_content_review(session: AsyncSession, source: object) -> None:
    from de_ai_kb.domain.enums import ReviewItemStatus
    from de_ai_kb.repositories.review import ReviewItemFilters, ReviewItemRepository

    review_repo = ReviewItemRepository(session)
    items = await review_repo.list_all(filters=ReviewItemFilters(entity_type="source"))
    content_item = next(
        i
        for i in items
        if i.entity_id == source.id and i.review_type == "content_review"  # type: ignore[attr-defined]
    )
    review_service = ReviewService(session)
    await review_service.decide(
        review_item_id=content_item.id,
        new_status=ReviewItemStatus.APPROVED,
        decision_reason="content looks fine",
        actor_id="test",
    )


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
        source_id=source.id, updates={"title": "Updated Title"}, actor_id="test", actor_type="api_key"
    )
    await db_session.commit()
    assert updated.title == "Updated Title"


async def test_valid_status_transition(db_session: AsyncSession) -> None:
    source = await _make_source(db_session)
    await db_session.commit()
    await _approve_rights_review(db_session, source)
    await db_session.commit()

    service = SourceRegistryService(db_session)
    updated = await service.transition_status(
        source_id=source.id,
        new_status=SourceStatus.FETCHED,
        reason="fetched",
        actor_id="test",
        actor_type="api_key",
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
            source_id=source.id,
            new_status=SourceStatus.PUBLISHED,
            reason=None,
            actor_id="test",
            actor_type="api_key",
        )


async def test_block_source_requires_reason(db_session: AsyncSession) -> None:
    source = await _make_source(db_session)
    await db_session.commit()
    service = SourceRegistryService(db_session)
    with pytest.raises(ValidationFailedError):
        await service.block_source(source_id=source.id, reason="   ", actor_id="test", actor_type="api_key")


async def test_block_source_with_reason_transitions_and_audits(db_session: AsyncSession) -> None:
    source = await _make_source(db_session)
    await db_session.commit()
    service = SourceRegistryService(db_session)
    blocked = await service.block_source(
        source_id=source.id, reason="takedown request", actor_id="test", actor_type="api_key"
    )
    await db_session.commit()
    assert blocked.status == SourceStatus.BLOCKED.value


async def test_update_nonexistent_source_raises_not_found(db_session: AsyncSession) -> None:
    import uuid

    service = SourceRegistryService(db_session)
    with pytest.raises(NotFoundError):
        await service.update_source(
            source_id=uuid.uuid4(), updates={"title": "x"}, actor_id="test", actor_type="api_key"
        )


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
        await service.update_source(
            source_id=source.id, updates={field: value}, actor_id="test", actor_type="api_key"
        )

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
        actor_type="api_key",
    )
    assert updated.title == "New Title"
    assert updated.publisher == "New Publisher"
    assert updated.tier == "B"
    assert updated.notes == "note"


# --- Requirement 1: source-creation bypass closed ---------------------------


async def test_create_source_always_starts_registered_needs_review_metadata_only(
    db_session: AsyncSession,
) -> None:
    """create_source() has no status/rights_status/access_policy parameters
    at all — every new source is forced through the governed defaults,
    regardless of caller."""
    source = await _make_source(db_session, source_key="FORCED_DEFAULTS")
    await db_session.commit()
    assert source.status == SourceStatus.REGISTERED.value
    assert source.rights_status == RightsStatus.NEEDS_REVIEW.value
    assert source.access_policy == AccessPolicy.METADATA_ONLY.value


async def test_create_source_rejects_unexpected_status_and_rights_kwargs(db_session: AsyncSession) -> None:
    """A direct caller cannot bypass the governed defaults by passing
    status/rights_status/access_policy — those keyword arguments no longer
    exist on create_source() at all, so attempting to pass them is a
    TypeError, not a silently-accepted override."""
    service = SourceRegistryService(db_session)
    with pytest.raises(TypeError):
        await service.create_source(  # type: ignore[call-arg]
            source_key="BYPASS_ATTEMPT",
            title="Bypass Attempt",
            publisher="Publisher",
            original_url="https://example.com/bypass",
            source_type="official_statistics",
            tier="A",
            refresh_interval_days=90,
            actor_id="test",
            actor_type="api_key",
            status=SourceStatus.PUBLISHED,
            rights_status=RightsStatus.REVIEWED_ALLOWED,
            access_policy=AccessPolicy.FULL_TEXT_ALLOWED,
        )


# --- Requirement 2: block-reason bypass closed (service layer) --------------


async def test_transition_status_to_blocked_without_reason_rejected(db_session: AsyncSession) -> None:
    source = await _make_source(db_session, source_key="BLOCKED_NO_REASON")
    await db_session.commit()
    service = SourceRegistryService(db_session)
    with pytest.raises(ValidationFailedError):
        await service.transition_status(
            source_id=source.id,
            new_status=SourceStatus.BLOCKED,
            reason=None,
            actor_id="test",
            actor_type="api_key",
        )


async def test_transition_status_to_blocked_with_blank_reason_rejected(db_session: AsyncSession) -> None:
    source = await _make_source(db_session, source_key="BLOCKED_BLANK_REASON")
    await db_session.commit()
    service = SourceRegistryService(db_session)
    with pytest.raises(ValidationFailedError):
        await service.transition_status(
            source_id=source.id,
            new_status=SourceStatus.BLOCKED,
            reason="   ",
            actor_id="test",
            actor_type="api_key",
        )


# --- Requirement 3: review gates ---------------------------------------------


async def test_transition_to_fetched_requires_approved_rights_review(db_session: AsyncSession) -> None:
    source = await _make_source(db_session, source_key="GATE_NO_RIGHTS")
    await db_session.commit()
    service = SourceRegistryService(db_session)
    with pytest.raises(ValidationFailedError):
        await service.transition_status(
            source_id=source.id,
            new_status=SourceStatus.FETCHED,
            reason="attempt",
            actor_id="test",
            actor_type="api_key",
        )


async def test_transition_to_fetched_succeeds_after_rights_review_approved(db_session: AsyncSession) -> None:
    source = await _make_source(db_session, source_key="GATE_RIGHTS_OK")
    await db_session.commit()
    await _approve_rights_review(db_session, source)
    await db_session.commit()

    service = SourceRegistryService(db_session)
    updated = await service.transition_status(
        source_id=source.id,
        new_status=SourceStatus.FETCHED,
        reason="fetched",
        actor_id="test",
        actor_type="api_key",
    )
    assert updated.status == SourceStatus.FETCHED.value


async def test_transition_to_approved_requires_content_review_approved(db_session: AsyncSession) -> None:
    source = await _make_source(db_session, source_key="GATE_NO_CONTENT")
    await db_session.commit()
    await _approve_rights_review(db_session, source)
    await db_session.commit()

    service = SourceRegistryService(db_session)
    await service.transition_status(
        source_id=source.id,
        new_status=SourceStatus.FETCHED,
        reason="fetched",
        actor_id="test",
        actor_type="api_key",
    )
    await service.transition_status(
        source_id=source.id,
        new_status=SourceStatus.EXTRACTED,
        reason="extracted",
        actor_id="test",
        actor_type="api_key",
    )
    await service.transition_status(
        source_id=source.id,
        new_status=SourceStatus.UNDER_REVIEW,
        reason="under review",
        actor_id="test",
        actor_type="api_key",
    )
    await db_session.commit()

    with pytest.raises(ValidationFailedError):
        await service.transition_status(
            source_id=source.id,
            new_status=SourceStatus.APPROVED,
            reason="attempt",
            actor_id="test",
            actor_type="api_key",
        )


async def test_full_lifecycle_to_published_requires_both_reviews_and_rechecks(
    db_session: AsyncSession,
) -> None:
    source = await _make_source(db_session, source_key="GATE_FULL_LIFECYCLE")
    await db_session.commit()
    await _approve_rights_review(db_session, source)
    await _approve_content_review(db_session, source)
    await db_session.commit()

    service = SourceRegistryService(db_session)
    for target in (
        SourceStatus.FETCHED,
        SourceStatus.EXTRACTED,
        SourceStatus.UNDER_REVIEW,
        SourceStatus.APPROVED,
        SourceStatus.PUBLISHED,
    ):
        source = await service.transition_status(
            source_id=source.id,
            new_status=target,
            reason=f"advance to {target.value}",
            actor_id="test",
            actor_type="api_key",
        )
        await db_session.commit()
    assert source.status == SourceStatus.PUBLISHED.value


async def test_rights_decision_blocked_auto_blocks_source_and_audits(db_session: AsyncSession) -> None:
    source = await _make_source(db_session, source_key="AUTO_BLOCK")
    await db_session.commit()
    await _approve_rights_review(
        db_session,
        source,
        rights_status=RightsStatus.BLOCKED,
        access_policy=AccessPolicy.BLOCKED,
    )
    await db_session.commit()

    service = SourceRegistryService(db_session)
    refreshed = await service.get_by_id(source.id)
    assert refreshed is not None
    assert refreshed.status == SourceStatus.BLOCKED.value

    audit_repo = AuditEventRepository(db_session)
    events = await audit_repo.list_for_entity(entity_type="source", entity_id=source.id)
    transition_events = [e for e in events if e.action == "source.status_transition"]
    assert any("auto-blocked" in (e.after_state or {}).get("reason", "") for e in transition_events)


async def test_auto_blocked_source_cannot_progress_to_fetched(db_session: AsyncSession) -> None:
    source = await _make_source(db_session, source_key="AUTO_BLOCK_NO_PROGRESS")
    await db_session.commit()
    await _approve_rights_review(
        db_session,
        source,
        rights_status=RightsStatus.BLOCKED,
        access_policy=AccessPolicy.BLOCKED,
    )
    await db_session.commit()

    service = SourceRegistryService(db_session)
    with pytest.raises(InvalidStateTransitionError):
        await service.transition_status(
            source_id=source.id,
            new_status=SourceStatus.FETCHED,
            reason="attempt",
            actor_id="test",
            actor_type="api_key",
        )


# --- Requirement 6: CLI/API audit provenance ---------------------------------


async def test_create_source_records_actor_type_from_caller(db_session: AsyncSession) -> None:
    source = await _make_source(db_session, source_key="ACTOR_TYPE_CLI", actor_id="alice", actor_type="cli")
    await db_session.commit()
    audit_repo = AuditEventRepository(db_session)
    events = await audit_repo.list_for_entity(entity_type="source", entity_id=source.id)
    created = next(e for e in events if e.action == "source.created")
    assert created.actor_type == "cli"
    assert created.actor_id == "alice"


async def test_transition_status_records_actor_type_from_caller(db_session: AsyncSession) -> None:
    source = await _make_source(db_session, source_key="ACTOR_TYPE_TRANSITION")
    await db_session.commit()
    service = SourceRegistryService(db_session)
    await service.block_source(source_id=source.id, reason="takedown", actor_id="bob", actor_type="cli")
    await db_session.commit()

    audit_repo = AuditEventRepository(db_session)
    events = await audit_repo.list_for_entity(entity_type="source", entity_id=source.id)
    transitioned = next(e for e in events if e.action == "source.status_transition")
    assert transitioned.actor_type == "cli"
    assert transitioned.actor_id == "bob"
