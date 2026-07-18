"""Thin CRUD for sources and source_snapshots. No business rules here."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from de_ai_kb.db.models.sources import Source, SourceQualityEvaluation, SourceSnapshot


@dataclass
class SourceFilters:
    tier: str | None = None
    source_type: str | None = None
    topic: str | None = None
    publisher: str | None = None
    language_code: str | None = None
    status: str | None = None


class SourceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, source_id: uuid.UUID) -> Source | None:
        return await self._session.get(Source, source_id)

    async def get_by_source_key(self, source_key: str) -> Source | None:
        result = await self._session.execute(select(Source).where(Source.source_key == source_key))
        return result.scalar_one_or_none()

    async def get_by_canonical_url(self, canonical_url: str) -> list[Source]:
        result = await self._session.execute(
            select(Source).where(Source.canonical_url == canonical_url)
        )
        return list(result.scalars().all())

    def _apply_filters(self, stmt: Select[Any], filters: SourceFilters) -> Select[Any]:
        if filters.tier:
            stmt = stmt.where(Source.tier == filters.tier)
        if filters.source_type:
            stmt = stmt.where(Source.source_type == filters.source_type)
        if filters.topic:
            stmt = stmt.where(Source.topic_tags.any(filters.topic))  # type: ignore[arg-type]
        if filters.publisher:
            stmt = stmt.where(Source.publisher.ilike(f"%{filters.publisher}%"))
        if filters.language_code:
            stmt = stmt.where(Source.language_code == filters.language_code)
        if filters.status:
            stmt = stmt.where(Source.status == filters.status)
        return stmt

    async def list_page(
        self, *, filters: SourceFilters, limit: int, offset: int
    ) -> tuple[list[Source], int]:
        base_stmt = self._apply_filters(select(Source), filters)
        count_stmt = self._apply_filters(select(func.count()).select_from(Source), filters)
        total = (await self._session.execute(count_stmt)).scalar_one()
        result = await self._session.execute(
            base_stmt.order_by(Source.created_at.desc(), Source.id).limit(limit).offset(offset)
        )
        return list(result.scalars().all()), total

    async def list_all(self) -> list[Source]:
        result = await self._session.execute(select(Source))
        return list(result.scalars().all())

    def add(self, source: Source) -> None:
        self._session.add(source)

    async def flush(self) -> None:
        await self._session.flush()


class SourceQualityEvaluationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, evaluation: SourceQualityEvaluation) -> None:
        self._session.add(evaluation)

    async def list_for_source(self, source_id: uuid.UUID) -> list[SourceQualityEvaluation]:
        result = await self._session.execute(
            select(SourceQualityEvaluation)
            .where(SourceQualityEvaluation.source_id == source_id)
            .order_by(SourceQualityEvaluation.evaluated_at.desc())
        )
        return list(result.scalars().all())


class SourceSnapshotRepository:
    """Deliberately exposes no update() — snapshots are immutable by policy
    and by a DB trigger (defense in depth, see prevent_snapshot_update())."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, snapshot: SourceSnapshot) -> None:
        self._session.add(snapshot)

    async def get_by_id(self, snapshot_id: uuid.UUID) -> SourceSnapshot | None:
        return await self._session.get(SourceSnapshot, snapshot_id)

    async def list_for_source(self, source_id: uuid.UUID) -> list[SourceSnapshot]:
        result = await self._session.execute(
            select(SourceSnapshot)
            .where(SourceSnapshot.source_id == source_id)
            .order_by(SourceSnapshot.retrieved_at.desc())
        )
        return list(result.scalars().all())
