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

# Fields the trusted seed-import workflow may edit (update_source_from_seed).
# A superset of EDITABLE_SOURCE_FIELDS: re-importing seed_sources.csv may
# also correct descriptive/identifying metadata that a generic API PATCH may
# not touch (source_type, language_code, geography_codes, and the URL pair).
# Still excludes status/rights_status/access_policy/tdm_opt_out_status/
# licence_* for the same reason as EDITABLE_SOURCE_FIELDS — a CSV re-import
# must never silently overwrite a completed rights review or lifecycle
# state. Must stay in sync with everything services.seed_import._diff_fields
# can produce.
SEED_UPDATABLE_FIELDS: frozenset[str] = EDITABLE_SOURCE_FIELDS | frozenset(
    {"source_type", "language_code", "geography_codes", "original_url", "canonical_url"}
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
        refresh_interval_days: int = 90,
        notes: str | None = None,
        actor_id: str,
        actor_type: str,
    ) -> Source:
        """Register a new source. Lifecycle status, rights_status, and
        access_policy are deliberately not caller-controllable parameters:
        every newly created source always starts at
        status=registered/rights_status=needs_review/
        access_policy=metadata_only, regardless of caller (API, CSV import,
        or any future entry point) — those governed fields can only change
        afterwards through transition_status/block_source/
        ReviewService.resolve_rights_review. This closes the creation-time
        bypass that letting a caller pass e.g. status=published or
        rights_status=reviewed_allowed at creation would otherwise open."""
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
            access_policy=AccessPolicy.METADATA_ONLY.value,
            rights_status=RightsStatus.NEEDS_REVIEW.value,
            refresh_interval_days=refresh_interval_days,
            notes=notes,
            status=SourceStatus.REGISTERED.value,
        )
        self._repo.add(source)
        await self._session.flush()
        self._audit.record(
            actor_type=actor_type,
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

    async def update_source(
        self, *, source_id: uuid.UUID, updates: dict[str, Any], actor_id: str, actor_type: str
    ) -> Source:
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
            actor_type=actor_type,
            actor_id=actor_id,
            action="source.updated",
            entity_type="source",
            entity_id=source.id,
            before_state={k: str(v) for k, v in before.items()},
            after_state={k: str(v) for k, v in updates.items()},
        )
        return source

    async def update_source_from_seed(
        self, *, source_id: uuid.UUID, updates: dict[str, Any], actor_id: str, actor_type: str
    ) -> Source:
        """Trusted seed-import update path (SeedImportService only). Allows a
        wider field set than the API-facing update_source() — source_type,
        language_code, geography_codes, original_url, and canonical_url —
        matching exactly what services.seed_import._diff_fields() can
        produce, so a dry-run "would update" prediction and the real import
        agree. Still excludes status/rights_status/access_policy/
        tdm_opt_out_status/licence_*: even a trusted CSV re-import must not
        silently overwrite a completed rights review or lifecycle state —
        those still require transition_status/block_source/
        ReviewService.resolve_rights_review."""
        unknown_or_protected = set(updates) - SEED_UPDATABLE_FIELDS
        if unknown_or_protected:
            raise ValidationFailedError(
                "update_source_from_seed received field(s) outside the trusted seed-update "
                "allowlist; use the transition/block/rights-decision workflows instead",
                details={"rejected_fields": sorted(unknown_or_protected)},
            )

        source = await self._repo.get_by_id(source_id)
        if source is None:
            raise NotFoundError(f"source {source_id} not found")

        if "canonical_url" in updates and updates["canonical_url"] != source.canonical_url:
            new_publisher = updates.get("publisher", source.publisher)
            conflicting = await self._repo.get_by_canonical_url(updates["canonical_url"])
            conflict = [s for s in conflicting if s.id != source_id and s.publisher == new_publisher]
            if conflict:
                raise DuplicateSourceError(
                    f"canonical_url {updates['canonical_url']!r} already registered for "
                    f"publisher {new_publisher!r}",
                    details={"existing_id": str(conflict[0].id)},
                )

        before = {k: getattr(source, k) for k in updates}
        for key, value in updates.items():
            setattr(source, key, value)
        await self._session.flush()
        self._audit.record(
            actor_type=actor_type,
            actor_id=actor_id,
            action="source.updated",
            entity_type="source",
            entity_id=source.id,
            before_state={k: str(v) for k, v in before.items()},
            after_state={k: str(v) for k, v in updates.items()},
        )
        return source

    async def transition_status(
        self,
        *,
        source_id: uuid.UUID,
        new_status: SourceStatus,
        reason: str | None,
        actor_id: str,
        actor_type: str,
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

        # BLOCKED is a takedown, not an ordinary lifecycle step: a non-blank
        # reason is required in the service layer itself (not just at the
        # /block endpoint), so no caller — API, CLI, or a future direct
        # service call — can block a source without recording why.
        if new_status == SourceStatus.BLOCKED and not (reason or "").strip():
            raise ValidationFailedError("a non-blank reason is required to transition a source to blocked")

        await self._check_review_gates(source=source, new_status=new_status)

        before_status = source.status
        source.status = new_status.value
        await self._session.flush()
        self._audit.record(
            actor_type=actor_type,
            actor_id=actor_id,
            action="source.status_transition",
            entity_type="source",
            entity_id=source.id,
            before_state={"status": before_status},
            after_state={"status": source.status, "reason": reason},
        )
        return source

    async def _check_review_gates(self, *, source: Source, new_status: SourceStatus) -> None:
        """Enforce that a source cannot progress past registered without
        completing the review workflow. FETCHED requires an approved
        rights_review with a valid, non-blocked rights outcome; APPROVED and
        PUBLISHED require both rights_review and content_review approved
        (PUBLISHED re-runs the same check rather than trusting the earlier
        APPROVED transition, since rights/review state could in principle
        change in between)."""
        non_blocked_rights_outcomes = {
            RightsStatus.REVIEWED_ALLOWED.value,
            RightsStatus.REVIEWED_RESTRICTED.value,
        }

        if new_status in (SourceStatus.FETCHED, SourceStatus.APPROVED, SourceStatus.PUBLISHED):
            rights_approved = await self._review.is_rights_review_approved(source_id=source.id)
            if not rights_approved or source.rights_status not in non_blocked_rights_outcomes:
                raise ValidationFailedError(
                    f"source {source.id}: cannot transition to {new_status.value} without an "
                    "approved rights_review and a valid, non-blocked rights outcome",
                    details={"to": new_status.value},
                )

        if new_status in (SourceStatus.APPROVED, SourceStatus.PUBLISHED):
            content_approved = await self._review.is_content_review_approved(source_id=source.id)
            if not content_approved:
                raise ValidationFailedError(
                    f"source {source.id}: cannot transition to {new_status.value} without an "
                    "approved content_review",
                    details={"to": new_status.value},
                )

    async def block_source(
        self, *, source_id: uuid.UUID, reason: str, actor_id: str, actor_type: str
    ) -> Source:
        """Takedown/block mechanism. The reason is mandatory and always
        retained in the audit trail, per RESEARCH_PROTOCOL.md §10."""
        if not reason.strip():
            raise ValidationFailedError("a non-blank block reason is required")
        return await self.transition_status(
            source_id=source_id,
            new_status=SourceStatus.BLOCKED,
            reason=reason,
            actor_id=actor_id,
            actor_type=actor_type,
        )

    async def list(self, *, filters: SourceFilters, limit: int, offset: int) -> tuple[list[Source], int]:
        return await self._repo.list_page(filters=filters, limit=limit, offset=offset)

    async def get_by_id(self, source_id: uuid.UUID) -> Source | None:
        return await self._repo.get_by_id(source_id)

    async def get_by_source_key(self, source_key: str) -> Source | None:
        return await self._repo.get_by_source_key(source_key)
