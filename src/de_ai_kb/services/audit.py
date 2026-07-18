"""Single seam for audit-event emission.

Every material mutation calls AuditService.record(...) explicitly, in the
same transaction/session as the mutation itself — not an ORM
before_flush hook, not an eventual/async side channel — so before/after
diffing stays controllable and testable, and a rollback of the mutation
also rolls back its audit row (no orphaned audit events).
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from de_ai_kb.db.models.ops import AuditEvent
from de_ai_kb.repositories.audit import AuditEventRepository


class AuditService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = AuditEventRepository(session)

    def record(
        self,
        *,
        actor_type: str,
        actor_id: str,
        action: str,
        entity_type: str,
        entity_id: uuid.UUID | None,
        before_state: dict[str, Any] | None = None,
        after_state: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> None:
        self._repo.add(
            AuditEvent(
                actor_type=actor_type,
                actor_id=actor_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                request_id=request_id,
                before_state=before_state,
                after_state=after_state,
                metadata_=metadata or {},
            )
        )
