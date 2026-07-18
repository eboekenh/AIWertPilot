from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from de_ai_kb.db.models.sources import Source, SourceSnapshot
from de_ai_kb.repositories.sources import SourceRepository, SourceSnapshotRepository

pytestmark = pytest.mark.asyncio


async def _make_snapshot(session: AsyncSession) -> SourceSnapshot:
    source_repo = SourceRepository(session)
    source = Source(
        source_key="SNAP_SOURCE",
        title="Snapshot Source",
        publisher="Publisher",
        original_url="https://example.com/x",
        canonical_url="https://example.com/x",
        source_type="official_statistics",
        tier="A",
        refresh_interval_days=90,
    )
    source_repo.add(source)
    await session.flush()

    snapshot_repo = SourceSnapshotRepository(session)
    snapshot = SourceSnapshot(
        source_id=source.id,
        retrieved_at=datetime.now(UTC),
        final_url="https://example.com/x",
        sha256="a" * 64,
        rights_decision="metadata_only",
        fetcher_version="test-fetcher-0.1",
    )
    snapshot_repo.add(snapshot)
    await session.flush()
    await session.commit()
    return snapshot


async def test_snapshot_update_is_rejected_by_db_trigger(db_session: AsyncSession) -> None:
    snapshot = await _make_snapshot(db_session)
    snapshot.rights_decision = "full_text_allowed"
    with pytest.raises(DBAPIError, match="immutable"):
        await db_session.flush()


async def test_snapshot_repository_exposes_no_update_method(db_session: AsyncSession) -> None:
    assert not hasattr(SourceSnapshotRepository(db_session), "update")
