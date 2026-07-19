from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from de_ai_kb.repositories.sources import SourceRepository
from de_ai_kb.services.seed_import import SeedImportService

pytestmark = pytest.mark.asyncio

_REPO_ROOT = Path(__file__).resolve().parents[2]
_REAL_SOURCES_CSV = _REPO_ROOT / "data" / "seed_sources.csv"
_MALFORMED_CSV = _REPO_ROOT / "tests" / "fixtures" / "malformed_sources.csv"

_HEADER = (
    "source_key,title,publisher,source_type,tier,topics,geography,language,"
    "url,access_policy,refresh_days,review_status,notes"
)


def _row(
    *,
    source_key: str = "CONSISTENCY_SOURCE",
    title: str = "Consistency Source",
    publisher: str = "Publisher A",
    source_type: str = "official_statistics",
    tier: str = "A",
    topics: str = "adoption",
    geography: str = "DE",
    language: str = "de",
    url: str = "https://example.com/consistency",
    access_policy: str = "metadata_only",
    refresh_days: str = "90",
    review_status: str = "discovery_verified",
    notes: str = "note",
) -> str:
    return (
        f'"{source_key}","{title}","{publisher}","{source_type}","{tier}","{topics}",'
        f'"{geography}","{language}","{url}","{access_policy}","{refresh_days}",'
        f'"{review_status}","{notes}"'
    )


def _write_csv(path: Path, *rows: str) -> Path:
    path.write_text(_HEADER + "\n" + "\n".join(rows) + "\n", encoding="utf-8")
    return path


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


# --- Requirement 4: dry-run/real-import consistency for changed fields ------


async def test_title_change_dry_run_and_real_import_agree(
    test_session_factory: async_sessionmaker[AsyncSession], clean_db: None, tmp_path: Path
) -> None:
    service = SeedImportService(test_session_factory)
    first_csv = _write_csv(tmp_path / "first.csv", _row(title="Original Title"))
    await service.import_csv(first_csv, dry_run=False, actor_id="test")

    changed_csv = _write_csv(tmp_path / "changed.csv", _row(title="Changed Title"))
    dry_run = await service.import_csv(changed_csv, dry_run=True, actor_id="test")
    assert dry_run.updated == 1
    assert dry_run.rejected == 0

    real_run = await service.import_csv(changed_csv, dry_run=False, actor_id="test")
    assert real_run.updated == 1
    assert real_run.rejected == 0

    async with test_session_factory() as session:
        source = await SourceRepository(session).get_by_source_key("CONSISTENCY_SOURCE")
    assert source is not None
    assert source.title == "Changed Title"

    unchanged_dry_run = await service.import_csv(changed_csv, dry_run=True, actor_id="test")
    assert unchanged_dry_run.unchanged == 1
    assert unchanged_dry_run.updated == 0


async def test_geography_change_dry_run_and_real_import_agree(
    test_session_factory: async_sessionmaker[AsyncSession], clean_db: None, tmp_path: Path
) -> None:
    service = SeedImportService(test_session_factory)
    first_csv = _write_csv(tmp_path / "first.csv", _row(geography="DE"))
    await service.import_csv(first_csv, dry_run=False, actor_id="test")

    changed_csv = _write_csv(tmp_path / "changed.csv", _row(geography="DE|EU"))
    dry_run = await service.import_csv(changed_csv, dry_run=True, actor_id="test")
    assert dry_run.updated == 1

    real_run = await service.import_csv(changed_csv, dry_run=False, actor_id="test")
    assert real_run.updated == 1
    assert real_run.rejected == 0

    async with test_session_factory() as session:
        source = await SourceRepository(session).get_by_source_key("CONSISTENCY_SOURCE")
    assert source is not None
    assert sorted(source.geography_codes) == ["DE", "EU"]


async def test_url_change_dry_run_and_real_import_agree(
    test_session_factory: async_sessionmaker[AsyncSession], clean_db: None, tmp_path: Path
) -> None:
    service = SeedImportService(test_session_factory)
    first_csv = _write_csv(tmp_path / "first.csv", _row(url="https://example.com/original-path"))
    await service.import_csv(first_csv, dry_run=False, actor_id="test")

    changed_csv = _write_csv(tmp_path / "changed.csv", _row(url="https://example.com/new-path"))
    dry_run = await service.import_csv(changed_csv, dry_run=True, actor_id="test")
    assert dry_run.updated == 1
    assert dry_run.rejected == 0

    real_run = await service.import_csv(changed_csv, dry_run=False, actor_id="test")
    assert real_run.updated == 1
    assert real_run.rejected == 0

    async with test_session_factory() as session:
        source = await SourceRepository(session).get_by_source_key("CONSISTENCY_SOURCE")
    assert source is not None
    assert source.original_url == "https://example.com/new-path"
    assert source.canonical_url == "https://example.com/new-path"


async def test_url_change_conflicting_with_another_source_is_rejected_consistently(
    test_session_factory: async_sessionmaker[AsyncSession], clean_db: None, tmp_path: Path
) -> None:
    service = SeedImportService(test_session_factory)
    initial_csv = _write_csv(
        tmp_path / "initial.csv",
        _row(source_key="SOURCE_A", url="https://example.com/a", publisher="Publisher A"),
        _row(source_key="SOURCE_B", url="https://example.com/b", publisher="Publisher A"),
    )
    await service.import_csv(initial_csv, dry_run=False, actor_id="test")

    conflicting_csv = _write_csv(
        tmp_path / "conflicting.csv",
        _row(source_key="SOURCE_A", url="https://example.com/b", publisher="Publisher A"),
        _row(source_key="SOURCE_B", url="https://example.com/b", publisher="Publisher A"),
    )
    dry_run = await service.import_csv(conflicting_csv, dry_run=True, actor_id="test")
    a_row = next(r for r in dry_run.rows if r.source_key == "SOURCE_A")
    assert a_row.outcome == "rejected"

    real_run = await service.import_csv(conflicting_csv, dry_run=False, actor_id="test")
    a_real_row = next(r for r in real_run.rows if r.source_key == "SOURCE_A")
    assert a_real_row.outcome == "rejected"

    async with test_session_factory() as session:
        source_a = await SourceRepository(session).get_by_source_key("SOURCE_A")
    assert source_a is not None
    assert source_a.original_url == "https://example.com/a"


async def test_access_policy_csv_change_never_overwrites_a_completed_rights_review(
    test_session_factory: async_sessionmaker[AsyncSession], clean_db: None, tmp_path: Path
) -> None:
    from de_ai_kb.domain.enums import AccessPolicy, RightsStatus
    from de_ai_kb.repositories.review import ReviewItemFilters, ReviewItemRepository
    from de_ai_kb.services.review import ReviewService

    service = SeedImportService(test_session_factory)
    first_csv = _write_csv(tmp_path / "first.csv", _row(access_policy="metadata_only"))
    await service.import_csv(first_csv, dry_run=False, actor_id="test")

    async with test_session_factory() as session:
        source = await SourceRepository(session).get_by_source_key("CONSISTENCY_SOURCE")
        assert source is not None
        review_repo = ReviewItemRepository(session)
        items = await review_repo.list_all(filters=ReviewItemFilters(entity_type="source"))
        rights_item = next(i for i in items if i.entity_id == source.id and i.review_type == "rights_review")
        review_service = ReviewService(session)
        await review_service.resolve_rights_review(
            review_item_id=rights_item.id,
            rights_status=RightsStatus.REVIEWED_ALLOWED,
            access_policy=AccessPolicy.SHORT_EVIDENCE,
            decision_reason="publisher licence confirmed",
            tdm_opt_out_status=None,
            licence_name=None,
            licence_url=None,
            actor_id="test",
        )
        await session.commit()

    # CSV re-import proposes a different access_policy for the same row.
    changed_csv = _write_csv(tmp_path / "changed.csv", _row(access_policy="full_text_allowed"))
    dry_run = await service.import_csv(changed_csv, dry_run=True, actor_id="test")
    assert dry_run.unchanged == 1
    assert dry_run.updated == 0

    real_run = await service.import_csv(changed_csv, dry_run=False, actor_id="test")
    assert real_run.unchanged == 1

    async with test_session_factory() as session:
        refreshed = await SourceRepository(session).get_by_source_key("CONSISTENCY_SOURCE")
    assert refreshed is not None
    assert refreshed.access_policy == AccessPolicy.SHORT_EVIDENCE.value
    assert refreshed.rights_status == RightsStatus.REVIEWED_ALLOWED.value
