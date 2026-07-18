"""GET /api/v1/research/freshness."""

from __future__ import annotations

from fastapi import APIRouter, Query

from de_ai_kb.api.deps import SessionDep
from de_ai_kb.api.schemas.sources import FreshnessReportItemRead
from de_ai_kb.domain.enums import FreshnessState
from de_ai_kb.services.freshness import FreshnessService

router = APIRouter(prefix="/api/v1/research", tags=["research"])


@router.get("/freshness", response_model=list[FreshnessReportItemRead])
async def freshness_report(
    session: SessionDep,
    state: str | None = Query(default=None, description="fresh|due_soon|stale|unknown"),
) -> list[FreshnessReportItemRead]:
    service = FreshnessService(session)
    state_filter = FreshnessState(state) if state else None
    items = await service.report(state_filter=state_filter)
    return [FreshnessReportItemRead.model_validate(vars(i)) for i in items]
