"""add Farm.tier column to farms table

Revision ID: 0b1a2c3d4e5f
Revises: 0a265488d88f
Create Date: 2026-06-10

WHY: Farm.tier was added to the ORM model after the baseline migration was
created. Existing (non-fresh) databases — including Railway/prod — do not have
this column and will 500 on any query that reads or writes it. This migration
makes the column available to all deployed instances.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0b1a2c3d4e5f"
down_revision: Union[str, None] = "0a265488d88f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("farms", sa.Column("tier", sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column("farms", "tier")
