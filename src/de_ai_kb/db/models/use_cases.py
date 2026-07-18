"""use_cases and its four association tables (schema.sql lines 260-312)."""

from __future__ import annotations

from sqlalchemy import ARRAY, CheckConstraint, Column, ForeignKey, Table, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from de_ai_kb.db.base import Base, TimestampMixin, UpdatedAtMixin, UUIDPkMixin


class UseCase(UUIDPkMixin, TimestampMixin, UpdatedAtMixin, Base):
    __tablename__ = "use_cases"
    __table_args__ = (
        CheckConstraint(
            "maturity IN ('candidate','emerging','established','mature')", name="maturity_valid"
        ),
        CheckConstraint(
            "lifecycle_status IN ('under_review','approved','published','superseded','archived')",
            name="lifecycle_status_valid",
        ),
    )

    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    business_problem: Mapped[str] = mapped_column(Text, nullable=False)
    ai_pattern: Mapped[str] = mapped_column(Text, nullable=False)
    human_role: Mapped[str | None] = mapped_column(Text)
    expected_outcomes: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'")
    )
    required_data: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'")
    )
    integration_dependencies: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'")
    )
    maturity: Mapped[str] = mapped_column(Text, nullable=False, server_default="candidate")
    lifecycle_status: Mapped[str] = mapped_column(Text, nullable=False, server_default="under_review")
    limitations: Mapped[str | None] = mapped_column(Text)


use_case_industries = Table(
    "use_case_industries",
    Base.metadata,
    Column("use_case_id", ForeignKey("use_cases.id", ondelete="CASCADE"), primary_key=True),
    Column("industry_id", ForeignKey("industries.id", ondelete="CASCADE"), primary_key=True),
    Column("relevance", Text, nullable=False, server_default="applicable"),
    CheckConstraint(
        "relevance IN ('primary','applicable','conditional')", name="ck_use_case_industries_relevance_valid"
    ),
)

use_case_processes = Table(
    "use_case_processes",
    Base.metadata,
    Column("use_case_id", ForeignKey("use_cases.id", ondelete="CASCADE"), primary_key=True),
    Column("process_id", ForeignKey("business_processes.id", ondelete="CASCADE"), primary_key=True),
)

use_case_capabilities = Table(
    "use_case_capabilities",
    Base.metadata,
    Column("use_case_id", ForeignKey("use_cases.id", ondelete="CASCADE"), primary_key=True),
    Column("capability_id", ForeignKey("capabilities.id", ondelete="CASCADE"), primary_key=True),
    Column("importance", Text, nullable=False),
    Column("minimum_level", Text),
    CheckConstraint(
        "importance IN ('required','recommended','advanced')",
        name="ck_use_case_capabilities_importance_valid",
    ),
)

use_case_claims = Table(
    "use_case_claims",
    Base.metadata,
    Column("use_case_id", ForeignKey("use_cases.id", ondelete="CASCADE"), primary_key=True),
    Column("claim_id", ForeignKey("claims.id", ondelete="CASCADE"), primary_key=True),
    Column("relationship", Text, primary_key=True),
    CheckConstraint(
        "relationship IN ('benefit','prerequisite','risk','implementation','context')",
        name="ck_use_case_claims_relationship_valid",
    ),
)
