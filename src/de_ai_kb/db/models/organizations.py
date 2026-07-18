"""organizations (schema.sql lines 195-210)."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from de_ai_kb.db.base import Base, TimestampMixin, UpdatedAtMixin, UUIDPkMixin


class Organization(UUIDPkMixin, TimestampMixin, UpdatedAtMixin, Base):
    __tablename__ = "organizations"
    __table_args__ = (UniqueConstraint("name", "country_code", name="name_country_code"),)

    name: Mapped[str] = mapped_column(Text, nullable=False)
    organization_type: Mapped[str] = mapped_column(Text, nullable=False)
    country_code: Mapped[str | None] = mapped_column(Text)
    website_url: Mapped[str | None] = mapped_column(Text)
    industry_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("industries.id", ondelete="SET NULL")
    )
    employee_band: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
