"""Shared response envelopes."""

from __future__ import annotations

from pydantic import BaseModel


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, object] = {}


class ErrorEnvelope(BaseModel):
    error: ErrorDetail
