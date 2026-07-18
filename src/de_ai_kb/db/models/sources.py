"""sources, source_quality_evaluations, source_snapshots (schema.sql lines 15-112)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    ARRAY,
    CheckConstraint,
    ForeignKey,
    Integer,
    SmallInteger,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from de_ai_kb.db.base import Base, TimestampMixin, UpdatedAtMixin, UUIDPkMixin


class Source(UUIDPkMixin, TimestampMixin, UpdatedAtMixin, Base):
    __tablename__ = "sources"
    __table_args__ = (
        CheckConstraint("tier IN ('A','B','C','D','E')", name="tier_valid"),
        CheckConstraint(
            "access_policy IN ('metadata_only','short_evidence','full_text_allowed','blocked','unknown')",
            name="access_policy_valid",
        ),
        CheckConstraint(
            "rights_status IN ('needs_review','reviewed_allowed','reviewed_restricted','blocked')",
            name="rights_status_valid",
        ),
        CheckConstraint(
            "tdm_opt_out_status IN ('unknown','not_found','reserved','not_applicable')",
            name="tdm_opt_out_status_valid",
        ),
        CheckConstraint("refresh_interval_days > 0", name="refresh_interval_days_positive"),
        CheckConstraint(
            "status IN ('discovered','registered','fetched','extracted','under_review',"
            "'approved','published','rejected','blocked','superseded','archived')",
            name="status_valid",
        ),
        UniqueConstraint("canonical_url", "publisher", name="canonical_url_publisher"),
    )

    source_key: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    publisher: Mapped[str] = mapped_column(Text, nullable=False)
    original_url: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    tier: Mapped[str] = mapped_column(Text, nullable=False)
    language_code: Mapped[str] = mapped_column(Text, nullable=False, server_default="de")
    geography_codes: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'")
    )
    jurisdiction_codes: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'")
    )
    topic_tags: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'")
    )
    access_policy: Mapped[str] = mapped_column(Text, nullable=False, server_default="metadata_only")
    licence_name: Mapped[str | None] = mapped_column(Text)
    licence_url: Mapped[str | None] = mapped_column(Text)
    rights_status: Mapped[str] = mapped_column(Text, nullable=False, server_default="needs_review")
    tdm_opt_out_status: Mapped[str] = mapped_column(Text, nullable=False, server_default="unknown")
    robots_reviewed_at: Mapped[datetime | None] = mapped_column()
    terms_reviewed_at: Mapped[datetime | None] = mapped_column()
    refresh_interval_days: Mapped[int] = mapped_column(Integer, nullable=False)
    last_discovered_at: Mapped[datetime | None] = mapped_column()
    last_verified_at: Mapped[datetime | None] = mapped_column()
    next_review_at: Mapped[datetime | None] = mapped_column()
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="registered")
    notes: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )

    quality_evaluations: Mapped[list[SourceQualityEvaluation]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )
    snapshots: Mapped[list[SourceSnapshot]] = relationship(back_populates="source")


class SourceQualityEvaluation(UUIDPkMixin, Base):
    __tablename__ = "source_quality_evaluations"
    __table_args__ = (
        CheckConstraint("authority BETWEEN 0 AND 5", name="authority_range"),
        CheckConstraint("method_transparency BETWEEN 0 AND 5", name="method_transparency_range"),
        CheckConstraint("recency BETWEEN 0 AND 5", name="recency_range"),
        CheckConstraint("geographic_relevance BETWEEN 0 AND 5", name="geographic_relevance_range"),
        CheckConstraint("scope_specificity BETWEEN 0 AND 5", name="scope_specificity_range"),
        CheckConstraint("independence BETWEEN 0 AND 5", name="independence_range"),
        CheckConstraint("locatability BETWEEN 0 AND 5", name="locatability_range"),
        CheckConstraint("derived_score BETWEEN 0 AND 100", name="derived_score_range"),
    )

    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), nullable=False
    )
    authority: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    method_transparency: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    recency: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    geographic_relevance: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    scope_specificity: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    independence: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    locatability: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    derived_score: Mapped[float] = mapped_column(nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    evaluated_by: Mapped[str] = mapped_column(Text, nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))
    superseded_at: Mapped[datetime | None] = mapped_column()

    source: Mapped[Source] = relationship(back_populates="quality_evaluations")


class SourceSnapshot(UUIDPkMixin, Base):
    __tablename__ = "source_snapshots"
    __table_args__ = (
        CheckConstraint(
            "retention_policy IN ('metadata_only','temporary','retained','blocked')",
            name="retention_policy_valid",
        ),
        UniqueConstraint("source_id", "sha256", name="source_sha256"),
    )

    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False
    )
    retrieved_at: Mapped[datetime] = mapped_column(nullable=False)
    final_url: Mapped[str] = mapped_column(Text, nullable=False)
    http_status: Mapped[int | None] = mapped_column(Integer)
    etag: Mapped[str | None] = mapped_column(Text)
    last_modified: Mapped[str | None] = mapped_column(Text)
    media_type: Mapped[str | None] = mapped_column(Text)
    content_length: Mapped[int | None] = mapped_column()
    sha256: Mapped[str] = mapped_column(Text, nullable=False)
    storage_uri: Mapped[str | None] = mapped_column(Text)
    retention_policy: Mapped[str] = mapped_column(Text, nullable=False, server_default="metadata_only")
    rights_decision: Mapped[str] = mapped_column(Text, nullable=False)
    fetcher_version: Mapped[str] = mapped_column(Text, nullable=False)
    parser_version: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )

    source: Mapped[Source] = relationship(back_populates="snapshots")
