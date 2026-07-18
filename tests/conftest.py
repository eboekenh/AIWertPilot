"""Shared pytest fixtures.

Integration tests run against a real PostgreSQL 16 + pgvector database
(TEST_DATABASE_URL), never SQLite — array/JSONB/pgvector/CHECK-constraint
behavior must be exercised for real. The target database must already have
migrations applied (see README.md / CLAUDE.md commands) before running the
suite.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from de_ai_kb.core.config import get_settings
from de_ai_kb.db.session import get_sessionmaker

# Children-before-parents order, safe for TRUNCATE ... CASCADE regardless.
_ALL_TABLES = [
    "audit_events",
    "review_items",
    "research_jobs",
    "funding_programs",
    "use_case_obligations",
    "regulatory_obligations",
    "regulations",
    "training_capabilities",
    "training_offerings",
    "training_providers",
    "case_study_claims",
    "case_studies",
    "use_case_claims",
    "use_case_capabilities",
    "use_case_processes",
    "use_case_industries",
    "use_cases",
    "claim_evidence",
    "claims",
    "organizations",
    "capabilities",
    "business_processes",
    "industries",
    "document_chunks",
    "documents",
    "source_snapshots",
    "source_quality_evaluations",
    "sources",
]


@pytest.fixture(scope="session")
def test_session_factory() -> async_sessionmaker[AsyncSession]:
    settings = get_settings()
    return get_sessionmaker(settings.test_database_url)


async def _truncate_all(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with session_factory() as session:
        await session.execute(text(f"TRUNCATE TABLE {', '.join(_ALL_TABLES)} RESTART IDENTITY CASCADE"))
        await session.commit()


@pytest_asyncio.fixture
async def clean_db(test_session_factory: async_sessionmaker[AsyncSession]) -> AsyncIterator[None]:
    """Truncates all tables after the test. Use this (rather than an outer
    rolled-back transaction) because several services under test
    deliberately open and commit their own independent sessions/transactions
    (e.g. SeedImportService commits one transaction per CSV row)."""
    yield
    await _truncate_all(test_session_factory)


@pytest_asyncio.fixture
async def db_session(
    test_session_factory: async_sessionmaker[AsyncSession], clean_db: None
) -> AsyncIterator[AsyncSession]:
    async with test_session_factory() as session:
        yield session
        if session.in_transaction() and not session.get_transaction().is_active:  # type: ignore[union-attr]
            # A test intentionally triggered a DB error (e.g. asserting a
            # trigger rejects a write) and left the transaction in a
            # rolled-back-pending state; there is nothing left to commit.
            await session.rollback()
        else:
            await session.commit()


@pytest_asyncio.fixture
async def api_client(
    test_session_factory: async_sessionmaker[AsyncSession], clean_db: None
) -> AsyncIterator[AsyncClient]:
    from de_ai_kb.api import deps
    from de_ai_kb.main import create_app

    app = create_app()

    async def _override_get_session() -> AsyncIterator[AsyncSession]:
        async with test_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[deps.get_session] = _override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture
def dev_api_key() -> str:
    return get_settings().dev_api_key
