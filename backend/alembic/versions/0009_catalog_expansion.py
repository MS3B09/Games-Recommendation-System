"""Versioned dashboard source documents and complete normalized title identities."""

import unicodedata
from pathlib import Path

from alembic import op
from sqlalchemy import text

revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute((Path(__file__).resolve().parents[2] / 'migrations/0010_catalog_expansion.sql').read_text(encoding='utf-8'))
    if op.get_context().as_sql:
        op.execute('-- Existing title-key backfill requires the online Python migration CLI.')
        return
    connection = op.get_bind()
    updates = []
    for version, app_id, title in connection.execute(text('select version,app_id,title from discovery.games')):
        folded = unicodedata.normalize('NFKC', title).casefold()
        folded = ''.join(c for c in folded if c not in "'’‘ʼ")
        normalized = ' '.join(''.join(c if c.isalnum() else ' ' for c in folded).split())
        updates.append({'v': version, 'id': app_id, 'title': normalized,
                        'compact': normalized.replace(' ', ''), 'tokens': normalized.split()})
    if updates:
        connection.execute(text('update discovery.games set identity_title=:title,compact_title=:compact,title_tokens=:tokens where version=:v and app_id=:id'), updates)


def downgrade() -> None:
    raise RuntimeError('No destructive catalog downgrade; roll back to a compatible application/catalog version instead')
