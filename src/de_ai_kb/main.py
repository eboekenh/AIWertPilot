"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from de_ai_kb.api.routers import health, research, review_items, sources
from de_ai_kb.core.config import get_settings
from de_ai_kb.core.exceptions import (
    DomainError,
    DuplicateSourceError,
    EvidenceRequiredError,
    ImmutableRecordError,
    InvalidStateTransitionError,
    NotFoundError,
    ValidationFailedError,
)
from de_ai_kb.core.logging import configure_logging

_STATUS_BY_ERROR: dict[type[DomainError], int] = {
    NotFoundError: 404,
    DuplicateSourceError: 409,
    InvalidStateTransitionError: 409,
    ValidationFailedError: 422,
    EvidenceRequiredError: 422,
    ImmutableRecordError: 409,
}


def _parse_cors_origins(raw: str) -> list[str]:
    """Comma-separated origin list -> list of trimmed, non-empty origins.
    An empty/unset value parses to an empty list, which disables CORS
    entirely (the safe default for a backend with no browser frontend
    attached)."""
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def create_app(*, cors_allowed_origins: list[str] | None = None) -> FastAPI:
    """Build the FastAPI app. ``cors_allowed_origins`` overrides the
    configured origins (used by tests); omit it to use
    ``Settings.cors_allowed_origins`` from the environment/.env."""
    configure_logging(get_settings().log_level)
    app = FastAPI(title="Germany AI Knowledge Base", version="0.1.0")

    origins = (
        cors_allowed_origins
        if cors_allowed_origins is not None
        else _parse_cors_origins(get_settings().cors_allowed_origins)
    )
    if origins:
        # No cookies/session auth is used anywhere in this API (writes are
        # authorized via the X-API-Key header), so allow_credentials stays
        # False — combining it with an origin allowlist would only widen
        # the attack surface for no benefit here. Methods/headers are
        # restricted to what the API actually uses.
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=False,
            allow_methods=["GET", "POST", "PATCH"],
            allow_headers=["Content-Type", "X-API-Key"],
        )

    app.include_router(health.router)
    app.include_router(sources.router)
    app.include_router(research.router)
    app.include_router(review_items.router)

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        status_code = 400
        for error_type, code in _STATUS_BY_ERROR.items():
            if isinstance(exc, error_type):
                status_code = code
                break
        return JSONResponse(
            status_code=status_code,
            content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_failed",
                    "message": "request validation failed",
                    "details": {"errors": jsonable_encoder(exc.errors())},
                }
            },
        )

    return app


app = create_app()
