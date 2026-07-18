import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from de_ai_kb.core.exceptions import InvalidStateTransitionError
from de_ai_kb.db.models.sources import Source
from de_ai_kb.domain.enums import REVIEW_TYPE_CONTENT, REVIEW_TYPE_RIGHTS, ReviewItemStatus
from de_ai_kb.repositories.audit import AuditEventRepository
from de_ai_kb.repositories.sources import SourceRepository
from de_ai_kb.services.review import ReviewService

pytestmark = pytest.mark.asyncio


async def _make_source(session: AsyncSession) -> Source:
    repo = SourceRepository(session)
    source = Source(
        source_key="REVIEW_SOURCE",
        title="Review Source",
        publisher="Publisher",
        original_url="https://example.com/review",
        canonical_url="https://example.com/review",
        source_type="official_statistics",
        tier="A",
        refresh_interval_days=90,
    )
    repo.add(source)
    await session.flush()
    return source


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
    item = items[0]

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
    item = items[0]

    await service.decide(
        review_item_id=item.id, new_status=ReviewItemStatus.APPROVED, decision_reason=None, actor_id="test"
    )
    await db_session.commit()

    with pytest.raises(InvalidStateTransitionError):
        # approved is terminal; cannot transition further
        await service.decide(
            review_item_id=item.id, new_status=ReviewItemStatus.OPEN, decision_reason=None, actor_id="test"
        )


async def test_source_creation_records_audit_event(db_session: AsyncSession) -> None:
    from de_ai_kb.services.source_registry import SourceRegistryService

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
    )
    await db_session.commit()

    audit_repo = AuditEventRepository(db_session)
    events = await audit_repo.list_for_entity(entity_type="source", entity_id=source.id)
    assert any(e.action == "source.created" for e in events)
