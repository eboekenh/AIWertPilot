"""Thin CRUD for review_items."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from de_ai_kb.db.models.ops import ReviewItem


@dataclass
class ReviewItemFilters:
    status: str | None = None
    review_type: str | None = None
    entity_type: str | None = None


class ReviewItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, item: ReviewItem) -> None:
        self._session.add(item)

    async def get_by_id(self, item_id: uuid.UUID) -> ReviewItem | None:
        return await self._session.get(ReviewItem, item_id)

    async def get_open(
        self, *, entity_type: str, entity_id: uuid.UUID, review_type: str
    ) -> ReviewItem | None:
        result = await self._session.execute(
            select(ReviewItem).where(
                ReviewItem.entity_type == entity_type,
                ReviewItem.entity_id == entity_id,
                ReviewItem.review_type == review_type,
                ReviewItem.status == "open",
            )
        )
        return result.scalar_one_or_none()

    def _apply_filters(self, stmt: Select[Any], filters: ReviewItemFilters) -> Select[Any]:
        if filters.status:
            stmt = stmt.where(ReviewItem.status == filters.status)
        if filters.review_type:
            stmt = stmt.where(ReviewItem.review_type == filters.review_type)
        if filters.entity_type:
            stmt = stmt.where(ReviewItem.entity_type == filters.entity_type)
        return stmt

    async def list_page(
        self, *, filters: ReviewItemFilters, limit: int, offset: int
    ) -> tuple[list[ReviewItem], int]:
        base_stmt = self._apply_filters(select(ReviewItem), filters)
        count_stmt = self._apply_filters(select(func.count()).select_from(ReviewItem), filters)
        total = (await self._session.execute(count_stmt)).scalar_one()
        result = await self._session.execute(
            base_stmt.order_by(
                ReviewItem.priority, ReviewItem.created_at
            ).limit(limit).offset(offset)
        )
        return list(result.scalars().all()), total

    async def list_all(self, *, filters: ReviewItemFilters | None = None) -> list[ReviewItem]:
        stmt: Select[Any] = select(ReviewItem)
        if filters:
            stmt = self._apply_filters(stmt, filters)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
