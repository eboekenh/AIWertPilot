"""claims, claim_evidence (schema.sql lines 212-258)."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    ARRAY,
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from de_ai_kb.db.base import Base, TimestampMixin, UpdatedAtMixin, UUIDPkMixin


class Claim(UUIDPkMixin, TimestampMixin, UpdatedAtMixin, Base):
    __tablename__ = "claims"
    __table_args__ = (
        CheckConstraint("sample_size IS NULL OR sample_size >= 0", name="sample_size_non_negative"),
        CheckConstraint(
            "confidence IN ('unknown','low','medium','high')", name="confidence_valid"
        ),
        CheckConstraint(
            "status IN ('extracted','under_review','approved','published','rejected',"
            "'superseded','archived')",
            name="status_valid",
        ),
    )

    claim_type: Mapped[str] = mapped_column(Text, nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_value: Mapped[float | None] = mapped_column(Numeric)
    normalized_unit: Mapped[str | None] = mapped_column(Text)
    geography_codes: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'")
    )
    jurisdiction_codes: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'")
    )
    industry_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("industries.id", ondelete="SET NULL")
    )
    company_size_scope: Mapped[str | None] = mapped_column(Text)
    sample_size: Mapped[int | None] = mapped_column(Integer)
    study_period_start: Mapped[date | None] = mapped_column()
    study_period_end: Mapped[date | None] = mapped_column()
    valid_from: Mapped[date | None] = mapped_column()
    valid_to: Mapped[date | None] = mapped_column()
    confidence: Mapped[str] = mapped_column(Text, nullable=False, server_default="unknown")
    confidence_rationale: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="under_review")
    analyst_notes: Mapped[str | None] = mapped_column(Text)

    evidence: Mapped[list[ClaimEvidence]] = relationship(
        back_populates="claim", cascade="all, delete-orphan"
    )


class ClaimEvidence(UUIDPkMixin, Base):
    __tablename__ = "claim_evidence"
    __table_args__ = (
        CheckConstraint(
            "short_quote IS NULL OR char_length(short_quote) <= 500", name="short_quote_length"
        ),
        CheckConstraint(
            "relationship IN ('supports','contradicts','qualifies','context')",
            name="relationship_valid",
        ),
        UniqueConstraint(
            "claim_id", "document_id", "locator", "relationship", name="claim_document_locator_relationship"
        ),
    )

    claim_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("claims.id", ondelete="CASCADE"), nullable=False
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="RESTRICT"), nullable=False
    )
    chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("document_chunks.id", ondelete="SET NULL")
    )
    page_number: Mapped[int | None] = mapped_column(Integer)
    locator: Mapped[str | None] = mapped_column(Text)
    evidence_summary: Mapped[str] = mapped_column(Text, nullable=False)
    short_quote: Mapped[str | None] = mapped_column(Text)
    relationship_: Mapped[str] = mapped_column("relationship", Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))

    claim: Mapped[Claim] = relationship(back_populates="evidence")
