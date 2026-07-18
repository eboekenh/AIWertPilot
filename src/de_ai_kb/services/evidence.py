"""Evidence-before-generation policy: a published claim must have >=1
claim_evidence row. Enforced here (service layer), not left to the DB alone.

No claims are created in Foundation Release 1 (seed_claims.csv is validated
only — see services/claims_validation.py), but this guard and its tests
ship now so Release 2/3's claim-publishing path has a tested policy
boundary to call into immediately.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from de_ai_kb.core.exceptions import EvidenceRequiredError
from de_ai_kb.repositories.evidence import ClaimEvidenceRepository


class EvidenceService:
    def __init__(self, session: AsyncSession) -> None:
        self._evidence_repo = ClaimEvidenceRepository(session)

    async def assert_can_publish(self, claim_id: uuid.UUID) -> None:
        count = await self._evidence_repo.count_for_claim(claim_id)
        if count < 1:
            raise EvidenceRequiredError(
                f"claim {claim_id} cannot be published without at least one claim_evidence row"
            )
