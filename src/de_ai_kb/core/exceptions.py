"""Typed domain exceptions used across services, CLI, and API."""

from __future__ import annotations


class DomainError(Exception):
    """Base class for typed, user-facing domain errors."""

    code: str = "domain_error"

    def __init__(self, message: str, *, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFoundError(DomainError):
    code = "not_found"


class DuplicateSourceError(DomainError):
    code = "duplicate_source"


class InvalidStateTransitionError(DomainError):
    code = "invalid_state_transition"


class ValidationFailedError(DomainError):
    code = "validation_failed"


class EvidenceRequiredError(DomainError):
    code = "evidence_required"


class ImmutableRecordError(DomainError):
    code = "immutable_record"
