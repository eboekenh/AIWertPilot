"""research_jobs, review_items, audit_events (schema.sql lines 467-521).

Deviation (documented in docs/ADR-001-architecture.md): review_items gains a
`metadata jsonb` column not present in schema.sql. It carries only
*supplemental* review context (e.g. a dedup candidate's counterpart source id
and similarity score for review_type='dedup_candidate') and must never be
used to hold a primary searchable business field — those stay as real
columns (entity_type, entity_id, review_type, status, priority,
assigned_to, decision_reason all remain plain columns exactly as in
schema.sql).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, ForeignKey, SmallInteger, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from de_ai_kb.db.base import Base, TimestampMixin, UpdatedAtMixin, UUIDPkMixin


class ResearchJob(UUIDPkMixin, Base):
    __tablename__ = "research_jobs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued','running','succeeded','failed','blocked','cancelled')",
            name="status_valid",
        ),
    )

    job_type: Mapped[str] = mapped_column(Text, nullable=False)
    source_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sources.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="queued")
    requested_by: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column()
    finished_at: Mapped[datetime | None] = mapped_column()
    input_: Mapped[dict[str, Any]] = mapped_column(
        "input", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    output_summary: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    error_code: Mapped[str | None] = mapped_column(Text)
    error_detail: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))


class ReviewItem(UUIDPkMixin, TimestampMixin, UpdatedAtMixin, Base):
    __tablename__ = "review_items"
    __table_args__ = (
        CheckConstraint(
            "status IN ('open','in_progress','approved','rejected','needs_changes','cancelled')",
            name="status_valid",
        ),
        CheckConstraint("priority BETWEEN 1 AND 5", name="priority_range"),
        UniqueConstraint(
            "entity_type", "entity_id", "review_type", "status",
            name="entity_type_entity_id_review_type_status",
        ),
    )

    entity_type: Mapped[str] = mapped_column(Text, nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    review_type: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="open")
    priority: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="3")
    assigned_to: Mapped[str | None] = mapped_column(Text)
    decision_reason: Mapped[str | None] = mapped_column(Text)
    due_at: Mapped[datetime | None] = mapped_column()
    decided_at: Mapped[datetime | None] = mapped_column()
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )


class AuditEvent(UUIDPkMixin, Base):
    __tablename__ = "audit_events"

    actor_type: Mapped[str] = mapped_column(Text, nullable=False)
    actor_id: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    entity_type: Mapped[str] = mapped_column(Text, nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column()
    request_id: Mapped[str | None] = mapped_column(Text)
    before_state: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    after_state: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    occurred_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))
