"""Review-item lifecycle: creation, decisions, and state-machine enforcement."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from de_ai_kb.core.exceptions import (
    InvalidStateTransitionError,
    NotFoundError,
    ValidationFailedError,
)
from de_ai_kb.db.models.ops import ReviewItem
from de_ai_kb.db.models.sources import Source
from de_ai_kb.domain.enums import (
    REVIEW_ITEM_STATUS_TRANSITIONS,
    REVIEW_TYPE_CONTENT,
    REVIEW_TYPE_RIGHTS,
    SOURCE_STATUS_TRANSITIONS,
    AccessPolicy,
    ReviewItemStatus,
    RightsStatus,
    SourceStatus,
    TdmOptOutStatus,
)
from de_ai_kb.domain.rights_policy import validate_rights_resolution
from de_ai_kb.repositories.review import ReviewItemFilters, ReviewItemRepository
from de_ai_kb.repositories.sources import SourceRepository
from de_ai_kb.services.audit import AuditService


class ReviewService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ReviewItemRepository(session)
        self._source_repo = SourceRepository(session)
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
                    "entity_type": "source",
                    "entity_id": str(source_id),
                    "review_type": review_type,
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

    async def is_rights_review_approved(self, *, source_id: uuid.UUID) -> bool:
        """Whether the source's rights_review item has been approved (via
        resolve_rights_review). Used by SourceRegistryService to gate status
        transitions — see SOURCE_STATUS_TRANSITIONS callers."""
        return await self._repo.has_status(
            entity_type="source",
            entity_id=source_id,
            review_type=REVIEW_TYPE_RIGHTS,
            status=ReviewItemStatus.APPROVED.value,
        )

    async def is_content_review_approved(self, *, source_id: uuid.UUID) -> bool:
        """Whether the source's content_review item has been approved."""
        return await self._repo.has_status(
            entity_type="source",
            entity_id=source_id,
            review_type=REVIEW_TYPE_CONTENT,
            status=ReviewItemStatus.APPROVED.value,
        )

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

        # A rights_review item can only be *approved* through the dedicated
        # rights-decision workflow (resolve_rights_review), which requires
        # explicit reviewed rights_status/access_policy values in the same
        # transaction as the decision. Approving it here would leave
        # review_items.status="approved" with the source's rights fields
        # untouched — an inconsistent "reviewed but nothing was actually
        # decided" state. Every other transition (reject/needs_changes/
        # cancel/in_progress) carries no rights implication and is
        # unaffected — non-rights review items always use this method.
        if item.review_type == REVIEW_TYPE_RIGHTS and new_status == ReviewItemStatus.APPROVED:
            raise ValidationFailedError(
                "rights_review items must be approved via "
                "POST /api/v1/review-items/{id}/rights-decision with explicit "
                "reviewed rights_status/access_policy values",
                details={"review_item_id": str(review_item_id)},
            )

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

    async def resolve_rights_review(
        self,
        *,
        review_item_id: uuid.UUID,
        rights_status: RightsStatus,
        access_policy: AccessPolicy,
        decision_reason: str,
        tdm_opt_out_status: TdmOptOutStatus | None,
        licence_name: str | None,
        licence_url: str | None,
        actor_id: str,
    ) -> tuple[ReviewItem, Source]:
        """Approve a rights_review item and apply its outcome to the source's
        actual rights fields, atomically (same session/transaction, no
        commit until the caller's request-scoped session commits).

        Validation happens entirely before any mutation, so a rejected
        rights/access combination or an invalid state transition leaves
        both the review item and the source completely untouched.
        """
        if not decision_reason.strip():
            raise ValidationFailedError(
                "a non-blank decision_reason is required to resolve a rights_review",
                details={"review_item_id": str(review_item_id)},
            )

        item = await self._repo.get_by_id(review_item_id)
        if item is None:
            raise NotFoundError(f"review_item {review_item_id} not found")

        if item.review_type != REVIEW_TYPE_RIGHTS:
            raise ValidationFailedError(
                f"review_item {review_item_id} is not a rights_review item "
                f"(review_type={item.review_type!r})",
                details={"review_item_id": str(review_item_id)},
            )

        if item.entity_type != "source":
            raise ValidationFailedError(
                f"review_item {review_item_id} does not belong to a source "
                f"(entity_type={item.entity_type!r})",
                details={"review_item_id": str(review_item_id)},
            )

        current = ReviewItemStatus(item.status)
        allowed = REVIEW_ITEM_STATUS_TRANSITIONS.get(current, set())
        if ReviewItemStatus.APPROVED not in allowed:
            raise InvalidStateTransitionError(
                f"review_item {review_item_id}: cannot transition from {current.value} to approved",
                details={"from": current.value, "to": "approved"},
            )

        try:
            validate_rights_resolution(rights_status, access_policy)
        except ValueError as exc:
            raise ValidationFailedError(str(exc), details={"review_item_id": str(review_item_id)}) from exc

        source = await self._source_repo.get_by_id(item.entity_id)
        if source is None:
            raise NotFoundError(f"source {item.entity_id} not found")

        # --- validation complete; only mutation from here on ---

        before_item = {"status": item.status, "decision_reason": item.decision_reason}
        item.status = ReviewItemStatus.APPROVED.value
        item.decision_reason = decision_reason
        item.decided_at = datetime.now(UTC)

        before_source = {
            "rights_status": source.rights_status,
            "access_policy": source.access_policy,
            "tdm_opt_out_status": source.tdm_opt_out_status,
            "licence_name": source.licence_name,
            "licence_url": source.licence_url,
        }
        source.rights_status = rights_status.value
        source.access_policy = access_policy.value
        if tdm_opt_out_status is not None:
            source.tdm_opt_out_status = tdm_opt_out_status.value
        if licence_name is not None:
            source.licence_name = licence_name
        if licence_url is not None:
            source.licence_url = licence_url

        # A rights outcome of blocked/blocked is a takedown, not merely a
        # policy note: the source's lifecycle status must move to BLOCKED in
        # the same transaction, or a fetch/publish could race ahead of a
        # rights decision that already forbids it. Only auto-transition when
        # the current status can legally reach BLOCKED (it already can from
        # any live state); a source that is already blocked or in a terminal
        # state (rejected/superseded/archived) is left as-is.
        blocked_status_before = source.status
        auto_blocked = False
        if rights_status == RightsStatus.BLOCKED and access_policy == AccessPolicy.BLOCKED:
            current_source_status = SourceStatus(source.status)
            if current_source_status != SourceStatus.BLOCKED and SourceStatus.BLOCKED in (
                SOURCE_STATUS_TRANSITIONS.get(current_source_status, set())
            ):
                source.status = SourceStatus.BLOCKED.value
                auto_blocked = True

        await self._session.flush()

        if auto_blocked:
            self._audit.record(
                actor_type="system",
                actor_id=actor_id,
                action="source.status_transition",
                entity_type="source",
                entity_id=source.id,
                before_state={"status": blocked_status_before},
                after_state={
                    "status": source.status,
                    "reason": "auto-blocked: rights review resolved to blocked/blocked",
                },
            )

        self._audit.record(
            actor_type="api_key",
            actor_id=actor_id,
            action="review_item.rights_decision",
            entity_type="review_item",
            entity_id=item.id,
            before_state=before_item,
            after_state={"status": item.status, "decision_reason": item.decision_reason},
        )
        self._audit.record(
            actor_type="api_key",
            actor_id=actor_id,
            action="source.rights_reviewed",
            entity_type="source",
            entity_id=source.id,
            before_state={k: (v or "") for k, v in before_source.items()},
            after_state={
                "rights_status": source.rights_status,
                "access_policy": source.access_policy,
                "tdm_opt_out_status": source.tdm_opt_out_status,
                "licence_name": source.licence_name or "",
                "licence_url": source.licence_url or "",
                "review_item_id": str(item.id),
            },
        )

        return item, source

    async def list(
        self, *, filters: ReviewItemFilters, limit: int, offset: int
    ) -> tuple[list[ReviewItem], int]:
        return await self._repo.list_page(filters=filters, limit=limit, offset=offset)
