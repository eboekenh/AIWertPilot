"""Pydantic row models for the two seed CSVs (data/seed_sources.csv,
data/seed_claims.csv). Validation only — these models never write to the
database themselves.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from de_ai_kb.domain.enums import AccessPolicy, SourceTier
from de_ai_kb.domain.url import canonicalize_url

_VALID_TIERS = {t.value for t in SourceTier}
_VALID_ACCESS_POLICIES = {p.value for p in AccessPolicy}


class SeedSourceRow(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    source_key: str = Field(min_length=1)
    title: str = Field(min_length=1)
    publisher: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    tier: str
    topics: list[str] = Field(default_factory=list)
    geography: list[str] = Field(default_factory=list)
    language: str = Field(min_length=2)
    url: str
    canonical_url: str = ""
    access_policy: str
    refresh_days: int
    review_status: str
    notes: str = ""

    @field_validator("tier")
    @classmethod
    def _tier_valid(cls, v: str) -> str:
        if v not in _VALID_TIERS:
            raise ValueError(f"tier {v!r} not one of {sorted(_VALID_TIERS)}")
        return v

    @field_validator("access_policy")
    @classmethod
    def _access_policy_valid(cls, v: str) -> str:
        if v not in _VALID_ACCESS_POLICIES:
            raise ValueError(f"access_policy {v!r} not one of {sorted(_VALID_ACCESS_POLICIES)}")
        return v

    @field_validator("refresh_days")
    @classmethod
    def _refresh_days_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("refresh_days must be positive")
        return v

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> SeedSourceRow:
        url = (row.get("url") or "").strip()
        canonical = canonicalize_url(url) if url else ""
        return cls(
            source_key=row.get("source_key", ""),
            title=row.get("title", ""),
            publisher=row.get("publisher", ""),
            source_type=row.get("source_type", ""),
            tier=row.get("tier", ""),
            topics=[t for t in (row.get("topics") or "").split("|") if t],
            geography=[g for g in (row.get("geography") or "").split("|") if g],
            language=row.get("language", ""),
            url=url,
            canonical_url=canonical,
            access_policy=row.get("access_policy", ""),
            refresh_days=int(row["refresh_days"]) if (row.get("refresh_days") or "").strip() else 0,
            review_status=row.get("review_status", ""),
            notes=row.get("notes", ""),
        )


class SeedClaimRow(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    claim_key: str = Field(min_length=1)
    source_key: str = Field(min_length=1)
    claim_type: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    normalized_value: str = ""
    unit: str = ""
    geography: str = ""
    company_size_scope: str = ""
    sample_size: str = ""
    study_period: str = ""
    locator: str = Field(min_length=1)
    review_status: str = Field(min_length=1)
    notes: str = ""

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> SeedClaimRow:
        return cls(
            claim_key=row.get("claim_key", ""),
            source_key=row.get("source_key", ""),
            claim_type=row.get("claim_type", ""),
            statement=row.get("statement", ""),
            normalized_value=row.get("normalized_value", ""),
            unit=row.get("unit", ""),
            geography=row.get("geography", ""),
            company_size_scope=row.get("company_size_scope", ""),
            sample_size=row.get("sample_size", ""),
            study_period=row.get("study_period", ""),
            locator=row.get("locator", ""),
            review_status=row.get("review_status", ""),
            notes=row.get("notes", ""),
        )
