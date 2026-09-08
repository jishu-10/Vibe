"""Add Vibe pair observability metadata."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0004_vibe_observability"
down_revision = "0003_vibe_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("vibe_pair_results", sa.Column("request_id", sa.String(length=36), nullable=True))
    op.add_column("vibe_pair_results", sa.Column("cache_hit", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("vibe_pair_results", sa.Column("spec_error_path", sa.String(length=256), nullable=True))


def downgrade() -> None:
    op.drop_column("vibe_pair_results", "spec_error_path")
    op.drop_column("vibe_pair_results", "cache_hit")
    op.drop_column("vibe_pair_results", "request_id")
