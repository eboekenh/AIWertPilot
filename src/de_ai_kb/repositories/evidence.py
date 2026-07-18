"""Thin CRUD for claims and claim_evidence.

No production claims are created in Foundation Release 1 (seed_claims.csv is
validated only, never imported — see services/claims_validation.py). This
repository exists so the evidence-required-to-publish policy
(services/evidence.py) has a real, tested data-access path ready for
Release 2/3.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from de_ai_kb.db.models.evidence import Claim, ClaimEvidence


class ClaimRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, claim: Claim) -> None:
        self._session.add(claim)

    async def get_by_id(self, claim_id: uuid.UUID) -> Claim | None:
        return await self._session.get(Claim, claim_id)


class ClaimEvidenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, evidence: ClaimEvidence) -> None:
        self._session.add(evidence)

    async def list_for_claim(self, claim_id: uuid.UUID) -> list[ClaimEvidence]:
        result = await self._session.execute(
            select(ClaimEvidence).where(ClaimEvidence.claim_id == claim_id)
        )
        return list(result.scalars().all())

    async def count_for_claim(self, claim_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(ClaimEvidence).where(ClaimEvidence.claim_id == claim_id)
        )
        return len(result.scalars().all())
