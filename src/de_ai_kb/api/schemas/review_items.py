"""Pydantic v2 schemas for the review-items API."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from de_ai_kb.api.schemas.sources import SourceRead
from de_ai_kb.domain.enums import AccessPolicy, ReviewItemStatus, RightsStatus, TdmOptOutStatus


class ReviewItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    review_type: str
    status: str
    priority: int
    assigned_to: str | None
    decision_reason: str | None
    due_at: datetime | None
    decided_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ReviewDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ReviewItemStatus
    decision_reason: str | None = None


class RightsReviewDecisionRequest(BaseModel):
    """Explicit, reviewed rights outcome for a rights_review item.

    Deliberately has no default and no inference from "approved" — a rights
    review must produce real values, never an assumption. See
    domain/rights_policy.py for which rights_status/access_policy
    combinations are valid (e.g. a blocked result can never carry
    short_evidence or full_text_allowed).
    """

    model_config = ConfigDict(extra="forbid")

    rights_status: RightsStatus
    access_policy: AccessPolicy
    decision_reason: str = Field(min_length=1)
    tdm_opt_out_status: TdmOptOutStatus | None = None
    licence_name: str | None = None
    licence_url: str | None = None


class RightsReviewDecisionResult(BaseModel):
    review_item: ReviewItemRead
    source: SourceRead
