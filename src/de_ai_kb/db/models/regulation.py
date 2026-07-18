"""regulations, regulatory_obligations, use_case_obligations (schema.sql lines 393-437)."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import CheckConstraint, Column, ForeignKey, Table, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from de_ai_kb.db.base import Base, TimestampMixin, UpdatedAtMixin, UUIDPkMixin


class Regulation(UUIDPkMixin, TimestampMixin, UpdatedAtMixin, Base):
    __tablename__ = "regulations"
    __table_args__ = (
        UniqueConstraint(
            "jurisdiction_code", "official_identifier", name="jurisdiction_code_official_identifier"
        ),
    )

    title: Mapped[str] = mapped_column(Text, nullable=False)
    official_identifier: Mapped[str | None] = mapped_column(Text)
    jurisdiction_code: Mapped[str] = mapped_column(Text, nullable=False)
    official_url: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[date | None] = mapped_column()
    effective_from: Mapped[date | None] = mapped_column()
    effective_to: Mapped[date | None] = mapped_column()
    authoritative_source_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("sources.id", ondelete="SET NULL")
    )
    notes: Mapped[str | None] = mapped_column(Text)


class RegulatoryObligation(UUIDPkMixin, TimestampMixin, UpdatedAtMixin, Base):
    __tablename__ = "regulatory_obligations"
    __table_args__ = (
        CheckConstraint(
            "status IN ('under_review','approved','published','superseded','archived')",
            name="status_valid",
        ),
    )

    regulation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("regulations.id", ondelete="CASCADE"), nullable=False
    )
    article_or_section: Mapped[str | None] = mapped_column(Text)
    affected_actor: Mapped[str] = mapped_column(Text, nullable=False)
    obligation_summary: Mapped[str] = mapped_column(Text, nullable=False)
    applies_from: Mapped[date | None] = mapped_column()
    applies_to: Mapped[str | None] = mapped_column(Text)
    authoritative_claim_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("claims.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="under_review")


use_case_obligations = Table(
    "use_case_obligations",
    Base.metadata,
    Column("use_case_id", ForeignKey("use_cases.id", ondelete="CASCADE"), primary_key=True),
    Column("obligation_id", ForeignKey("regulatory_obligations.id", ondelete="CASCADE"), primary_key=True),
    Column("relevance", Text, nullable=False),
    Column("rationale", Text, nullable=False),
    CheckConstraint(
        "relevance IN ('possible','likely','context_only')",
        name="ck_use_case_obligations_relevance_valid",
    ),
)
