"""Python mirrors of every schema.sql CHECK-constrained enumeration.

Each enum's value set must exactly match the corresponding CHECK constraint
list in schema.sql / migrations/versions/0001_baseline_schema.py. This is
verified by tests/unit/test_enum_constraint_lockstep.py so the two never
silently drift apart. Values are plain strings on the wire and in the
database (text + CHECK), never native Postgres ENUM types — see
docs/ADR-001-architecture.md for the rationale.
"""

from __future__ import annotations

from enum import StrEnum


class SourceTier(StrEnum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


class AccessPolicy(StrEnum):
    METADATA_ONLY = "metadata_only"
    SHORT_EVIDENCE = "short_evidence"
    FULL_TEXT_ALLOWED = "full_text_allowed"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


class RightsStatus(StrEnum):
    NEEDS_REVIEW = "needs_review"
    REVIEWED_ALLOWED = "reviewed_allowed"
    REVIEWED_RESTRICTED = "reviewed_restricted"
    BLOCKED = "blocked"


class TdmOptOutStatus(StrEnum):
    UNKNOWN = "unknown"
    NOT_FOUND = "not_found"
    RESERVED = "reserved"
    NOT_APPLICABLE = "not_applicable"


class SourceStatus(StrEnum):
    DISCOVERED = "discovered"
    REGISTERED = "registered"
    FETCHED = "fetched"
    EXTRACTED = "extracted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"
    BLOCKED = "blocked"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


# Allowed source.status transitions. Enforced by ReviewService /
# SourceRegistryService, in addition to the DB CHECK constraint that only
# guarantees membership, not transition validity.
SOURCE_STATUS_TRANSITIONS: dict[SourceStatus, set[SourceStatus]] = {
    SourceStatus.DISCOVERED: {SourceStatus.REGISTERED, SourceStatus.REJECTED, SourceStatus.BLOCKED},
    SourceStatus.REGISTERED: {
        SourceStatus.FETCHED,
        SourceStatus.REJECTED,
        SourceStatus.BLOCKED,
        SourceStatus.SUPERSEDED,
        SourceStatus.ARCHIVED,
    },
    SourceStatus.FETCHED: {
        SourceStatus.EXTRACTED,
        SourceStatus.REJECTED,
        SourceStatus.BLOCKED,
        SourceStatus.SUPERSEDED,
    },
    SourceStatus.EXTRACTED: {
        SourceStatus.UNDER_REVIEW,
        SourceStatus.REJECTED,
        SourceStatus.BLOCKED,
        SourceStatus.SUPERSEDED,
    },
    SourceStatus.UNDER_REVIEW: {
        SourceStatus.APPROVED,
        SourceStatus.REJECTED,
        SourceStatus.BLOCKED,
        SourceStatus.SUPERSEDED,
    },
    SourceStatus.APPROVED: {SourceStatus.PUBLISHED, SourceStatus.BLOCKED, SourceStatus.SUPERSEDED},
    SourceStatus.PUBLISHED: {SourceStatus.SUPERSEDED, SourceStatus.ARCHIVED, SourceStatus.BLOCKED},
    SourceStatus.REJECTED: {SourceStatus.ARCHIVED, SourceStatus.REGISTERED},
    SourceStatus.BLOCKED: {SourceStatus.ARCHIVED},
    SourceStatus.SUPERSEDED: {SourceStatus.ARCHIVED},
    SourceStatus.ARCHIVED: set(),
}


class SnapshotRetentionPolicy(StrEnum):
    METADATA_ONLY = "metadata_only"
    TEMPORARY = "temporary"
    RETAINED = "retained"
    BLOCKED = "blocked"


class ClaimConfidence(StrEnum):
    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ClaimStatus(StrEnum):
    EXTRACTED = "extracted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class EvidenceRelationship(StrEnum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    QUALIFIES = "qualifies"
    CONTEXT = "context"


class UseCaseMaturity(StrEnum):
    CANDIDATE = "candidate"
    EMERGING = "emerging"
    ESTABLISHED = "established"
    MATURE = "mature"


class LifecycleStatus(StrEnum):
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class UseCaseIndustryRelevance(StrEnum):
    PRIMARY = "primary"
    APPLICABLE = "applicable"
    CONDITIONAL = "conditional"


class UseCaseCapabilityImportance(StrEnum):
    REQUIRED = "required"
    RECOMMENDED = "recommended"
    ADVANCED = "advanced"


class UseCaseClaimRelationship(StrEnum):
    BENEFIT = "benefit"
    PREREQUISITE = "prerequisite"
    RISK = "risk"
    IMPLEMENTATION = "implementation"
    CONTEXT = "context"


class DeploymentStage(StrEnum):
    EXPERIMENT = "experiment"
    POC = "poc"
    PILOT = "pilot"
    PRODUCTION = "production"
    SCALED = "scaled"
    UNKNOWN = "unknown"


class CaseStudyStatus(StrEnum):
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class TrainingOfferingStatus(StrEnum):
    UNDER_REVIEW = "under_review"
    ACTIVE = "active"
    INACTIVE = "inactive"
    STALE = "stale"
    ARCHIVED = "archived"


class TrainingCoverage(StrEnum):
    INTRODUCTORY = "introductory"
    WORKING = "working"
    ADVANCED = "advanced"


class RegulatoryObligationStatus(StrEnum):
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class UseCaseObligationRelevance(StrEnum):
    POSSIBLE = "possible"
    LIKELY = "likely"
    CONTEXT_ONLY = "context_only"


class FundingProgramStatus(StrEnum):
    UNDER_REVIEW = "under_review"
    OPEN = "open"
    CLOSED = "closed"
    PAUSED = "paused"
    STALE = "stale"
    ARCHIVED = "archived"


class ResearchJobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class ReviewItemStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_CHANGES = "needs_changes"
    CANCELLED = "cancelled"


# Allowed review_items.status transitions, enforced by ReviewService.
REVIEW_ITEM_STATUS_TRANSITIONS: dict[ReviewItemStatus, set[ReviewItemStatus]] = {
    ReviewItemStatus.OPEN: {
        ReviewItemStatus.IN_PROGRESS,
        ReviewItemStatus.APPROVED,
        ReviewItemStatus.REJECTED,
        ReviewItemStatus.NEEDS_CHANGES,
        ReviewItemStatus.CANCELLED,
    },
    ReviewItemStatus.IN_PROGRESS: {
        ReviewItemStatus.APPROVED,
        ReviewItemStatus.REJECTED,
        ReviewItemStatus.NEEDS_CHANGES,
        ReviewItemStatus.CANCELLED,
    },
    ReviewItemStatus.NEEDS_CHANGES: {
        ReviewItemStatus.IN_PROGRESS,
        ReviewItemStatus.APPROVED,
        ReviewItemStatus.REJECTED,
        ReviewItemStatus.CANCELLED,
    },
    ReviewItemStatus.APPROVED: set(),
    ReviewItemStatus.REJECTED: set(),
    ReviewItemStatus.CANCELLED: set(),
}


# review_items.review_type is free text in schema.sql (not CHECK-constrained,
# since new review categories may be needed later). These are the values this
# release actually creates; kept as constants, not an enum, to avoid implying
# a closed set.
REVIEW_TYPE_RIGHTS = "rights_review"
REVIEW_TYPE_CONTENT = "content_review"
REVIEW_TYPE_DEDUP_CANDIDATE = "dedup_candidate"


class FreshnessState(StrEnum):
    """Not a DB column — computed by domain.freshness at read time."""

    FRESH = "fresh"
    DUE_SOON = "due_soon"
    STALE = "stale"
    UNKNOWN = "unknown"
