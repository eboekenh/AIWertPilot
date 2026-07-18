from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from de_ai_kb.db.models.evidence import Claim, ClaimEvidence
from de_ai_kb.services.claims_validation import ClaimsValidationService
from de_ai_kb.services.seed_import import SeedImportService

pytestmark = pytest.mark.asyncio

_REPO_ROOT = Path(__file__).resolve().parents[2]
_REAL_CLAIMS_CSV = _REPO_ROOT / "data" / "seed_claims.csv"
_REAL_SOURCES_CSV = _REPO_ROOT / "data" / "seed_sources.csv"


async def test_real_seed_claims_csv_has_38_rows() -> None:
    assert _REAL_CLAIMS_CSV.exists()
    with _REAL_CLAIMS_CSV.open(encoding="utf-8") as fh:
        assert sum(1 for _ in fh) - 1 == 38


async def test_claims_validation_writes_zero_rows(
    test_session_factory: async_sessionmaker[AsyncSession], clean_db: None
) -> None:
    import_service = SeedImportService(test_session_factory)
    await import_service.import_csv(_REAL_SOURCES_CSV, dry_run=False, actor_id="test")

    async with test_session_factory() as session:
        validation_service = ClaimsValidationService(session)
        summary = await validation_service.validate_csv(_REAL_CLAIMS_CSV)

    assert summary.total_rows == 38
    assert summary.claims_written == 0
    assert summary.claim_evidence_written == 0
    assert summary.duplicate_claim_keys == []

    async with test_session_factory() as session:
        claims = (await session.execute(select(Claim))).scalars().all()
        evidence = (await session.execute(select(ClaimEvidence))).scalars().all()
    assert len(claims) == 0
    assert len(evidence) == 0


async def test_claims_validation_reports_all_source_keys_resolved(
    test_session_factory: async_sessionmaker[AsyncSession], clean_db: None
) -> None:
    import_service = SeedImportService(test_session_factory)
    await import_service.import_csv(_REAL_SOURCES_CSV, dry_run=False, actor_id="test")

    async with test_session_factory() as session:
        validation_service = ClaimsValidationService(session)
        summary = await validation_service.validate_csv(_REAL_CLAIMS_CSV)

    # Every claim_key's source_key resolves once sources are imported —
    # this is the specific thing this test verifies.
    assert summary.unresolved_source_keys == []
    for row in summary.rows:
        assert not any("does not resolve" in reason for reason in row.reasons)


async def test_claims_validation_flags_non_numeric_sample_size_accurately(
    test_session_factory: async_sessionmaker[AsyncSession], clean_db: None
) -> None:
    # data/seed_claims.csv genuinely contains four Bitkom-sourced rows with
    # descriptive (non-numeric) sample_size text ("604 total survey")
    # rather than a bare integer. Validation must report this accurately
    # rather than being loosened just to make every row look "valid".
    import_service = SeedImportService(test_session_factory)
    await import_service.import_csv(_REAL_SOURCES_CSV, dry_run=False, actor_id="test")

    async with test_session_factory() as session:
        validation_service = ClaimsValidationService(session)
        summary = await validation_service.validate_csv(_REAL_CLAIMS_CSV)

    non_numeric_sample_size_rows = [
        r for r in summary.rows if any("sample_size" in reason for reason in r.reasons)
    ]
    assert len(non_numeric_sample_size_rows) == 4
    assert summary.valid + summary.invalid == summary.total_rows


async def test_claims_validation_flags_unresolved_source_key_without_sources(
    test_session_factory: async_sessionmaker[AsyncSession], clean_db: None
) -> None:
    # No sources imported in this test -> every claim's source_key should
    # fail to resolve, and nothing should be written.
    async with test_session_factory() as session:
        validation_service = ClaimsValidationService(session)
        summary = await validation_service.validate_csv(_REAL_CLAIMS_CSV)

    assert summary.invalid == summary.total_rows
    assert len(summary.unresolved_source_keys) > 0
    assert summary.claims_written == 0
