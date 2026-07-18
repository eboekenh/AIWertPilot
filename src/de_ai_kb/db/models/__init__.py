"""Import every model module so Base.metadata is fully populated.

Alembic's env.py and any code that calls Base.metadata.create_all/drop_all
must import this package first.
"""

from de_ai_kb.db.models.case_studies import CaseStudy, case_study_claims
from de_ai_kb.db.models.documents import Document, DocumentChunk
from de_ai_kb.db.models.evidence import Claim, ClaimEvidence
from de_ai_kb.db.models.funding import FundingProgram
from de_ai_kb.db.models.ops import AuditEvent, ResearchJob, ReviewItem
from de_ai_kb.db.models.organizations import Organization
from de_ai_kb.db.models.regulation import Regulation, RegulatoryObligation, use_case_obligations
from de_ai_kb.db.models.sources import Source, SourceQualityEvaluation, SourceSnapshot
from de_ai_kb.db.models.taxonomy import BusinessProcess, Capability, Industry
from de_ai_kb.db.models.training import TrainingOffering, TrainingProvider, training_capabilities
from de_ai_kb.db.models.use_cases import (
    UseCase,
    use_case_capabilities,
    use_case_claims,
    use_case_industries,
    use_case_processes,
)

__all__ = [
    "AuditEvent",
    "BusinessProcess",
    "Capability",
    "CaseStudy",
    "Claim",
    "ClaimEvidence",
    "Document",
    "DocumentChunk",
    "FundingProgram",
    "Industry",
    "Organization",
    "Regulation",
    "RegulatoryObligation",
    "ResearchJob",
    "ReviewItem",
    "Source",
    "SourceQualityEvaluation",
    "SourceSnapshot",
    "TrainingOffering",
    "TrainingProvider",
    "UseCase",
    "case_study_claims",
    "training_capabilities",
    "use_case_capabilities",
    "use_case_claims",
    "use_case_industries",
    "use_case_obligations",
    "use_case_processes",
]
