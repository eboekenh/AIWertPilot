"""Thin CRUD for documents. Exists to support claim_evidence's FK chain in
tests; no document ingestion pipeline ships in this release."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from de_ai_kb.db.models.documents import Document


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, document: Document) -> None:
        self._session.add(document)

    async def get_by_id(self, document_id: uuid.UUID) -> Document | None:
        return await self._session.get(Document, document_id)
