"""Temporary owner-approved R4 capacity; retain consumed usage and all guards."""

from pathlib import Path

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute((Path(__file__).resolve().parents[2] / "migrations" / "0006_r4_ai_budget_limits.sql").read_text(encoding="utf-8"))


def downgrade() -> None:
    raise RuntimeError("Restore lower runtime limits after R4; never discard consumed usage or lower constraints over it.")
