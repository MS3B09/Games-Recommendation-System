"""Bounded legacy card import capacity and explicit private-table policy."""
from pathlib import Path
from alembic import op

revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute((Path(__file__).resolve().parents[2] / 'migrations' / '0009_archive_bootstrap_capacity.sql').read_text(encoding='utf-8'))


def downgrade() -> None:
    op.execute('drop policy conversation_archives_private on discovery.conversation_archives')
    original = (Path(__file__).resolve().parents[2] / 'migrations' / '0008_conversation_archive.sql').read_text(encoding='utf-8')
    start = original.index('create function discovery.conversation_create')
    end = original.index('create function discovery.conversation_read')
    op.execute(original[start:end].replace('create function', 'create or replace function', 1))
    # Existing complete imports are retained; only new admission changes.
