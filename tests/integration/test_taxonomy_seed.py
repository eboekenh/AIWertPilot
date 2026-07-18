import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from de_ai_kb.domain.taxonomy_seed_data import BUSINESS_PROCESSES
from de_ai_kb.repositories.taxonomy import BusinessProcessRepository
from de_ai_kb.services.taxonomy_seed import TaxonomySeedService

pytestmark = pytest.mark.asyncio


async def test_seed_business_processes_inserts_19(db_session: AsyncSession) -> None:
    service = TaxonomySeedService(db_session)
    inserted, unchanged = await service.seed_business_processes()
    await db_session.commit()

    assert inserted == 19
    assert unchanged == 0
    assert len(BUSINESS_PROCESSES) == 19

    all_processes = await BusinessProcessRepository(db_session).list_all()
    assert len(all_processes) == 19


async def test_seed_business_processes_is_idempotent(db_session: AsyncSession) -> None:
    service = TaxonomySeedService(db_session)
    await service.seed_business_processes()
    await db_session.commit()

    inserted, unchanged = await service.seed_business_processes()
    await db_session.commit()
    assert inserted == 0
    assert unchanged == 19
