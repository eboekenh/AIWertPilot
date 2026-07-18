"""Idempotent seeding of the business_processes reference vocabulary."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from de_ai_kb.db.models.taxonomy import BusinessProcess
from de_ai_kb.domain.slugify import slugify
from de_ai_kb.domain.taxonomy_seed_data import BUSINESS_PROCESSES
from de_ai_kb.repositories.taxonomy import BusinessProcessRepository


class TaxonomySeedService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = BusinessProcessRepository(session)

    async def seed_business_processes(self) -> tuple[int, int]:
        """Returns (inserted, unchanged)."""
        inserted = 0
        unchanged = 0
        for name in BUSINESS_PROCESSES:
            slug = slugify(name)
            existing = await self._repo.get_by_slug(slug)
            if existing is not None:
                unchanged += 1
                continue
            self._repo.add(BusinessProcess(name=name, slug=slug))
            await self._session.flush()
            inserted += 1
        return inserted, unchanged
