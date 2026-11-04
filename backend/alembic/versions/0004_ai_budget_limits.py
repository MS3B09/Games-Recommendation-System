"""Owner-approved daily AI ceilings; preserve all consumed usage."""

from pathlib import Path

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute((Path(__file__).resolve().parents[2] / "migrations" / "0005_ai_budget_limits.sql").read_text(encoding="utf-8"))


def downgrade() -> None:
    raise RuntimeError("Do not discard consumed usage to lower AI limits; configure lower runtime ceilings instead.")
