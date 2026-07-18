"""Thin CRUD for audit_events."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from de_ai_kb.db.models.ops import AuditEvent


class AuditEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, event: AuditEvent) -> None:
        self._session.add(event)

    async def list_for_entity(self, *, entity_type: str, entity_id: uuid.UUID) -> list[AuditEvent]:
        result = await self._session.execute(
            select(AuditEvent)
            .where(AuditEvent.entity_type == entity_type, AuditEvent.entity_id == entity_id)
            .order_by(AuditEvent.occurred_at.desc())
        )
        return list(result.scalars().all())
