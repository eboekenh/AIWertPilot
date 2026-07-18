"""GET /api/v1/review-items, POST /api/v1/review-items/{id}/decision."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from de_ai_kb.api.deps import ApiKeyActorDep, SessionDep
from de_ai_kb.api.schemas.common import Page
from de_ai_kb.api.schemas.review_items import ReviewDecisionRequest, ReviewItemRead
from de_ai_kb.repositories.review import ReviewItemFilters
from de_ai_kb.services.review import ReviewService

router = APIRouter(prefix="/api/v1/review-items", tags=["review-items"])


@router.get("", response_model=Page[ReviewItemRead])
async def list_review_items(
    session: SessionDep,
    status: str | None = None,
    review_type: str | None = None,
    entity_type: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> Page[ReviewItemRead]:
    service = ReviewService(session)
    filters = ReviewItemFilters(status=status, review_type=review_type, entity_type=entity_type)
    items, total = await service.list(filters=filters, limit=limit, offset=offset)
    return Page(
        items=[ReviewItemRead.model_validate(i) for i in items], total=total, limit=limit, offset=offset
    )


@router.post("/{review_item_id}/decision", response_model=ReviewItemRead)
async def decide_review_item(
    review_item_id: uuid.UUID,
    payload: ReviewDecisionRequest,
    session: SessionDep,
    actor: ApiKeyActorDep,
) -> ReviewItemRead:
    service = ReviewService(session)
    item = await service.decide(
        review_item_id=review_item_id,
        new_status=payload.status,
        decision_reason=payload.decision_reason,
        actor_id=actor,
    )
    return ReviewItemRead.model_validate(item)
