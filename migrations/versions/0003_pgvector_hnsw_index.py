"""Deviation: HNSW index on document_chunks.embedding.

Not present in schema.sql (which specifies the vector(1536) column but no
index). IVFFlat is not chosen because its `lists` parameter needs an
existing row-count/distribution to tune well, and document_chunks is empty
in Foundation Release 1 (ingestion is Release 2). HNSW builds incrementally
with reasonable defaults and does not degrade with zero rows, so it is the
safer default to ship now. Uses the cosine-distance operator class since
retrieval in later releases is expected to rank by cosine similarity. See
docs/ADR-001-architecture.md.

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-18

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX ix_document_chunks_embedding_hnsw ON document_chunks "
        "USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding_hnsw;")
