"""industries, business_processes, capabilities (schema.sql lines 155-193)."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from de_ai_kb.db.base import Base, TimestampMixin, UpdatedAtMixin, UUIDPkMixin


class Industry(UUIDPkMixin, TimestampMixin, UpdatedAtMixin, Base):
    __tablename__ = "industries"

    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    nace_code: Mapped[str | None] = mapped_column(Text)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("industries.id", ondelete="SET NULL")
    )
    description: Mapped[str | None] = mapped_column(Text)


class BusinessProcess(UUIDPkMixin, TimestampMixin, UpdatedAtMixin, Base):
    __tablename__ = "business_processes"

    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("business_processes.id", ondelete="SET NULL")
    )
    description: Mapped[str | None] = mapped_column(Text)


class Capability(UUIDPkMixin, TimestampMixin, UpdatedAtMixin, Base):
    __tablename__ = "capabilities"

    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
