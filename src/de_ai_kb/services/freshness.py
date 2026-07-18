"""Freshness reporting: wraps domain.freshness (pure) with real source data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from de_ai_kb.domain.enums import FreshnessState
from de_ai_kb.domain.freshness import compute_freshness_state
from de_ai_kb.repositories.sources import SourceFilters, SourceRepository


@dataclass
class FreshnessReportItem:
    source_id: UUID
    source_key: str
    title: str
    status: str
    last_verified_at: datetime | None
    refresh_interval_days: int
    freshness_state: FreshnessState


class FreshnessService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = SourceRepository(session)

    async def report(self, *, state_filter: FreshnessState | None = None) -> list[FreshnessReportItem]:
        sources = await self._repo.list_page(filters=SourceFilters(), limit=10_000, offset=0)
        now = datetime.now(UTC)
        items = []
        for source in sources[0]:
            state = compute_freshness_state(
                last_verified_at=source.last_verified_at,
                refresh_interval_days=source.refresh_interval_days,
                now=now,
            )
            if state_filter is not None and state != state_filter:
                continue
            items.append(
                FreshnessReportItem(
                    source_id=source.id,
                    source_key=source.source_key,
                    title=source.title,
                    status=source.status,
                    last_verified_at=source.last_verified_at,
                    refresh_interval_days=source.refresh_interval_days,
                    freshness_state=state,
                )
            )
        return items
