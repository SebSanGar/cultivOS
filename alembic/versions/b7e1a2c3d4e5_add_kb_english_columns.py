"""add knowledge-base English (*_en) columns

Bilingual layer (B4): English siblings for the Spanish-only KB text so the app
renders fully in English. Idempotent — checks for existing columns first, so it
is safe whether the DB was built by alembic OR by create_all (which already adds
these columns on fresh DBs).

Revision ID: b7e1a2c3d4e5
Revises: 0b1a2c3d4e5f
Create Date: 2026-06-10
"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "b7e1a2c3d4e5"
down_revision: Union[str, None] = "0b1a2c3d4e5f"
branch_labels = None
depends_on = None

# table -> [(column, type), ...]
_COLUMNS = {
    "ancestral_methods": [
        ("description_en", sa.Text()),
        ("benefits_en", sa.Text()),
        ("scientific_basis_en", sa.Text()),
    ],
    "fertilizers": [
        ("description_en", sa.Text()),
        ("application_method_en", sa.Text()),
        ("nutrient_profile_en", sa.String(200)),
    ],
    "diseases": [
        ("description_en", sa.Text()),
    ],
    "crop_types": [
        ("growing_season_en", sa.String(100)),
        ("description_en", sa.Text()),
    ],
}


def _existing_columns(table: str) -> set:
    insp = sa.inspect(op.get_bind())
    if table not in insp.get_table_names():
        return set()
    return {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    for table, cols in _COLUMNS.items():
        have = _existing_columns(table)
        if not have:  # table absent (shouldn't happen post-baseline) — skip safely
            continue
        for name, type_ in cols:
            if name not in have:
                op.add_column(table, sa.Column(name, type_, nullable=True))


def downgrade() -> None:
    for table, cols in _COLUMNS.items():
        have = _existing_columns(table)
        for name, _ in cols:
            if name in have:
                try:
                    op.drop_column(table, name)
                except Exception:
                    pass
