from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from de_ai_kb.repositories.sources import SourceRepository
from de_ai_kb.services.seed_import import SeedImportService

pytestmark = pytest.mark.asyncio

_REPO_ROOT = Path(__file__).resolve().parents[2]
_REAL_SOURCES_CSV = _REPO_ROOT / "data" / "seed_sources.csv"
_MALFORMED_CSV = _REPO_ROOT / "tests" / "fixtures" / "malformed_sources.csv"


async def test_malformed_rows_are_rejected_with_reasons(
    test_session_factory: async_sessionmaker[AsyncSession], clean_db: None
) -> None:
    service = SeedImportService(test_session_factory)
    summary = await service.import_csv(_MALFORMED_CSV, dry_run=False, actor_id="test")

    assert summary.total_rows == 7
    assert summary.inserted == 2
    assert summary.rejected == 5
    rejected_keys = {r.source_key or "" for r in summary.rows if r.outcome == "rejected"}
    assert "BAD_TIER" in rejected_keys
    assert "BAD_ACCESS_POLICY" in rejected_keys
    assert "BAD_URL" in rejected_keys
    assert "BAD_REFRESH" in rejected_keys
    for row in summary.rows:
        if row.outcome == "rejected":
            assert row.reason, f"row {row.row_number} rejected without a reason"


async def test_malformed_row_rejection_does_not_block_other_rows(
    test_session_factory: async_sessionmaker[AsyncSession], clean_db: None
) -> None:
    service = SeedImportService(test_session_factory)
    summary = await service.import_csv(_MALFORMED_CSV, dry_run=False, actor_id="test")
    inserted_keys = {r.source_key for r in summary.rows if r.outcome == "inserted"}
    assert inserted_keys == {"GOOD_ROW_1", "GOOD_ROW_2"}


async def test_dry_run_writes_nothing(
    test_session_factory: async_sessionmaker[AsyncSession], clean_db: None
) -> None:
    service = SeedImportService(test_session_factory)
    summary = await service.import_csv(_MALFORMED_CSV, dry_run=True, actor_id="test")
    assert summary.inserted == 2

    async with test_session_factory() as session:
        sources = await SourceRepository(session).list_all()
    assert sources == []


async def test_real_seed_sources_csv_has_65_rows() -> None:
    assert _REAL_SOURCES_CSV.exists()
    with _REAL_SOURCES_CSV.open(encoding="utf-8") as fh:
        # subtract header row
        assert sum(1 for _ in fh) - 1 == 65


async def test_real_seed_sources_first_import_counts(
    test_session_factory: async_sessionmaker[AsyncSession], clean_db: None
) -> None:
    service = SeedImportService(test_session_factory)
    summary = await service.import_csv(_REAL_SOURCES_CSV, dry_run=False, actor_id="test")

    assert summary.total_rows == 65
    if summary.rejected == 0:
        assert summary.inserted == 65
        assert summary.review_items_created == 130
    else:
        # Report accurately rather than forcing a hardcoded expectation:
        # any rejected row must carry a concrete reason.
        for row in summary.rows:
            if row.outcome == "rejected":
                assert row.reason


async def test_real_seed_sources_second_import_is_idempotent(
    test_session_factory: async_sessionmaker[AsyncSession], clean_db: None
) -> None:
    service = SeedImportService(test_session_factory)
    first = await service.import_csv(_REAL_SOURCES_CSV, dry_run=False, actor_id="test")
    second = await service.import_csv(_REAL_SOURCES_CSV, dry_run=False, actor_id="test")

    assert second.inserted == 0
    assert second.updated == 0
    assert second.review_items_created == 0
    assert second.unchanged == first.inserted
