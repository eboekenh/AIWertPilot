"""Every Python enum in domain.enums must have exactly the same value set as
its corresponding schema.sql / migration CHECK constraint. This test parses
the CheckConstraint SQL text straight off the SQLAlchemy table metadata (the
same objects Alembic's baseline migration and the ORM models share) so the
two can never silently drift apart.
"""

from __future__ import annotations

import re

from sqlalchemy import CheckConstraint, Table
from sqlalchemy.orm import DeclarativeBase

from de_ai_kb.db.models.case_studies import CaseStudy
from de_ai_kb.db.models.evidence import Claim, ClaimEvidence
from de_ai_kb.db.models.funding import FundingProgram
from de_ai_kb.db.models.ops import ResearchJob, ReviewItem
from de_ai_kb.db.models.regulation import RegulatoryObligation, use_case_obligations
from de_ai_kb.db.models.sources import Source, SourceSnapshot
from de_ai_kb.db.models.training import TrainingOffering, training_capabilities
from de_ai_kb.db.models.use_cases import UseCase, use_case_capabilities, use_case_claims, use_case_industries
from de_ai_kb.domain.enums import (
    AccessPolicy,
    CaseStudyStatus,
    ClaimConfidence,
    ClaimStatus,
    DeploymentStage,
    EvidenceRelationship,
    FundingProgramStatus,
    LifecycleStatus,
    RegulatoryObligationStatus,
    ResearchJobStatus,
    ReviewItemStatus,
    RightsStatus,
    SnapshotRetentionPolicy,
    SourceStatus,
    SourceTier,
    TdmOptOutStatus,
    TrainingCoverage,
    TrainingOfferingStatus,
    UseCaseCapabilityImportance,
    UseCaseClaimRelationship,
    UseCaseIndustryRelevance,
    UseCaseMaturity,
    UseCaseObligationRelevance,
)

_IN_LIST_RE = re.compile(r"IN\s*\(([^)]*)\)")


def _values_for_column(table_or_model: type[DeclarativeBase] | Table, column_prefix: str) -> set[str]:
    table = table_or_model.__table__ if hasattr(table_or_model, "__table__") else table_or_model
    for constraint in table.constraints:
        if not isinstance(constraint, CheckConstraint):
            continue
        sql_text = str(constraint.sqltext)
        if sql_text.strip().startswith(f"{column_prefix} IN"):
            match = _IN_LIST_RE.search(sql_text)
            assert match, f"could not parse IN-list from: {sql_text}"
            return {v.strip().strip("'") for v in match.group(1).split(",")}
    raise AssertionError(f"no CHECK...IN constraint found for column {column_prefix!r} on {table.name}")


def _enum_values(enum_cls: type) -> set[str]:
    return {member.value for member in enum_cls}


def test_source_tier() -> None:
    assert _values_for_column(Source, "tier") == _enum_values(SourceTier)


def test_source_access_policy() -> None:
    assert _values_for_column(Source, "access_policy") == _enum_values(AccessPolicy)


def test_source_rights_status() -> None:
    assert _values_for_column(Source, "rights_status") == _enum_values(RightsStatus)


def test_source_tdm_opt_out_status() -> None:
    assert _values_for_column(Source, "tdm_opt_out_status") == _enum_values(TdmOptOutStatus)


def test_source_status() -> None:
    assert _values_for_column(Source, "status") == _enum_values(SourceStatus)


def test_source_snapshot_retention_policy() -> None:
    assert _values_for_column(SourceSnapshot, "retention_policy") == _enum_values(SnapshotRetentionPolicy)


def test_claim_confidence() -> None:
    assert _values_for_column(Claim, "confidence") == _enum_values(ClaimConfidence)


def test_claim_status() -> None:
    assert _values_for_column(Claim, "status") == _enum_values(ClaimStatus)


def test_claim_evidence_relationship() -> None:
    assert _values_for_column(ClaimEvidence, "relationship") == _enum_values(EvidenceRelationship)


def test_use_case_maturity() -> None:
    assert _values_for_column(UseCase, "maturity") == _enum_values(UseCaseMaturity)


def test_use_case_lifecycle_status() -> None:
    assert _values_for_column(UseCase, "lifecycle_status") == _enum_values(LifecycleStatus)


def test_use_case_industries_relevance() -> None:
    assert _values_for_column(use_case_industries, "relevance") == _enum_values(UseCaseIndustryRelevance)


def test_use_case_capabilities_importance() -> None:
    assert _values_for_column(use_case_capabilities, "importance") == _enum_values(
        UseCaseCapabilityImportance
    )


def test_use_case_claims_relationship() -> None:
    assert _values_for_column(use_case_claims, "relationship") == _enum_values(UseCaseClaimRelationship)


def test_case_study_deployment_stage() -> None:
    assert _values_for_column(CaseStudy, "deployment_stage") == _enum_values(DeploymentStage)


def test_case_study_status() -> None:
    assert _values_for_column(CaseStudy, "status") == _enum_values(CaseStudyStatus)


def test_training_offering_status() -> None:
    assert _values_for_column(TrainingOffering, "status") == _enum_values(TrainingOfferingStatus)


def test_training_capabilities_coverage() -> None:
    assert _values_for_column(training_capabilities, "coverage") == _enum_values(TrainingCoverage)


def test_regulatory_obligation_status() -> None:
    assert _values_for_column(RegulatoryObligation, "status") == _enum_values(RegulatoryObligationStatus)


def test_use_case_obligations_relevance() -> None:
    assert _values_for_column(use_case_obligations, "relevance") == _enum_values(UseCaseObligationRelevance)


def test_funding_program_status() -> None:
    assert _values_for_column(FundingProgram, "status") == _enum_values(FundingProgramStatus)


def test_research_job_status() -> None:
    assert _values_for_column(ResearchJob, "status") == _enum_values(ResearchJobStatus)


def test_review_item_status() -> None:
    assert _values_for_column(ReviewItem, "status") == _enum_values(ReviewItemStatus)
