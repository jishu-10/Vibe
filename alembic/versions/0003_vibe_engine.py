"""Add versioned Vibe profiles and explicit pair results."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003_vibe_engine"
down_revision = "0002_version_snapshots"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vibe_profiles",
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("profile_version", sa.String(length=128), nullable=False),
        sa.Column("answers", sa.JSON(), nullable=False),
        sa.Column("signals", sa.JSON(), nullable=False),
        sa.Column("derived", sa.JSON(), nullable=False),
        sa.Column("facts", sa.JSON(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.JSON(), nullable=False),
        sa.Column("profile_narrative", sa.JSON(), nullable=True),
        sa.Column("engine_versions", sa.JSON(), nullable=False),
        sa.Column("config_hash", sa.String(length=128), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table(
        "vibe_pair_results",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("sorted_user_a_id", sa.String(length=64), nullable=False),
        sa.Column("sorted_user_b_id", sa.String(length=64), nullable=False),
        sa.Column("request_user_a_id", sa.String(length=64), nullable=False),
        sa.Column("request_user_b_id", sa.String(length=64), nullable=False),
        sa.Column("relationship_mode", sa.String(length=16), nullable=False),
        sa.Column("cache_key", sa.String(length=128), nullable=False),
        sa.Column("user_a_profile_version", sa.String(length=128), nullable=False),
        sa.Column("user_b_profile_version", sa.String(length=128), nullable=False),
        sa.Column("engine_versions", sa.JSON(), nullable=False),
        sa.Column("deterministic_result", sa.JSON(), nullable=False),
        sa.Column("public_response", sa.JSON(), nullable=False),
        sa.Column("approach", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["sorted_user_a_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["sorted_user_b_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cache_key"),
    )


def downgrade() -> None:
    op.drop_table("vibe_pair_results")
    op.drop_table("vibe_profiles")

