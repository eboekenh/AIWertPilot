"""Thin CRUD for business_processes (the only taxonomy table seeded this release)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from de_ai_kb.db.models.taxonomy import BusinessProcess


class BusinessProcessRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_slug(self, slug: str) -> BusinessProcess | None:
        result = await self._session.execute(select(BusinessProcess).where(BusinessProcess.slug == slug))
        return result.scalar_one_or_none()

    def add(self, process: BusinessProcess) -> None:
        self._session.add(process)

    async def list_all(self) -> list[BusinessProcess]:
        result = await self._session.execute(select(BusinessProcess).order_by(BusinessProcess.name))
        return list(result.scalars().all())
