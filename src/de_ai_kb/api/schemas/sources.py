"""Pydantic v2 schemas for the sources API."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

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
    title: str | None = None
    publisher: str | None = None
    tier: SourceTier | None = None
    topic_tags: list[str] | None = None
    access_policy: AccessPolicy | None = None
    rights_status: RightsStatus | None = None
    refresh_interval_days: int | None = Field(default=None, gt=0)
    notes: str | None = None
    status: SourceStatus | None = None


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
