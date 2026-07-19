"""CLI-level coverage for the `sources transition`/`sources block` guards.

Only the guards that run before any database access are exercised here
(the CLI resolves its own DB session from Settings.database_url, not
test_database_url, so a full DB-backed CLI invocation is out of scope for
this suite — see tests/integration/test_source_registry.py for
DB-backed, direct-service coverage of the same actor_type="cli" audit
provenance and BLOCKED-transition-reason behavior the CLI commands rely on).
"""

from __future__ import annotations

from typer.testing import CliRunner

from de_ai_kb.cli.main import app

runner = CliRunner()


def test_sources_transition_rejects_blocked_status() -> None:
    """The CLI must reject `--status blocked` before ever touching the
    database, directing the caller to `sources block` instead."""
    result = runner.invoke(app, ["sources", "transition", "SOME_SOURCE", "--status", "blocked"])
    assert result.exit_code == 1
    assert "sources block" in result.output


def test_sources_transition_rejects_unknown_status() -> None:
    result = runner.invoke(app, ["sources", "transition", "SOME_SOURCE", "--status", "not_a_status"])
    assert result.exit_code == 1
    assert "invalid_status" in result.output
