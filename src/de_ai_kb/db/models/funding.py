"""funding_programs (schema.sql lines 439-465)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ARRAY, CheckConstraint, ForeignKey, Numeric, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from de_ai_kb.db.base import Base, TimestampMixin, UpdatedAtMixin, UUIDPkMixin


class FundingProgram(UUIDPkMixin, TimestampMixin, UpdatedAtMixin, Base):
    __tablename__ = "funding_programs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('under_review','open','closed','paused','stale','archived')",
            name="status_valid",
        ),
        UniqueConstraint("provider", "official_url", name="provider_official_url"),
    )

    title: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    official_url: Mapped[str] = mapped_column(Text, nullable=False)
    geography_codes: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'")
    )
    applicant_types: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'")
    )
    company_size_scope: Mapped[str | None] = mapped_column(Text)
    funding_form: Mapped[str | None] = mapped_column(Text)
    funding_rate: Mapped[float | None] = mapped_column(Numeric)
    maximum_amount: Mapped[float | None] = mapped_column(Numeric)
    currency: Mapped[str | None] = mapped_column(Text)
    opens_at: Mapped[datetime | None] = mapped_column()
    deadline_at: Mapped[datetime | None] = mapped_column()
    eligibility_summary: Mapped[str | None] = mapped_column(Text)
    last_verified_at: Mapped[datetime | None] = mapped_column()
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="under_review")
    source_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sources.id", ondelete="SET NULL"))
