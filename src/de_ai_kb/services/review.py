"""Review-item lifecycle: creation, decisions, and state-machine enforcement."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from de_ai_kb.core.exceptions import InvalidStateTransitionError, NotFoundError
from de_ai_kb.db.models.ops import ReviewItem
from de_ai_kb.domain.enums import (
    REVIEW_ITEM_STATUS_TRANSITIONS,
    REVIEW_TYPE_CONTENT,
    REVIEW_TYPE_RIGHTS,
    ReviewItemStatus,
)
from de_ai_kb.repositories.review import ReviewItemFilters, ReviewItemRepository
from de_ai_kb.services.audit import AuditService


class ReviewService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ReviewItemRepository(session)
        self._audit = AuditService(session)

    async def create_standard_source_review_items(
        self, *, source_id: uuid.UUID, actor_id: str
    ) -> list[ReviewItem]:
        """Create the two mandatory review items for a newly imported/registered
        source: rights/access review and content review. Idempotent — if an
        open item of the same review_type already exists for this source, it
        is left as-is and not duplicated (the UNIQUE(entity_type, entity_id,
        review_type, status) constraint would reject a duplicate anyway)."""
        created: list[ReviewItem] = []
        for review_type in (REVIEW_TYPE_RIGHTS, REVIEW_TYPE_CONTENT):
            existing = await self._repo.get_open(
                entity_type="source", entity_id=source_id, review_type=review_type
            )
            if existing is not None:
                continue
            item = ReviewItem(entity_type="source", entity_id=source_id, review_type=review_type)
            self._repo.add(item)
            await self._session.flush()
            self._audit.record(
                actor_type="system",
                actor_id=actor_id,
                action="review_item.created",
                entity_type="review_item",
                entity_id=item.id,
                after_state={
                    "entity_type": "source", "entity_id": str(source_id), "review_type": review_type,
                },
            )
            created.append(item)
        return created

    async def create_dedup_candidate(
        self,
        *,
        source_id: uuid.UUID,
        counterpart_source_id: uuid.UUID,
        similarity_score: float,
        reason: str,
        actor_id: str,
    ) -> ReviewItem | None:
        # schema.sql's UNIQUE(entity_type, entity_id, review_type, status)
        # allows at most one *open* dedup_candidate item per source. If one
        # already exists, leave it in place rather than raising a constraint
        # violation on a re-scan — this is what makes repeated dedup scans
        # idempotent.
        existing = await self._repo.get_open(
            entity_type="source", entity_id=source_id, review_type="dedup_candidate"
        )
        if existing is not None:
            return None
        item = ReviewItem(
            entity_type="source",
            entity_id=source_id,
            review_type="dedup_candidate",
            metadata_={
                "counterpart_source_id": str(counterpart_source_id),
                "similarity_score": round(similarity_score, 4),
                "reason": reason,
            },
        )
        self._repo.add(item)
        await self._session.flush()
        self._audit.record(
            actor_type="system",
            actor_id=actor_id,
            action="review_item.dedup_candidate_created",
            entity_type="review_item",
            entity_id=item.id,
            after_state=item.metadata_,
        )
        return item

    async def decide(
        self,
        *,
        review_item_id: uuid.UUID,
        new_status: ReviewItemStatus,
        decision_reason: str | None,
        actor_id: str,
    ) -> ReviewItem:
        item = await self._repo.get_by_id(review_item_id)
        if item is None:
            raise NotFoundError(f"review_item {review_item_id} not found")

        current = ReviewItemStatus(item.status)
        allowed = REVIEW_ITEM_STATUS_TRANSITIONS.get(current, set())
        if new_status not in allowed:
            raise InvalidStateTransitionError(
                f"review_item {review_item_id}: cannot transition from {current.value} to {new_status.value}",
                details={"from": current.value, "to": new_status.value},
            )

        before: dict[str, Any] = {"status": item.status, "decision_reason": item.decision_reason}
        item.status = new_status.value
        item.decision_reason = decision_reason
        if new_status in (
            ReviewItemStatus.APPROVED,
            ReviewItemStatus.REJECTED,
            ReviewItemStatus.NEEDS_CHANGES,
            ReviewItemStatus.CANCELLED,
        ):
            from datetime import UTC, datetime

            item.decided_at = datetime.now(UTC)

        await self._session.flush()
        self._audit.record(
            actor_type="api_key",
            actor_id=actor_id,
            action="review_item.decision",
            entity_type="review_item",
            entity_id=item.id,
            before_state=before,
            after_state={"status": item.status, "decision_reason": item.decision_reason},
        )
        return item

    async def list(
        self, *, filters: ReviewItemFilters, limit: int, offset: int
    ) -> tuple[list[ReviewItem], int]:
        return await self._repo.list_page(filters=filters, limit=limit, offset=offset)
