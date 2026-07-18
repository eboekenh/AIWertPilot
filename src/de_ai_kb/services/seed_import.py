"""Seed-source CSV import: dry-run support, structured results, row-level
rejection reasons, canonical URL handling, duplicate review candidates, and
idempotency (each row commits in its own transaction, so one row's failure
never rolls back another row's already-committed work, and a source is
never left without its two standard review items).
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from de_ai_kb.core.exceptions import DomainError
from de_ai_kb.domain.enums import AccessPolicy, RightsStatus, SourceStatus
from de_ai_kb.repositories.sources import SourceRepository
from de_ai_kb.services.csv_rows import SeedSourceRow
from de_ai_kb.services.review import ReviewService
from de_ai_kb.services.source_registry import SourceRegistryService

Outcome = Literal["inserted", "updated", "unchanged", "rejected"]
_ParsedRow = tuple[int, "dict[str, str] | None", "SeedSourceRow | None", "str | None"]


@dataclass
class RowResult:
    row_number: int
    source_key: str
    outcome: Outcome
    reason: str | None = None
    source_id: str | None = None


@dataclass
class SeedImportSummary:
    total_rows: int = 0
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0
    rejected: int = 0
    review_items_created: int = 0
    dry_run: bool = True
    rows: list[RowResult] = field(default_factory=list)


def _format_validation_error(exc: ValidationError) -> str:
    parts = [f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()]
    return "; ".join(parts)


def _diff_fields(existing: Any, parsed: SeedSourceRow) -> dict[str, Any]:
    diff: dict[str, Any] = {}
    if existing.title != parsed.title:
        diff["title"] = parsed.title
    if existing.publisher != parsed.publisher:
        diff["publisher"] = parsed.publisher
    if existing.source_type != parsed.source_type:
        diff["source_type"] = parsed.source_type
    if existing.tier != parsed.tier:
        diff["tier"] = parsed.tier
    if existing.language_code != parsed.language:
        diff["language_code"] = parsed.language
    if sorted(existing.topic_tags) != sorted(parsed.topics):
        diff["topic_tags"] = parsed.topics
    if sorted(existing.geography_codes) != sorted(parsed.geography):
        diff["geography_codes"] = parsed.geography
    if existing.access_policy != parsed.access_policy:
        diff["access_policy"] = parsed.access_policy
    if existing.refresh_interval_days != parsed.refresh_days:
        diff["refresh_interval_days"] = parsed.refresh_days
    if existing.original_url != parsed.url:
        diff["original_url"] = parsed.url
    if existing.canonical_url != parsed.canonical_url:
        diff["canonical_url"] = parsed.canonical_url
    if (existing.notes or "") != (parsed.notes or ""):
        diff["notes"] = parsed.notes
    return diff


class SeedImportService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    def _parse_rows(self, file_path: Path) -> list[_ParsedRow]:
        parsed_rows: list[_ParsedRow] = []
        with file_path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for i, raw_row in enumerate(reader, start=2):  # header is row 1
                try:
                    row = SeedSourceRow.from_csv_row(raw_row)
                except (ValidationError, ValueError) as exc:
                    reason = (
                        _format_validation_error(exc) if isinstance(exc, ValidationError) else str(exc)
                    )
                    parsed_rows.append((i, raw_row, None, reason))
                    continue
                parsed_rows.append((i, raw_row, row, None))
        return parsed_rows

    async def import_csv(
        self, file_path: Path, *, dry_run: bool, actor_id: str
    ) -> SeedImportSummary:
        summary = SeedImportSummary(dry_run=dry_run)
        parsed_rows = self._parse_rows(file_path)
        summary.total_rows = len(parsed_rows)

        for row_number, raw_row, parsed, reject_reason in parsed_rows:
            source_key = (raw_row or {}).get("source_key", "") if raw_row else ""
            if parsed is None:
                summary.rejected += 1
                summary.rows.append(
                    RowResult(row_number, source_key, "rejected", reason=reject_reason)
                )
                continue

            if dry_run:
                async with self._session_factory() as session:
                    repo = SourceRepository(session)
                    existing = await repo.get_by_source_key(parsed.source_key)
                    if existing is None:
                        summary.inserted += 1
                        summary.rows.append(RowResult(row_number, parsed.source_key, "inserted"))
                    else:
                        diff = _diff_fields(existing, parsed)
                        if diff:
                            summary.updated += 1
                            summary.rows.append(RowResult(row_number, parsed.source_key, "updated"))
                        else:
                            summary.unchanged += 1
                            summary.rows.append(RowResult(row_number, parsed.source_key, "unchanged"))
                continue

            try:
                async with self._session_factory() as session, session.begin():
                    repo = SourceRepository(session)
                    existing = await repo.get_by_source_key(parsed.source_key)
                    registry_service = SourceRegistryService(session)
                    review_service = ReviewService(session)

                    if existing is None:
                        source = await registry_service.create_source(
                            source_key=parsed.source_key,
                            title=parsed.title,
                            publisher=parsed.publisher,
                            original_url=parsed.url,
                            source_type=parsed.source_type,
                            tier=parsed.tier,
                            language_code=parsed.language,
                            geography_codes=parsed.geography,
                            topic_tags=parsed.topics,
                            access_policy=AccessPolicy(parsed.access_policy),
                            rights_status=RightsStatus.NEEDS_REVIEW,
                            refresh_interval_days=parsed.refresh_days,
                            notes=parsed.notes,
                            status=SourceStatus.REGISTERED,
                            actor_id=actor_id,
                        )
                        created_items = await review_service.create_standard_source_review_items(
                            source_id=source.id, actor_id=actor_id
                        )
                        summary.inserted += 1
                        summary.review_items_created += len(created_items)
                        summary.rows.append(
                            RowResult(
                                row_number, parsed.source_key, "inserted", source_id=str(source.id)
                            )
                        )
                    else:
                        diff = _diff_fields(existing, parsed)
                        if diff:
                            await registry_service.update_source(
                                source_id=existing.id, updates=diff, actor_id=actor_id
                            )
                            summary.updated += 1
                            summary.rows.append(
                                RowResult(
                                    row_number, parsed.source_key, "updated", source_id=str(existing.id)
                                )
                            )
                        else:
                            summary.unchanged += 1
                            summary.rows.append(
                                RowResult(
                                    row_number, parsed.source_key, "unchanged",
                                    source_id=str(existing.id),
                                )
                            )
            except DomainError as exc:
                summary.rejected += 1
                summary.rows.append(
                    RowResult(row_number, parsed.source_key, "rejected", reason=exc.message)
                )

        return summary
