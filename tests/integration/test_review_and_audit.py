import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from de_ai_kb.core.exceptions import InvalidStateTransitionError, ValidationFailedError
from de_ai_kb.db.models.sources import Source
from de_ai_kb.domain.enums import (
    REVIEW_TYPE_CONTENT,
    REVIEW_TYPE_RIGHTS,
    AccessPolicy,
    ReviewItemStatus,
    RightsStatus,
)
from de_ai_kb.repositories.audit import AuditEventRepository
from de_ai_kb.repositories.review import ReviewItemRepository
from de_ai_kb.repositories.sources import SourceRepository
from de_ai_kb.services.review import ReviewService
from de_ai_kb.services.source_registry import SourceRegistryService

pytestmark = pytest.mark.asyncio


async def _make_source(session: AsyncSession, source_key: str = "REVIEW_SOURCE") -> Source:
    repo = SourceRepository(session)
    source = Source(
        source_key=source_key,
        title="Review Source",
        publisher="Publisher",
        original_url=f"https://example.com/{source_key.lower()}",
        canonical_url=f"https://example.com/{source_key.lower()}",
        source_type="official_statistics",
        tier="A",
        refresh_interval_days=90,
    )
    repo.add(source)
    await session.flush()
    return source


def _item_by_type(items: list, review_type: str):  # type: ignore[no-untyped-def]
    return next(i for i in items if i.review_type == review_type)


async def test_create_standard_review_items_creates_exactly_two(db_session: AsyncSession) -> None:
    source = await _make_source(db_session)
    service = ReviewService(db_session)
    items = await service.create_standard_source_review_items(source_id=source.id, actor_id="test")
    await db_session.commit()
    assert len(items) == 2
    review_types = {i.review_type for i in items}
    assert review_types == {REVIEW_TYPE_RIGHTS, REVIEW_TYPE_CONTENT}


async def test_create_standard_review_items_is_idempotent(db_session: AsyncSession) -> None:
    source = await _make_source(db_session)
    service = ReviewService(db_session)
    first = await service.create_standard_source_review_items(source_id=source.id, actor_id="test")
    await db_session.commit()
    second = await service.create_standard_source_review_items(source_id=source.id, actor_id="test")
    await db_session.commit()
    assert len(first) == 2
    assert len(second) == 0  # both already open -> nothing new created


async def test_review_decision_valid_transition_records_audit(db_session: AsyncSession) -> None:
    source = await _make_source(db_session)
    service = ReviewService(db_session)
    items = await service.create_standard_source_review_items(source_id=source.id, actor_id="test")
    await db_session.commit()
    item = _item_by_type(items, REVIEW_TYPE_CONTENT)

    decided = await service.decide(
        review_item_id=item.id,
        new_status=ReviewItemStatus.APPROVED,
        decision_reason="looks fine",
        actor_id="test",
    )
    await db_session.commit()
    assert decided.status == ReviewItemStatus.APPROVED.value
    assert decided.decided_at is not None

    audit_repo = AuditEventRepository(db_session)
    events = await audit_repo.list_for_entity(entity_type="review_item", entity_id=item.id)
    actions = {e.action for e in events}
    assert "review_item.decision" in actions


async def test_review_decision_invalid_transition_rejected(db_session: AsyncSession) -> None:
    source = await _make_source(db_session)
    service = ReviewService(db_session)
    items = await service.create_standard_source_review_items(source_id=source.id, actor_id="test")
    await db_session.commit()
    item = _item_by_type(items, REVIEW_TYPE_CONTENT)

    await service.decide(
        review_item_id=item.id, new_status=ReviewItemStatus.APPROVED, decision_reason=None, actor_id="test"
    )
    await db_session.commit()

    with pytest.raises(InvalidStateTransitionError):
        # approved is terminal; cannot transition further
        await service.decide(
            review_item_id=item.id, new_status=ReviewItemStatus.OPEN, decision_reason=None, actor_id="test"
        )


async def test_generic_decide_rejects_rights_review_approval(db_session: AsyncSession) -> None:
    """A generic review decision must not be able to approve a rights_review
    item — that would leave review_items.status=approved with the source's
    rights fields silently unchanged. Must use resolve_rights_review."""
    source = await _make_source(db_session)
    service = ReviewService(db_session)
    items = await service.create_standard_source_review_items(source_id=source.id, actor_id="test")
    await db_session.commit()
    item = _item_by_type(items, REVIEW_TYPE_RIGHTS)

    with pytest.raises(ValidationFailedError):
        await service.decide(
            review_item_id=item.id,
            new_status=ReviewItemStatus.APPROVED,
            decision_reason="approved",
            actor_id="test",
        )


async def test_generic_decide_non_approval_still_works_for_rights_review(db_session: AsyncSession) -> None:
    """Rejecting/cancelling a rights_review carries no rights implication and
    must remain usable via the normal decision workflow."""
    source = await _make_source(db_session)
    service = ReviewService(db_session)
    items = await service.create_standard_source_review_items(source_id=source.id, actor_id="test")
    await db_session.commit()
    item = _item_by_type(items, REVIEW_TYPE_RIGHTS)

    decided = await service.decide(
        review_item_id=item.id,
        new_status=ReviewItemStatus.REJECTED,
        decision_reason="not a usable source",
        actor_id="test",
    )
    assert decided.status == ReviewItemStatus.REJECTED.value


async def test_resolve_rights_review_valid_updates_both_atomically(db_session: AsyncSession) -> None:
    source = await _make_source(db_session)
    service = ReviewService(db_session)
    items = await service.create_standard_source_review_items(source_id=source.id, actor_id="test")
    await db_session.commit()
    item = _item_by_type(items, REVIEW_TYPE_RIGHTS)

    decided_item, updated_source = await service.resolve_rights_review(
        review_item_id=item.id,
        rights_status=RightsStatus.REVIEWED_ALLOWED,
        access_policy=AccessPolicy.SHORT_EVIDENCE,
        decision_reason="publisher licence confirmed",
        tdm_opt_out_status=None,
        licence_name=None,
        licence_url=None,
        actor_id="test",
    )
    await db_session.commit()

    assert decided_item.status == ReviewItemStatus.APPROVED.value
    assert updated_source.rights_status == RightsStatus.REVIEWED_ALLOWED.value
    assert updated_source.access_policy == AccessPolicy.SHORT_EVIDENCE.value

    audit_repo = AuditEventRepository(db_session)
    review_events = await audit_repo.list_for_entity(entity_type="review_item", entity_id=item.id)
    assert any(e.action == "review_item.rights_decision" for e in review_events)
    source_events = await audit_repo.list_for_entity(entity_type="source", entity_id=source.id)
    assert any(e.action == "source.rights_reviewed" for e in source_events)


async def test_resolve_rights_review_invalid_combination_changes_neither_record(
    db_session: AsyncSession,
) -> None:
    source = await _make_source(db_session)
    service = ReviewService(db_session)
    items = await service.create_standard_source_review_items(source_id=source.id, actor_id="test")
    await db_session.commit()
    item = _item_by_type(items, REVIEW_TYPE_RIGHTS)

    with pytest.raises(ValidationFailedError):
        await service.resolve_rights_review(
            review_item_id=item.id,
            rights_status=RightsStatus.BLOCKED,
            access_policy=AccessPolicy.FULL_TEXT_ALLOWED,  # invalid: blocked must pair with BLOCKED
            decision_reason="bad combination",
            tdm_opt_out_status=None,
            licence_name=None,
            licence_url=None,
            actor_id="test",
        )

    source_repo = SourceRepository(db_session)
    unchanged_source = await source_repo.get_by_id(source.id)
    assert unchanged_source is not None
    assert unchanged_source.rights_status == RightsStatus.NEEDS_REVIEW.value
    assert unchanged_source.access_policy == AccessPolicy.METADATA_ONLY.value

    review_repo = ReviewItemRepository(db_session)
    unchanged_item = await review_repo.get_by_id(item.id)
    assert unchanged_item is not None
    assert unchanged_item.status == ReviewItemStatus.OPEN.value


async def test_non_rights_decision_does_not_alter_source_rights_fields(db_session: AsyncSession) -> None:
    source = await _make_source(db_session)
    service = ReviewService(db_session)
    items = await service.create_standard_source_review_items(source_id=source.id, actor_id="test")
    await db_session.commit()
    content_item = _item_by_type(items, REVIEW_TYPE_CONTENT)

    await service.decide(
        review_item_id=content_item.id,
        new_status=ReviewItemStatus.APPROVED,
        decision_reason="content looks fine",
        actor_id="test",
    )
    await db_session.commit()

    repo = SourceRepository(db_session)
    refreshed = await repo.get_by_id(source.id)
    assert refreshed is not None
    assert refreshed.rights_status == RightsStatus.NEEDS_REVIEW.value
    assert refreshed.access_policy == AccessPolicy.METADATA_ONLY.value


async def test_source_creation_records_audit_event(db_session: AsyncSession) -> None:
    service = SourceRegistryService(db_session)
    source = await service.create_source(
        source_key="AUDIT_SOURCE",
        title="Audit Source",
        publisher="Publisher",
        original_url="https://example.com/audit",
        source_type="official_statistics",
        tier="A",
        refresh_interval_days=90,
        actor_id="test",
        actor_type="api_key",
    )
    await db_session.commit()

    audit_repo = AuditEventRepository(db_session)
    events = await audit_repo.list_for_entity(entity_type="source", entity_id=source.id)
    assert any(e.action == "source.created" for e in events)


async def test_create_source_creates_exactly_two_standard_review_items(db_session: AsyncSession) -> None:
    """create_source() itself must guarantee the two standard review items —
    the invariant is centralized here, not duplicated by each caller."""
    from de_ai_kb.repositories.review import ReviewItemFilters, ReviewItemRepository

    service = SourceRegistryService(db_session)
    source = await service.create_source(
        source_key="CENTRALIZED_REVIEW_SOURCE",
        title="Centralized Review Source",
        publisher="Publisher",
        original_url="https://example.com/centralized-review",
        source_type="official_statistics",
        tier="A",
        refresh_interval_days=90,
        actor_id="test",
        actor_type="api_key",
    )
    await db_session.commit()

    review_repo = ReviewItemRepository(db_session)
    items = await review_repo.list_all(filters=ReviewItemFilters(entity_type="source"))
    matching = [i for i in items if i.entity_id == source.id]
    assert len(matching) == 2
    assert {i.review_type for i in matching} == {REVIEW_TYPE_RIGHTS, REVIEW_TYPE_CONTENT}
    assert all(i.status == ReviewItemStatus.OPEN.value for i in matching)


async def test_resolve_rights_review_rejects_blank_decision_reason(db_session: AsyncSession) -> None:
    source = await _make_source(db_session)
    service = ReviewService(db_session)
    items = await service.create_standard_source_review_items(source_id=source.id, actor_id="test")
    await db_session.commit()
    item = _item_by_type(items, REVIEW_TYPE_RIGHTS)

    with pytest.raises(ValidationFailedError):
        await service.resolve_rights_review(
            review_item_id=item.id,
            rights_status=RightsStatus.REVIEWED_ALLOWED,
            access_policy=AccessPolicy.SHORT_EVIDENCE,
            decision_reason="   ",
            tdm_opt_out_status=None,
            licence_name=None,
            licence_url=None,
            actor_id="test",
        )

    unchanged_item = await ReviewItemRepository(db_session).get_by_id(item.id)
    assert unchanged_item is not None
    assert unchanged_item.status == ReviewItemStatus.OPEN.value
    unchanged_source = await SourceRepository(db_session).get_by_id(source.id)
    assert unchanged_source is not None
    assert unchanged_source.rights_status == RightsStatus.NEEDS_REVIEW.value


async def test_resolve_rights_review_rejects_non_source_entity_type(db_session: AsyncSession) -> None:
    """A rights_review item that (incorrectly) points at a non-source entity
    must be rejected outright, and must change neither the review item nor
    any source."""
    from de_ai_kb.db.models.ops import ReviewItem

    repo = ReviewItemRepository(db_session)
    stray_item = ReviewItem(entity_type="document", entity_id=uuid.uuid4(), review_type=REVIEW_TYPE_RIGHTS)
    repo.add(stray_item)
    await db_session.flush()
    await db_session.commit()

    service = ReviewService(db_session)
    with pytest.raises(ValidationFailedError):
        await service.resolve_rights_review(
            review_item_id=stray_item.id,
            rights_status=RightsStatus.REVIEWED_ALLOWED,
            access_policy=AccessPolicy.SHORT_EVIDENCE,
            decision_reason="should not apply",
            tdm_opt_out_status=None,
            licence_name=None,
            licence_url=None,
            actor_id="test",
        )

    unchanged_item = await repo.get_by_id(stray_item.id)
    assert unchanged_item is not None
    assert unchanged_item.status == ReviewItemStatus.OPEN.value
    assert unchanged_item.decision_reason is None
