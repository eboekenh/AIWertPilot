"""training_providers, training_offerings, training_capabilities (schema.sql lines 342-391)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    ARRAY,
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    Numeric,
    Table,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from de_ai_kb.db.base import Base, TimestampMixin, UpdatedAtMixin, UUIDPkMixin


class TrainingProvider(UUIDPkMixin, TimestampMixin, UpdatedAtMixin, Base):
    __tablename__ = "training_providers"
    __table_args__ = (UniqueConstraint("name", "official_url", name="name_official_url"),)

    name: Mapped[str] = mapped_column(Text, nullable=False)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL")
    )
    official_url: Mapped[str] = mapped_column(Text, nullable=False)
    provider_type: Mapped[str | None] = mapped_column(Text)


class TrainingOffering(UUIDPkMixin, TimestampMixin, UpdatedAtMixin, Base):
    __tablename__ = "training_offerings"
    __table_args__ = (
        CheckConstraint(
            "duration_minutes IS NULL OR duration_minutes >= 0", name="duration_minutes_non_negative"
        ),
        CheckConstraint("price_amount IS NULL OR price_amount >= 0", name="price_amount_non_negative"),
        CheckConstraint(
            "status IN ('under_review','active','inactive','stale','archived')", name="status_valid"
        ),
        UniqueConstraint("provider_id", "official_url", name="provider_official_url"),
    )

    provider_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("training_providers.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    official_url: Mapped[str] = mapped_column(Text, nullable=False)
    target_roles: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'")
    )
    level: Mapped[str | None] = mapped_column(Text)
    language_codes: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'")
    )
    format: Mapped[str | None] = mapped_column(Text)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    location: Mapped[str | None] = mapped_column(Text)
    price_amount: Mapped[float | None] = mapped_column(Numeric)
    price_currency: Mapped[str | None] = mapped_column(Text)
    price_observed_at: Mapped[date | None] = mapped_column()
    certificate: Mapped[str | None] = mapped_column(Text)
    prerequisites: Mapped[str | None] = mapped_column(Text)
    next_start_at: Mapped[datetime | None] = mapped_column()
    last_verified_at: Mapped[datetime | None] = mapped_column()
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="under_review")
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )


training_capabilities = Table(
    "training_capabilities",
    Base.metadata,
    Column("training_id", ForeignKey("training_offerings.id", ondelete="CASCADE"), primary_key=True),
    Column("capability_id", ForeignKey("capabilities.id", ondelete="CASCADE"), primary_key=True),
    Column("coverage", Text, nullable=False),
    CheckConstraint(
        "coverage IN ('introductory','working','advanced')", name="ck_training_capabilities_coverage_valid"
    ),
)
