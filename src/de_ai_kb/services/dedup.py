"""Duplicate-candidate detection.

Never merges automatically. Flags two kinds of candidate pairs as
review_items(review_type='dedup_candidate'):
  - same canonical_url, different publisher (score 1.0, reason
    'canonical_url_match') — schema.sql's UNIQUE(canonical_url, publisher)
    already prevents an exact (url, publisher) duplicate at the DB level;
    this catches the same URL registered under a different publisher label.
  - same publisher, title similarity >= TITLE_SIMILARITY_THRESHOLD (score =
    similarity ratio, reason 'title_similarity').
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from de_ai_kb.db.models.sources import Source
from de_ai_kb.domain.similarity import TITLE_SIMILARITY_THRESHOLD, title_similarity
from de_ai_kb.repositories.sources import SourceRepository
from de_ai_kb.services.review import ReviewService


@dataclass
class DuplicateCandidate:
    source_id: UUID
    counterpart_source_id: UUID
    similarity_score: float
    reason: str


class DuplicateDetectionService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._source_repo = SourceRepository(session)
        self._review_service = ReviewService(session)

    @staticmethod
    def find_candidates(sources: list[Source]) -> list[DuplicateCandidate]:
        candidates: list[DuplicateCandidate] = []
        seen_pairs: set[frozenset[UUID]] = set()
        for i, a in enumerate(sources):
            for b in sources[i + 1 :]:
                pair = frozenset({a.id, b.id})
                if pair in seen_pairs:
                    continue
                if a.canonical_url == b.canonical_url and a.publisher != b.publisher:
                    seen_pairs.add(pair)
                    candidates.append(
                        DuplicateCandidate(a.id, b.id, 1.0, "canonical_url_match")
                    )
                    continue
                if a.publisher == b.publisher:
                    score = title_similarity(a.title, b.title)
                    if score >= TITLE_SIMILARITY_THRESHOLD:
                        seen_pairs.add(pair)
                        candidates.append(
                            DuplicateCandidate(a.id, b.id, score, "title_similarity")
                        )
        return candidates

    async def scan_all(self, *, actor_id: str) -> list[DuplicateCandidate]:
        sources = await self._source_repo.list_all()
        candidates = self.find_candidates(sources)
        for candidate in candidates:
            await self._review_service.create_dedup_candidate(
                source_id=candidate.source_id,
                counterpart_source_id=candidate.counterpart_source_id,
                similarity_score=candidate.similarity_score,
                reason=candidate.reason,
                actor_id=actor_id,
            )
        return candidates
