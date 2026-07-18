"""Declarative base, naming convention, and shared mixins."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, MetaData, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    # Every schema.sql timestamp column is `timestamptz`; without this map,
    # a bare `Mapped[datetime]` infers timezone-naive DateTime() and asyncpg
    # rejects aware datetimes bound against it ("can't subtract offset-naive
    # and offset-aware datetimes").
    type_annotation_map = {datetime: DateTime(timezone=True)}


class UUIDPkMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"), nullable=False)


class UpdatedAtMixin:
    updated_at: Mapped[datetime] = mapped_column(server_default=text("now()"), nullable=False)
