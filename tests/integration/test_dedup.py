import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from de_ai_kb.services.dedup import DuplicateDetectionService
from de_ai_kb.services.source_registry import SourceRegistryService

pytestmark = pytest.mark.asyncio


async def _seed_sources(session: AsyncSession) -> None:
    service = SourceRegistryService(session)
    await service.create_source(
        source_key="DEDUP_A",
        title="Use of artificial intelligence by German companies",
        publisher="Destatis",
        original_url="https://example.com/a",
        source_type="official_statistics",
        tier="A",
        refresh_interval_days=90,
        actor_id="test",
    )
    # near-duplicate title, same publisher
    await service.create_source(
        source_key="DEDUP_B",
        title="Use of artificial intelligence by German companies (2026)",
        publisher="Destatis",
        original_url="https://example.com/b",
        source_type="official_statistics",
        tier="A",
        refresh_interval_days=90,
        actor_id="test",
    )
    # same canonical URL, different publisher label
    await service.create_source(
        source_key="DEDUP_C",
        title="Completely unrelated title",
        publisher="Other Publisher",
        original_url="https://example.com/a",
        source_type="official_statistics",
        tier="A",
        refresh_interval_days=90,
        actor_id="test",
    )
    # unrelated source, should not match anything
    await service.create_source(
        source_key="DEDUP_D",
        title="Barriers to the use of artificial intelligence",
        publisher="Bitkom",
        original_url="https://example.com/d",
        source_type="industry_report",
        tier="C",
        refresh_interval_days=180,
        actor_id="test",
    )
    await session.commit()


async def test_dedup_scan_finds_title_and_url_candidates(db_session: AsyncSession) -> None:
    await _seed_sources(db_session)
    service = DuplicateDetectionService(db_session)
    candidates = await service.scan_all(actor_id="test")
    await db_session.commit()

    reasons = {c.reason for c in candidates}
    assert "title_similarity" in reasons
    assert "canonical_url_match" in reasons
    # No merge ever happens: still exactly 4 sources in the registry.
    from de_ai_kb.repositories.sources import SourceRepository

    all_sources = await SourceRepository(db_session).list_all()
    assert len(all_sources) == 4


async def test_dedup_scan_is_idempotent(db_session: AsyncSession) -> None:
    await _seed_sources(db_session)
    service = DuplicateDetectionService(db_session)
    first = await service.scan_all(actor_id="test")
    await db_session.commit()
    second = await service.scan_all(actor_id="test")
    await db_session.commit()

    from de_ai_kb.repositories.review import ReviewItemFilters, ReviewItemRepository

    review_repo = ReviewItemRepository(db_session)
    dedup_items = await review_repo.list_all(
        filters=ReviewItemFilters(review_type="dedup_candidate")
    )
    # find_candidates still reports the same pairs on a re-scan (the
    # underlying source data hasn't changed), but no *additional*
    # review_items are created — the UNIQUE(entity_type, entity_id,
    # review_type, status) constraint allows only one open dedup_candidate
    # item per source, and create_dedup_candidate is a no-op when one
    # already exists. This is what makes repeated scans idempotent.
    assert len(second) == len(first)
    assert len(dedup_items) == len({c.source_id for c in first})
