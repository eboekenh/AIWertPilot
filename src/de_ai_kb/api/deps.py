"""FastAPI dependencies: DB session and dev-only API-key auth."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from de_ai_kb.core.config import get_settings
from de_ai_kb.db.session import get_sessionmaker


async def get_session() -> AsyncIterator[AsyncSession]:
    settings = get_settings()
    session_factory = get_sessionmaker(settings.database_url)
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def require_api_key(
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> str:
    settings = get_settings()
    if not x_api_key or x_api_key != settings.dev_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or missing X-API-Key")
    return "dev-api-key"


ApiKeyActorDep = Annotated[str, Depends(require_api_key)]
