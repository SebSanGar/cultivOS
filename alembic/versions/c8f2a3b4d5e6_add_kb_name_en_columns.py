"""add knowledge-base English name (name_en) columns

Bilingual layer (B4 follow-up): KB entity NAMES (technique, fertilizer,
disease) stayed Spanish in EN mode — only descriptions had _en variants.
Idempotent — checks for existing columns first, so it is safe whether the
DB was built by alembic OR by create_all (which already adds these columns
on fresh DBs).

Revision ID: c8f2a3b4d5e6
Revises: b7e1a2c3d4e5
Create Date: 2026-06-11
"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "c8f2a3b4d5e6"
down_revision: Union[str, None] = "b7e1a2c3d4e5"
branch_labels = None
depends_on = None

_TABLES = ["ancestral_methods", "fertilizers", "diseases"]


def _existing_columns(table: str) -> set:
    insp = sa.inspect(op.get_bind())
    if table not in insp.get_table_names():
        return set()
    return {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    for table in _TABLES:
        have = _existing_columns(table)
        if not have:  # table absent (shouldn't happen post-baseline) — skip safely
            continue
        if "name_en" not in have:
            op.add_column(table, sa.Column("name_en", sa.String(150), nullable=True))


def downgrade() -> None:
    for table in _TABLES:
        if "name_en" in _existing_columns(table):
            try:
                op.drop_column(table, "name_en")
            except Exception:
                pass
