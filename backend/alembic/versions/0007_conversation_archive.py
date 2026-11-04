"""Independent capability-protected guest conversation archive."""
from pathlib import Path
from alembic import op

revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute((Path(__file__).resolve().parents[2] / 'migrations' / '0008_conversation_archive.sql').read_text(encoding='utf-8'))


def downgrade() -> None:
    op.execute('drop function discovery.conversation_delete(uuid,text), discovery.conversation_finish(uuid,text,uuid,jsonb,jsonb,jsonb), discovery.conversation_begin(uuid,text,uuid,integer,text), discovery.conversation_read(uuid,text), discovery.conversation_create(uuid,text,jsonb)')
    op.execute('drop table discovery.conversation_archives')
