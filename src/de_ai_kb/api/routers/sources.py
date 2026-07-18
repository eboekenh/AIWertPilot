"""GET/POST /api/v1/sources, GET/PATCH /api/v1/sources/{id}."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from de_ai_kb.api.deps import ApiKeyActorDep, SessionDep
from de_ai_kb.api.schemas.common import Page
from de_ai_kb.api.schemas.sources import SourceCreate, SourceRead, SourceUpdate
from de_ai_kb.core.exceptions import NotFoundError
from de_ai_kb.domain.enums import FreshnessState, SourceStatus
from de_ai_kb.domain.freshness import compute_freshness_state
from de_ai_kb.repositories.sources import SourceFilters
from de_ai_kb.services.source_registry import SourceRegistryService

router = APIRouter(prefix="/api/v1/sources", tags=["sources"])


@router.get("", response_model=Page[SourceRead])
async def list_sources(
    session: SessionDep,
    tier: str | None = None,
    source_type: str | None = None,
    topic: str | None = None,
    publisher: str | None = None,
    language: str | None = None,
    status: str | None = None,
    freshness: str | None = Query(default=None, description="fresh|due_soon|stale|unknown"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> Page[SourceRead]:
    service = SourceRegistryService(session)
    filters = SourceFilters(
        tier=tier, source_type=source_type, topic=topic, publisher=publisher,
        language_code=language, status=status,
    )
    if freshness:
        from datetime import UTC
        from datetime import datetime as _dt

        wanted = FreshnessState(freshness)
        all_sources, _ = await service.list(filters=filters, limit=10_000, offset=0)
        now = _dt.now(UTC)
        matched = [
            s for s in all_sources
            if compute_freshness_state(
                last_verified_at=s.last_verified_at, refresh_interval_days=s.refresh_interval_days, now=now
            ) == wanted
        ]
        total = len(matched)
        page_items = matched[offset : offset + limit]
        return Page(
            items=[SourceRead.model_validate(s) for s in page_items], total=total, limit=limit, offset=offset
        )

    items, total = await service.list(filters=filters, limit=limit, offset=offset)
    return Page(
        items=[SourceRead.model_validate(s) for s in items], total=total, limit=limit, offset=offset
    )


@router.post("", response_model=SourceRead, status_code=201)
async def create_source(payload: SourceCreate, session: SessionDep, actor: ApiKeyActorDep) -> SourceRead:
    service = SourceRegistryService(session)
    source = await service.create_source(
        source_key=payload.source_key,
        title=payload.title,
        publisher=payload.publisher,
        original_url=payload.original_url,
        source_type=payload.source_type,
        tier=payload.tier.value,
        language_code=payload.language_code,
        geography_codes=payload.geography_codes,
        jurisdiction_codes=payload.jurisdiction_codes,
        topic_tags=payload.topic_tags,
        access_policy=payload.access_policy,
        rights_status=payload.rights_status,
        refresh_interval_days=payload.refresh_interval_days,
        notes=payload.notes,
        status=SourceStatus.REGISTERED,
        actor_id=actor,
    )
    return SourceRead.model_validate(source)


@router.get("/{source_id}", response_model=SourceRead)
async def get_source(source_id: uuid.UUID, session: SessionDep) -> SourceRead:
    service = SourceRegistryService(session)
    source = await service.get_by_id(source_id)
    if source is None:
        raise NotFoundError(f"source {source_id} not found")
    return SourceRead.model_validate(source)


@router.patch("/{source_id}", response_model=SourceRead)
async def update_source(
    source_id: uuid.UUID, payload: SourceUpdate, session: SessionDep, actor: ApiKeyActorDep
) -> SourceRead:
    service = SourceRegistryService(session)
    updates = payload.model_dump(exclude_unset=True)
    for enum_field in ("tier", "access_policy", "rights_status", "status"):
        value = updates.get(enum_field)
        if value is not None:
            updates[enum_field] = value.value if hasattr(value, "value") else value
    source = await service.update_source(source_id=source_id, updates=updates, actor_id=actor)
    return SourceRead.model_validate(source)
