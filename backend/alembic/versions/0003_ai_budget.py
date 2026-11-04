"""Bounded optional AI usage reservations, never guest state."""

from pathlib import Path

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute((Path(__file__).resolve().parents[2] / "migrations" / "0004_ai_budget.sql").read_text(encoding="utf-8"))


def downgrade() -> None:
    raise RuntimeError("Do not reset consumed AI budgets through a downgrade; restore explicitly when appropriate.")
