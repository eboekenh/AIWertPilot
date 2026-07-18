"""Deviation: add review_items.metadata (documented supplemental payload).

Not present in schema.sql. Carries only supplemental review context (e.g. a
dedup candidate's counterpart source_id and similarity score for
review_type='dedup_candidate'); primary searchable fields on review_items
(entity_type, entity_id, review_type, status, priority, assigned_to,
decision_reason) remain plain columns, unchanged from schema.sql. See
docs/ADR-001-architecture.md and docs/DATA_DICTIONARY.md.

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-18

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE review_items ADD COLUMN metadata jsonb NOT NULL DEFAULT '{}'::jsonb;"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE review_items DROP COLUMN metadata;")
