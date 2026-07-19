"""Source registry business rules: creation, update, status transitions,
rights defaults, and the takedown/block mechanism.

Policy enforcement lives here, not in routers/CLI commands, and not assumed
to be fully covered by DB constraints alone — constraints are the last line
of defense.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from de_ai_kb.core.exceptions import (
    DuplicateSourceError,
    InvalidStateTransitionError,
    NotFoundError,
    ValidationFailedError,
)
from de_ai_kb.db.models.sources import Source
from de_ai_kb.domain.enums import (
    SOURCE_STATUS_TRANSITIONS,
    AccessPolicy,
    RightsStatus,
    SourceStatus,
)
from de_ai_kb.domain.url import canonicalize_url
from de_ai_kb.repositories.sources import SourceFilters, SourceRepository
from de_ai_kb.services.audit import AuditService
from de_ai_kb.services.review import ReviewService

# Fields a generic PATCH may edit. Deliberately excludes status,
# rights_status, access_policy, tdm_opt_out_status, and licence_*: those are
# governed invariants with their own dedicated workflows (transition_status,
# block_source, ReviewService.resolve_rights_review), not free-form
# metadata. Enforced here — not just at the Pydantic/API layer — so a
# direct service call (from a future CLI command, script, or test) gets the
# same protection as the HTTP API.
EDITABLE_SOURCE_FIELDS: frozenset[str] = frozenset(
    {"title", "publisher", "tier", "topic_tags", "refresh_interval_days", "notes"}
)


class SourceRegistryService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = SourceRepository(session)
        self._audit = AuditService(session)
        self._review = ReviewService(session)

    async def create_source(
        self,
        *,
        source_key: str,
        title: str,
        publisher: str,
        original_url: str,
        source_type: str,
        tier: str,
        language_code: str = "de",
        geography_codes: list[str] | None = None,
        jurisdiction_codes: list[str] | None = None,
        topic_tags: list[str] | None = None,
        access_policy: AccessPolicy = AccessPolicy.METADATA_ONLY,
        rights_status: RightsStatus = RightsStatus.NEEDS_REVIEW,
        refresh_interval_days: int = 90,
        notes: str | None = None,
        status: SourceStatus = SourceStatus.REGISTERED,
        actor_id: str,
    ) -> Source:
        canonical_url = canonicalize_url(original_url)
        existing_by_key = await self._repo.get_by_source_key(source_key)
        if existing_by_key is not None:
            raise DuplicateSourceError(
                f"source_key {source_key!r} already registered",
                details={"existing_id": str(existing_by_key.id)},
            )
        existing_by_url = await self._repo.get_by_canonical_url(canonical_url)
        exact_publisher_match = [s for s in existing_by_url if s.publisher == publisher]
        if exact_publisher_match:
            raise DuplicateSourceError(
                f"canonical_url {canonical_url!r} already registered for publisher {publisher!r}",
                details={"existing_id": str(exact_publisher_match[0].id)},
            )

        source = Source(
            source_key=source_key,
            title=title,
            publisher=publisher,
            original_url=original_url,
            canonical_url=canonical_url,
            source_type=source_type,
            tier=tier,
            language_code=language_code,
            geography_codes=geography_codes or [],
            jurisdiction_codes=jurisdiction_codes or [],
            topic_tags=topic_tags or [],
            access_policy=access_policy.value,
            rights_status=rights_status.value,
            refresh_interval_days=refresh_interval_days,
            notes=notes,
            status=status.value,
        )
        self._repo.add(source)
        await self._session.flush()
        self._audit.record(
            actor_type="api_key" if actor_id != "cli" else "cli",
            actor_id=actor_id,
            action="source.created",
            entity_type="source",
            entity_id=source.id,
            after_state={"source_key": source_key, "canonical_url": canonical_url, "status": source.status},
        )

        # Every newly registered source, regardless of caller (API, CSV
        # import, or any future entry point), gets exactly one open
        # rights_review and one open content_review item. Centralized here
        # so the invariant cannot be forgotten by a new caller — see
        # docs/RESEARCH_WORKFLOW.md.
        await self._review.create_standard_source_review_items(source_id=source.id, actor_id=actor_id)

        return source

    async def update_source(self, *, source_id: uuid.UUID, updates: dict[str, Any], actor_id: str) -> Source:
        unknown_or_protected = set(updates) - EDITABLE_SOURCE_FIELDS
        if unknown_or_protected:
            raise ValidationFailedError(
                "update_source received field(s) that are not generic editable metadata; "
                "use the transition/block/rights-decision workflows instead",
                details={"rejected_fields": sorted(unknown_or_protected)},
            )

        source = await self._repo.get_by_id(source_id)
        if source is None:
            raise NotFoundError(f"source {source_id} not found")

        before = {k: getattr(source, k) for k in updates}
        for key, value in updates.items():
            setattr(source, key, value)
        await self._session.flush()
        self._audit.record(
            actor_type="api_key",
            actor_id=actor_id,
            action="source.updated",
            entity_type="source",
            entity_id=source.id,
            before_state={k: str(v) for k, v in before.items()},
            after_state={k: str(v) for k, v in updates.items()},
        )
        return source

    async def transition_status(
        self, *, source_id: uuid.UUID, new_status: SourceStatus, reason: str | None, actor_id: str
    ) -> Source:
        source = await self._repo.get_by_id(source_id)
        if source is None:
            raise NotFoundError(f"source {source_id} not found")

        current = SourceStatus(source.status)
        allowed = SOURCE_STATUS_TRANSITIONS.get(current, set())
        if new_status not in allowed:
            raise InvalidStateTransitionError(
                f"source {source_id}: cannot transition from {current.value} to {new_status.value}",
                details={"from": current.value, "to": new_status.value},
            )

        before_status = source.status
        source.status = new_status.value
        await self._session.flush()
        self._audit.record(
            actor_type="api_key",
            actor_id=actor_id,
            action="source.status_transition",
            entity_type="source",
            entity_id=source.id,
            before_state={"status": before_status},
            after_state={"status": source.status, "reason": reason},
        )
        return source

    async def block_source(self, *, source_id: uuid.UUID, reason: str, actor_id: str) -> Source:
        """Takedown/block mechanism. The reason is mandatory and always
        retained in the audit trail, per RESEARCH_PROTOCOL.md §10."""
        if not reason.strip():
            raise ValidationFailedError("a non-blank block reason is required")
        return await self.transition_status(
            source_id=source_id, new_status=SourceStatus.BLOCKED, reason=reason, actor_id=actor_id
        )

    async def list(self, *, filters: SourceFilters, limit: int, offset: int) -> tuple[list[Source], int]:
        return await self._repo.list_page(filters=filters, limit=limit, offset=offset)

    async def get_by_id(self, source_id: uuid.UUID) -> Source | None:
        return await self._repo.get_by_id(source_id)

    async def get_by_source_key(self, source_key: str) -> Source | None:
        return await self._repo.get_by_source_key(source_key)
