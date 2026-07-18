from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from de_ai_kb.core.exceptions import EvidenceRequiredError
from de_ai_kb.db.models.documents import Document
from de_ai_kb.db.models.evidence import Claim, ClaimEvidence
from de_ai_kb.db.models.sources import Source, SourceSnapshot
from de_ai_kb.repositories.documents import DocumentRepository
from de_ai_kb.repositories.evidence import ClaimEvidenceRepository, ClaimRepository
from de_ai_kb.repositories.sources import SourceRepository, SourceSnapshotRepository
from de_ai_kb.services.evidence import EvidenceService

pytestmark = pytest.mark.asyncio


async def _make_document(session: AsyncSession) -> Document:
    source_repo = SourceRepository(session)
    source = Source(
        source_key="EVID_SOURCE",
        title="Evidence Source",
        publisher="Publisher",
        original_url="https://example.com/evidence",
        canonical_url="https://example.com/evidence",
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
        final_url="https://example.com/evidence",
        sha256="b" * 64,
        rights_decision="metadata_only",
        fetcher_version="test-fetcher-0.1",
    )
    snapshot_repo.add(snapshot)
    await session.flush()

    document_repo = DocumentRepository(session)
    document = Document(
        snapshot_id=snapshot.id,
        title="Evidence Document",
        document_type="report",
        language_code="de",
    )
    document_repo.add(document)
    await session.flush()
    return document


async def test_claim_without_evidence_cannot_be_published(db_session: AsyncSession) -> None:
    claim_repo = ClaimRepository(db_session)
    claim = Claim(claim_type="adoption_statistic", statement="Test statement")
    claim_repo.add(claim)
    await db_session.flush()

    evidence_service = EvidenceService(db_session)
    with pytest.raises(EvidenceRequiredError):
        await evidence_service.assert_can_publish(claim.id)


async def test_claim_with_evidence_can_be_published(db_session: AsyncSession) -> None:
    document = await _make_document(db_session)
    claim_repo = ClaimRepository(db_session)
    claim = Claim(claim_type="adoption_statistic", statement="Test statement with evidence")
    claim_repo.add(claim)
    await db_session.flush()

    evidence_repo = ClaimEvidenceRepository(db_session)
    evidence_repo.add(
        ClaimEvidence(
            claim_id=claim.id,
            document_id=document.id,
            evidence_summary="Paraphrased summary of what the source states.",
            relationship_="supports",
        )
    )
    await db_session.flush()

    evidence_service = EvidenceService(db_session)
    await evidence_service.assert_can_publish(claim.id)  # must not raise
