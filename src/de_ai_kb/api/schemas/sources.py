"""Pydantic v2 schemas for the sources API."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from de_ai_kb.domain.enums import (
    AccessPolicy,
    FreshnessState,
    RightsStatus,
    SourceStatus,
    SourceTier,
)


class SourceCreate(BaseModel):
    source_key: str = Field(min_length=1)
    title: str = Field(min_length=1)
    publisher: str = Field(min_length=1)
    original_url: str
    source_type: str
    tier: SourceTier
    language_code: str = "de"
    geography_codes: list[str] = Field(default_factory=list)
    jurisdiction_codes: list[str] = Field(default_factory=list)
    topic_tags: list[str] = Field(default_factory=list)
    access_policy: AccessPolicy = AccessPolicy.METADATA_ONLY
    rights_status: RightsStatus = RightsStatus.NEEDS_REVIEW
    refresh_interval_days: int = Field(default=90, gt=0)
    notes: str | None = None


class SourceUpdate(BaseModel):
    """Generic source metadata edits only.

    Lifecycle (``status``) and rights/access fields (``rights_status``,
    ``access_policy``) are deliberately absent — those are governed
    invariants, not free-form metadata, and must go through
    ``POST /api/v1/sources/{id}/transition``,
    ``POST /api/v1/sources/{id}/block``, and
    ``POST /api/v1/review-items/{id}/rights-decision`` respectively. See
    docs/RESEARCH_WORKFLOW.md. ``extra="forbid"`` makes an attempt to set a
    removed or unknown field fail with 422 rather than being silently
    ignored.
    """

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1)
    publisher: str | None = Field(default=None, min_length=1)
    tier: SourceTier | None = None
    topic_tags: list[str] | None = None
    refresh_interval_days: int | None = Field(default=None, gt=0)
    notes: str | None = None


class SourceTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    new_status: SourceStatus
    reason: str | None = None


class SourceBlockRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=1)

    @field_validator("reason")
    @classmethod
    def _reason_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("reason must not be blank")
        return v


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_key: str
    title: str
    publisher: str
    original_url: str
    canonical_url: str
    source_type: str
    tier: str
    language_code: str
    geography_codes: list[str]
    jurisdiction_codes: list[str]
    topic_tags: list[str]
    access_policy: str
    rights_status: str
    tdm_opt_out_status: str
    licence_name: str | None
    licence_url: str | None
    refresh_interval_days: int
    last_verified_at: datetime | None
    next_review_at: datetime | None
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class FreshnessReportItemRead(BaseModel):
    source_id: uuid.UUID
    source_key: str
    title: str
    status: str
    last_verified_at: datetime | None
    refresh_interval_days: int
    freshness_state: FreshnessState
