"""GET /api/v1/review-items, POST /api/v1/review-items/{id}/decision,
POST /api/v1/review-items/{id}/rights-decision.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from de_ai_kb.api.deps import ApiKeyActorDep, SessionDep
from de_ai_kb.api.schemas.common import Page
from de_ai_kb.api.schemas.review_items import (
    ReviewDecisionRequest,
    ReviewItemRead,
    RightsReviewDecisionRequest,
    RightsReviewDecisionResult,
)
from de_ai_kb.api.schemas.sources import SourceRead
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
    """Generic decision workflow for non-rights review items (content_review,
    dedup_candidate, and non-approval outcomes of rights_review). Approving
    a rights_review item here is rejected — see /rights-decision."""
    service = ReviewService(session)
    item = await service.decide(
        review_item_id=review_item_id,
        new_status=payload.status,
        decision_reason=payload.decision_reason,
        actor_id=actor,
    )
    return ReviewItemRead.model_validate(item)


@router.post("/{review_item_id}/rights-decision", response_model=RightsReviewDecisionResult)
async def resolve_rights_review(
    review_item_id: uuid.UUID,
    payload: RightsReviewDecisionRequest,
    session: SessionDep,
    actor: ApiKeyActorDep,
) -> RightsReviewDecisionResult:
    """Approve a rights_review item with an explicit reviewed rights_status/
    access_policy outcome, applied to the source atomically in the same
    transaction as the review decision. Both the review-item update and the
    source policy update are audited."""
    service = ReviewService(session)
    item, source = await service.resolve_rights_review(
        review_item_id=review_item_id,
        rights_status=payload.rights_status,
        access_policy=payload.access_policy,
        decision_reason=payload.decision_reason,
        tdm_opt_out_status=payload.tdm_opt_out_status,
        licence_name=payload.licence_name,
        licence_url=payload.licence_url,
        actor_id=actor,
    )
    return RightsReviewDecisionResult(
        review_item=ReviewItemRead.model_validate(item), source=SourceRead.model_validate(source)
    )
