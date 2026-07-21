"""CORS is opt-in and origin-scoped: no Access-Control-Allow-Origin header at
all unless the app is explicitly configured with an allowlist, and only for
origins actually on that allowlist. Uses create_app(cors_allowed_origins=...)
directly rather than the environment, so the test never depends on ambient
.env state."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from de_ai_kb.main import create_app

pytestmark = pytest.mark.asyncio


async def test_no_cors_header_when_no_origins_configured() -> None:
    app = create_app(cors_allowed_origins=[])
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


async def test_cors_header_present_for_allowed_origin() -> None:
    app = create_app(cors_allowed_origins=["http://localhost:3000"])
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


async def test_cors_header_absent_for_disallowed_origin() -> None:
    app = create_app(cors_allowed_origins=["http://localhost:3000"])
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/health", headers={"Origin": "http://evil.example"})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


async def test_cors_never_allows_credentials() -> None:
    """No cookie/session auth exists in this API; combining a credentialed
    CORS response with an origin allowlist would only widen the attack
    surface for no benefit, so allow_credentials must always be False."""
    app = create_app(cors_allowed_origins=["http://localhost:3000"])
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert "access-control-allow-credentials" not in response.headers
