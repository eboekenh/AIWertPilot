import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from de_ai_kb.db.models.sources import Source, SourceQualityEvaluation
from de_ai_kb.repositories.sources import SourceQualityEvaluationRepository, SourceRepository

pytestmark = pytest.mark.asyncio


async def _make_source(session: AsyncSession) -> Source:
    repo = SourceRepository(session)
    source = Source(
        source_key="QUALITY_SOURCE",
        title="Quality Source",
        publisher="Publisher",
        original_url="https://example.com/quality",
        canonical_url="https://example.com/quality",
        source_type="official_statistics",
        tier="A",
        refresh_interval_days=90,
    )
    repo.add(source)
    await session.flush()
    return source


def _make_evaluation(source_id: object, **overrides: int) -> SourceQualityEvaluation:
    defaults: dict[str, int] = dict(
        authority=5,
        method_transparency=4,
        recency=3,
        geographic_relevance=5,
        scope_specificity=4,
        independence=5,
        locatability=5,
    )
    defaults.update(overrides)
    return SourceQualityEvaluation(
        source_id=source_id,
        rationale="Test rationale",
        evaluated_by="test",
        derived_score=85.5,
        **defaults,
    )


async def test_valid_quality_evaluation_is_accepted(db_session: AsyncSession) -> None:
    source = await _make_source(db_session)
    repo = SourceQualityEvaluationRepository(db_session)
    repo.add(_make_evaluation(source.id))
    await db_session.flush()  # must not raise


@pytest.mark.parametrize("field", ["authority", "method_transparency", "recency", "independence"])
async def test_component_above_five_is_rejected(db_session: AsyncSession, field: str) -> None:
    source = await _make_source(db_session)
    repo = SourceQualityEvaluationRepository(db_session)
    repo.add(_make_evaluation(source.id, **{field: 6}))
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_component_below_zero_is_rejected(db_session: AsyncSession) -> None:
    source = await _make_source(db_session)
    repo = SourceQualityEvaluationRepository(db_session)
    repo.add(_make_evaluation(source.id, authority=-1))
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_derived_score_above_100_is_rejected(db_session: AsyncSession) -> None:
    source = await _make_source(db_session)
    repo = SourceQualityEvaluationRepository(db_session)
    evaluation = _make_evaluation(source.id)
    evaluation.derived_score = 150
    repo.add(evaluation)
    with pytest.raises(IntegrityError):
        await db_session.flush()
