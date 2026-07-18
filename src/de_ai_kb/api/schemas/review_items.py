"""Pydantic v2 schemas for the review-items API."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from de_ai_kb.domain.enums import ReviewItemStatus


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
    status: ReviewItemStatus
    decision_reason: str | None = None
