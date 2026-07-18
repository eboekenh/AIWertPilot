"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
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


def create_app() -> FastAPI:
    configure_logging(get_settings().log_level)
    app = FastAPI(title="Germany AI Knowledge Base", version="0.1.0")

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
