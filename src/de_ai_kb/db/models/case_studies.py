"""case_studies, case_study_claims (schema.sql lines 314-340)."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Table, Text
from sqlalchemy.orm import Mapped, mapped_column

from de_ai_kb.db.base import Base, TimestampMixin, UpdatedAtMixin, UUIDPkMixin


class CaseStudy(UUIDPkMixin, TimestampMixin, UpdatedAtMixin, Base):
    __tablename__ = "case_studies"
    __table_args__ = (
        CheckConstraint(
            "deployment_stage IN ('experiment','poc','pilot','production','scaled','unknown')",
            name="deployment_stage_valid",
        ),
        CheckConstraint(
            "status IN ('under_review','approved','published','rejected','superseded','archived')",
            name="status_valid",
        ),
    )

    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL")
    )
    use_case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("use_cases.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    deployment_stage: Mapped[str] = mapped_column(Text, nullable=False)
    self_reported: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    baseline_summary: Mapped[str | None] = mapped_column(Text)
    intervention_summary: Mapped[str] = mapped_column(Text, nullable=False)
    outcome_summary: Mapped[str | None] = mapped_column(Text)
    measurement_period: Mapped[str | None] = mapped_column(Text)
    transferability_notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="under_review")


case_study_claims = Table(
    "case_study_claims",
    Base.metadata,
    Column("case_study_id", ForeignKey("case_studies.id", ondelete="CASCADE"), primary_key=True),
    Column("claim_id", ForeignKey("claims.id", ondelete="CASCADE"), primary_key=True),
)
