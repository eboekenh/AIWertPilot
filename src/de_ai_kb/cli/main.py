"""Typer CLI. Calls the same services as the API — no duplicated logic."""

from __future__ import annotations

import asyncio
import csv
import uuid
from collections.abc import Coroutine
from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console
from rich.table import Table
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from de_ai_kb.core.config import get_settings
from de_ai_kb.core.exceptions import DomainError, NotFoundError
from de_ai_kb.db.models.sources import Source
from de_ai_kb.db.session import get_sessionmaker
from de_ai_kb.domain.enums import FreshnessState, SourceStatus
from de_ai_kb.repositories.review import ReviewItemFilters, ReviewItemRepository
from de_ai_kb.services.claims_validation import ClaimsValidationService, ClaimsValidationSummary
from de_ai_kb.services.dedup import DuplicateDetectionService
from de_ai_kb.services.freshness import FreshnessService
from de_ai_kb.services.seed_import import SeedImportService, SeedImportSummary
from de_ai_kb.services.source_registry import SourceRegistryService
from de_ai_kb.services.taxonomy_seed import TaxonomySeedService

app = typer.Typer(no_args_is_help=True, add_completion=False)
db_app = typer.Typer(no_args_is_help=True)
sources_app = typer.Typer(no_args_is_help=True)
review_app = typer.Typer(no_args_is_help=True)
claims_app = typer.Typer(no_args_is_help=True)
app.add_typer(db_app, name="db")
app.add_typer(sources_app, name="sources")
app.add_typer(review_app, name="review")
app.add_typer(claims_app, name="claims")

console = Console()
_REPO_ROOT = Path(__file__).resolve().parents[3]


def _run[T](coro: Coroutine[Any, Any, T]) -> T:
    return asyncio.run(coro)


@db_app.command("check")
def db_check() -> None:
    """Verify DB connectivity and report the current Alembic revision."""

    async def _check() -> str | None:
        settings = get_settings()
        session_factory = get_sessionmaker(settings.database_url)
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
            result = await session.execute(text("SELECT version_num FROM alembic_version"))
            row = result.first()
            return row[0] if row else None

    current = _run(_check())
    console.print(f"[green]Database reachable.[/green] Current revision: {current or '(none)'}")


@db_app.command("init")
def db_init() -> None:
    """Best-effort creation of required extensions, then report readiness."""

    async def _init() -> None:
        settings = get_settings()
        session_factory = get_sessionmaker(settings.database_url)
        async with session_factory() as session:
            for ext in ("pgcrypto", "vector"):
                try:
                    await session.execute(text(f"CREATE EXTENSION IF NOT EXISTS {ext}"))
                    await session.commit()
                    console.print(f"[green]Extension {ext} available.[/green]")
                except Exception as exc:  # noqa: BLE001
                    await session.rollback()
                    console.print(
                        f"[yellow]Could not create extension {ext} ({exc}); "
                        f"it may already exist or require superuser — continuing.[/yellow]"
                    )

    _run(_init())


@db_app.command("migrate")
def db_migrate() -> None:
    """Run `alembic upgrade head`."""
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(_REPO_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(_REPO_ROOT / "migrations"))
    command.upgrade(cfg, "head")
    console.print("[green]Migrations applied (head).[/green]")


@db_app.command("seed-taxonomy")
def db_seed_taxonomy() -> None:
    """Idempotently seed the business_processes reference vocabulary."""

    async def _seed() -> tuple[int, int]:
        settings = get_settings()
        session_factory = get_sessionmaker(settings.database_url)
        async with session_factory() as session, session.begin():
            service = TaxonomySeedService(session)
            return await service.seed_business_processes()

    inserted, unchanged = _run(_seed())
    console.print(f"business_processes: inserted={inserted} unchanged={unchanged}")


def _print_import_summary(summary: SeedImportSummary) -> None:
    table = Table(title=f"Seed import ({'dry-run' if summary.dry_run else 'applied'})")
    table.add_column("metric")
    table.add_column("count", justify="right")
    table.add_row("total_rows", str(summary.total_rows))
    table.add_row("inserted", str(summary.inserted))
    table.add_row("updated", str(summary.updated))
    table.add_row("unchanged", str(summary.unchanged))
    table.add_row("rejected", str(summary.rejected))
    table.add_row("review_items_created", str(summary.review_items_created))
    console.print(table)
    rejected_rows = [r for r in summary.rows if r.outcome == "rejected"]
    if rejected_rows:
        rej_table = Table(title="Rejected rows")
        rej_table.add_column("row")
        rej_table.add_column("source_key")
        rej_table.add_column("reason")
        for r in rejected_rows:
            rej_table.add_row(str(r.row_number), r.source_key, r.reason or "")
        console.print(rej_table)


@sources_app.command("import")
def sources_import(
    file: Annotated[Path, typer.Option(help="CSV file to import")] = Path("data/seed_sources.csv"),
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
    actor: Annotated[str, typer.Option(help="Actor id recorded in audit events")] = "cli",
) -> None:
    """Import seed_sources.csv. Idempotent; supports --dry-run."""

    async def _import() -> SeedImportSummary:
        settings = get_settings()
        session_factory: async_sessionmaker[AsyncSession] = get_sessionmaker(settings.database_url)
        service = SeedImportService(session_factory)
        return await service.import_csv(file, dry_run=dry_run, actor_id=actor)

    summary = _run(_import())
    _print_import_summary(summary)


@sources_app.command("validate")
def sources_validate(
    file: Annotated[Path, typer.Option(help="CSV file to validate")] = Path("data/seed_sources.csv"),
) -> None:
    """Validate a source CSV without writing anything (alias of import --dry-run
    that also surfaces row-level validation reasons in detail)."""

    async def _validate() -> SeedImportSummary:
        settings = get_settings()
        session_factory: async_sessionmaker[AsyncSession] = get_sessionmaker(settings.database_url)
        service = SeedImportService(session_factory)
        return await service.import_csv(file, dry_run=True, actor_id="cli")

    summary = _run(_validate())
    _print_import_summary(summary)
    if summary.rejected:
        raise typer.Exit(code=1)


@sources_app.command("duplicates")
def sources_duplicates(
    actor: Annotated[str, typer.Option(help="Actor id recorded in audit events")] = "cli",
) -> None:
    """Scan the registry for duplicate candidates and create review items.
    Never merges automatically."""
    from de_ai_kb.services.dedup import DuplicateCandidate

    async def _scan() -> list[DuplicateCandidate]:
        settings = get_settings()
        session_factory = get_sessionmaker(settings.database_url)
        async with session_factory() as session, session.begin():
            service = DuplicateDetectionService(session)
            return await service.scan_all(actor_id=actor)

    candidates = _run(_scan())
    table = Table(title="Duplicate candidates")
    table.add_column("source_id")
    table.add_column("counterpart_source_id")
    table.add_column("score")
    table.add_column("reason")
    for c in candidates:
        table.add_row(str(c.source_id), str(c.counterpart_source_id), f"{c.similarity_score:.3f}", c.reason)
    console.print(table)
    console.print(f"[bold]{len(candidates)} duplicate candidate(s) found.[/bold]")


@sources_app.command("stale")
def sources_stale(
    state: Annotated[str, typer.Option(help="fresh|due_soon|stale|unknown|all")] = "all",
) -> None:
    """Report source freshness states."""
    from de_ai_kb.services.freshness import FreshnessReportItem

    async def _report() -> list[FreshnessReportItem]:
        settings = get_settings()
        session_factory = get_sessionmaker(settings.database_url)
        async with session_factory() as session:
            service = FreshnessService(session)
            state_filter = None if state == "all" else FreshnessState(state)
            return await service.report(state_filter=state_filter)

    items = _run(_report())
    table = Table(title=f"Freshness report ({state})")
    table.add_column("source_key")
    table.add_column("title")
    table.add_column("last_verified_at")
    table.add_column("refresh_days")
    table.add_column("state")
    for item in items:
        table.add_row(
            item.source_key,
            item.title[:60],
            str(item.last_verified_at) if item.last_verified_at else "(never)",
            str(item.refresh_interval_days),
            item.freshness_state.value,
        )
    console.print(table)
    console.print(f"[bold]{len(items)} source(s).[/bold]")


async def _resolve_source_id(service: SourceRegistryService, identifier: str) -> uuid.UUID:
    """Accept either a source_key or a UUID id, as documented for the
    `sources transition`/`sources block` commands."""
    try:
        return uuid.UUID(identifier)
    except ValueError:
        pass
    source = await service.get_by_source_key(identifier)
    if source is None:
        raise NotFoundError(f"no source found with source_key or id {identifier!r}")
    return source.id


@sources_app.command("transition")
def sources_transition(
    identifier: Annotated[str, typer.Argument(help="source_key or UUID id")],
    status: Annotated[str, typer.Option("--status", help="target lifecycle status")],
    reason: Annotated[str | None, typer.Option("--reason", help="recorded in the audit trail")] = None,
    actor: Annotated[str, typer.Option(help="Actor id recorded in audit events")] = "cli",
) -> None:
    """Transition a source's lifecycle status. The only supported way to
    change status — invalid transitions are rejected."""
    try:
        target_status = SourceStatus(status)
    except ValueError as exc:
        console.print(f"[red]invalid_status: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    async def _transition() -> Source:
        settings = get_settings()
        session_factory = get_sessionmaker(settings.database_url)
        async with session_factory() as session, session.begin():
            service = SourceRegistryService(session)
            source_id = await _resolve_source_id(service, identifier)
            return await service.transition_status(
                source_id=source_id, new_status=target_status, reason=reason, actor_id=actor
            )

    try:
        source = _run(_transition())
    except DomainError as exc:
        console.print(f"[red]{exc.code}: {exc.message}[/red]")
        raise typer.Exit(code=1) from exc

    console.print(f"[green]Source {source.source_key} transitioned to {source.status}.[/green]")


@sources_app.command("block")
def sources_block(
    identifier: Annotated[str, typer.Argument(help="source_key or UUID id")],
    reason: Annotated[str, typer.Option("--reason", help="mandatory, non-blank takedown reason")],
    actor: Annotated[str, typer.Option(help="Actor id recorded in audit events")] = "cli",
) -> None:
    """Block (takedown) a source. A non-blank reason is mandatory and is
    always recorded in the audit trail alongside the status change."""

    async def _block() -> Source:
        settings = get_settings()
        session_factory = get_sessionmaker(settings.database_url)
        async with session_factory() as session, session.begin():
            service = SourceRegistryService(session)
            source_id = await _resolve_source_id(service, identifier)
            return await service.block_source(source_id=source_id, reason=reason, actor_id=actor)

    try:
        source = _run(_block())
    except DomainError as exc:
        console.print(f"[red]{exc.code}: {exc.message}[/red]")
        raise typer.Exit(code=1) from exc

    console.print(f"[green]Source {source.source_key} blocked.[/green]")


@review_app.command("export")
def review_export(
    out: Annotated[Path, typer.Option(help="Output CSV path")] = Path("review_items_export.csv"),
    status: Annotated[str | None, typer.Option(help="Filter by status")] = None,
    review_type: Annotated[str | None, typer.Option(help="Filter by review_type")] = None,
) -> None:
    """Export review items as CSV for external reviewers."""
    from de_ai_kb.db.models.ops import ReviewItem

    async def _export() -> list[ReviewItem]:
        settings = get_settings()
        session_factory = get_sessionmaker(settings.database_url)
        async with session_factory() as session:
            repo = ReviewItemRepository(session)
            filters = ReviewItemFilters(status=status, review_type=review_type)
            return await repo.list_all(filters=filters)

    items = _run(_export())
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "id",
                "entity_type",
                "entity_id",
                "review_type",
                "status",
                "priority",
                "assigned_to",
                "created_at",
            ]
        )
        for item in items:
            writer.writerow(
                [
                    str(item.id),
                    item.entity_type,
                    str(item.entity_id),
                    item.review_type,
                    item.status,
                    item.priority,
                    item.assigned_to or "",
                    item.created_at.isoformat(),
                ]
            )
    console.print(f"[green]Exported {len(items)} review item(s) to {out}[/green]")


@claims_app.command("validate")
def claims_validate(
    file: Annotated[Path, typer.Option(help="CSV file to validate")] = Path("data/seed_claims.csv"),
) -> None:
    """Validate seed_claims.csv. Never imports/publishes claims in this
    release — see docs/NEXT_RELEASES.md for the Release 2/3 import path."""

    async def _validate() -> ClaimsValidationSummary:
        settings = get_settings()
        session_factory = get_sessionmaker(settings.database_url)
        async with session_factory() as session:
            service = ClaimsValidationService(session)
            return await service.validate_csv(file)

    summary = _run(_validate())
    table = Table(title="Claims validation (no rows written)")
    table.add_column("metric")
    table.add_column("count", justify="right")
    table.add_row("total_rows", str(summary.total_rows))
    table.add_row("valid", str(summary.valid))
    table.add_row("invalid", str(summary.invalid))
    table.add_row("duplicate_claim_keys", str(len(summary.duplicate_claim_keys)))
    table.add_row("unresolved_source_keys", str(len(summary.unresolved_source_keys)))
    table.add_row("claims_written", str(summary.claims_written))
    table.add_row("claim_evidence_written", str(summary.claim_evidence_written))
    console.print(table)
    invalid_rows = [r for r in summary.rows if not r.valid]
    if invalid_rows:
        inv_table = Table(title="Invalid rows")
        inv_table.add_column("row")
        inv_table.add_column("claim_key")
        inv_table.add_column("reasons")
        for r in invalid_rows:
            inv_table.add_row(str(r.row_number), r.claim_key, "; ".join(r.reasons))
        console.print(inv_table)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
