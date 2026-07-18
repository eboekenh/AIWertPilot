"""seed_claims.csv validation.

Validates structure, required fields, and that every source_key resolves to
a registered source. Never writes to claims or claim_evidence in Foundation
Release 1 — seed_claims.csv is a worksheet; the corresponding snapshots,
documents, and evidence locators do not exist yet (see
docs/NEXT_RELEASES.md for the Release 2/3 import path).
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from de_ai_kb.repositories.sources import SourceRepository
from de_ai_kb.services.csv_rows import SeedClaimRow


@dataclass
class ClaimRowResult:
    row_number: int
    claim_key: str
    valid: bool
    reasons: list[str] = field(default_factory=list)


@dataclass
class ClaimsValidationSummary:
    total_rows: int = 0
    valid: int = 0
    invalid: int = 0
    duplicate_claim_keys: list[str] = field(default_factory=list)
    unresolved_source_keys: list[str] = field(default_factory=list)
    rows: list[ClaimRowResult] = field(default_factory=list)
    claims_written: int = 0
    claim_evidence_written: int = 0


class ClaimsValidationService:
    def __init__(self, session: AsyncSession) -> None:
        self._source_repo = SourceRepository(session)

    async def validate_csv(self, file_path: Path) -> ClaimsValidationSummary:
        summary = ClaimsValidationSummary()
        seen_keys: dict[str, int] = {}

        with file_path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            raw_rows = list(enumerate(reader, start=2))

        summary.total_rows = len(raw_rows)

        for row_number, raw_row in raw_rows:
            reasons: list[str] = []
            try:
                row = SeedClaimRow.from_csv_row(raw_row)
            except ValidationError as exc:
                reasons = [f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()]
                summary.invalid += 1
                summary.rows.append(
                    ClaimRowResult(row_number, raw_row.get("claim_key", ""), False, reasons)
                )
                continue

            if row.claim_key in seen_keys:
                reasons.append(
                    f"duplicate claim_key (first seen row {seen_keys[row.claim_key]})"
                )
                if row.claim_key not in summary.duplicate_claim_keys:
                    summary.duplicate_claim_keys.append(row.claim_key)
            else:
                seen_keys[row.claim_key] = row_number

            source = await self._source_repo.get_by_source_key(row.source_key)
            if source is None:
                reasons.append(f"source_key {row.source_key!r} does not resolve to a registered source")
                if row.source_key not in summary.unresolved_source_keys:
                    summary.unresolved_source_keys.append(row.source_key)

            if row.normalized_value:
                try:
                    float(row.normalized_value)
                except ValueError:
                    reasons.append(f"normalized_value {row.normalized_value!r} is not numeric")

            if row.sample_size:
                try:
                    int(row.sample_size)
                except ValueError:
                    reasons.append(f"sample_size {row.sample_size!r} is not an integer")

            if reasons:
                summary.invalid += 1
                summary.rows.append(ClaimRowResult(row_number, row.claim_key, False, reasons))
            else:
                summary.valid += 1
                summary.rows.append(ClaimRowResult(row_number, row.claim_key, True))

        return summary
