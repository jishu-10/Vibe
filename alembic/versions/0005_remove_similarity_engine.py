"""Remove the retired similarity engine schema from existing databases."""

from __future__ import annotations

from alembic import op


revision = "0005_remove_similarity_engine"
down_revision = "0004_vibe_observability"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop dependents before their referenced legacy tables.  These tables are
    # historical schema only; no active Vibe model or route reads them.
    for table in (
        "similarity_explanations",
        "similarity_evidence",
        "similarity_area_results",
        "similarity_results",
        "signal_observations",
        "user_signals",
        "responses",
        "option_signal_mappings",
        "prompt_options",
        "prompts",
        "signals",
        "similarity_areas",
    ):
        op.drop_table(table)
    op.drop_column("users", "profile_completion")


def downgrade() -> None:
    raise RuntimeError("The retired similarity schema cannot be restored after Vibe-only cleanup.")
