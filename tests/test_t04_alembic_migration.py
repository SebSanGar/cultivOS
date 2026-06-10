"""T0.4 alembic migration tests — add tier column to farms table.

Tests that the migration adds `tier VARCHAR(50)` to an existing farms table
(i.e. a non-fresh DB that was created before this column existed).
"""
import sqlite3

import pytest
import sqlalchemy as sa
from alembic.runtime.migration import MigrationContext
from alembic.operations import Operations


def _cols(db_path: str, table: str) -> list[str]:
    """Return column names for a table via SQLite PRAGMA."""
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(f"PRAGMA table_info({table})")
    names = [row[1] for row in cursor.fetchall()]
    conn.close()
    return names


def _nonfresh_db(db_path: str) -> None:
    """Create a farms table WITHOUT the tier column (pre-migration state)."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE farms (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            owner_name VARCHAR(100),
            location_lat FLOAT,
            location_lon FLOAT,
            total_hectares FLOAT,
            municipality VARCHAR(100),
            state VARCHAR(50),
            country VARCHAR(10),
            cooperative_id INTEGER,
            created_at DATETIME
        )
    """)
    conn.execute("INSERT INTO farms (id, name) VALUES (1, 'Rancho Don Manuel')")
    conn.commit()
    conn.close()


def _apply_upgrade(db_path: str) -> None:
    """Apply the migration's upgrade() logic: add tier column."""
    engine = sa.create_engine(f"sqlite:///{db_path}")
    with engine.begin() as connection:
        ctx = MigrationContext.configure(connection)
        ops = Operations(ctx)
        ops.add_column("farms", sa.Column("tier", sa.String(length=50), nullable=True))


def _apply_downgrade(db_path: str) -> None:
    """Apply the migration's downgrade() logic: drop tier column."""
    engine = sa.create_engine(f"sqlite:///{db_path}")
    with engine.begin() as connection:
        ctx = MigrationContext.configure(connection)
        ops = Operations(ctx)
        ops.drop_column("farms", "tier")


class TestT04AlembicMigration:
    def test_tier_absent_before_migration(self, tmp_path):
        """Pre-condition: baseline farms table has no tier column."""
        db_path = str(tmp_path / "premigration.db")
        _nonfresh_db(db_path)
        assert "tier" not in _cols(db_path, "farms")

    def test_upgrade_adds_tier_to_existing_farms_table(self, tmp_path):
        """upgrade() adds tier column to a non-fresh DB that lacks it."""
        db_path = str(tmp_path / "upgrade.db")
        _nonfresh_db(db_path)
        _apply_upgrade(db_path)
        assert "tier" in _cols(db_path, "farms")

    def test_upgrade_preserves_existing_farm_rows(self, tmp_path):
        """upgrade() does not destroy pre-existing farm rows."""
        db_path = str(tmp_path / "preserve.db")
        _nonfresh_db(db_path)
        _apply_upgrade(db_path)
        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT id, name, tier FROM farms WHERE id=1").fetchone()
        conn.close()
        assert row[0] == 1
        assert row[1] == "Rancho Don Manuel"
        assert row[2] is None  # existing rows get NULL for the new column

    def test_upgrade_tier_column_is_nullable(self, tmp_path):
        """tier column is nullable — farms without a subscription tier should be insertable."""
        db_path = str(tmp_path / "nullable.db")
        _nonfresh_db(db_path)
        _apply_upgrade(db_path)
        conn = sqlite3.connect(db_path)
        conn.execute("INSERT INTO farms (id, name, tier) VALUES (2, 'Nueva Granja', NULL)")
        conn.commit()
        row = conn.execute("SELECT tier FROM farms WHERE id=2").fetchone()
        conn.close()
        assert row[0] is None

    def test_upgrade_tier_column_accepts_string_values(self, tmp_path):
        """tier column accepts string tier values like 'basico', 'premium'."""
        db_path = str(tmp_path / "values.db")
        _nonfresh_db(db_path)
        _apply_upgrade(db_path)
        conn = sqlite3.connect(db_path)
        conn.execute("INSERT INTO farms (id, name, tier) VALUES (3, 'Granja Pro', 'premium')")
        conn.commit()
        row = conn.execute("SELECT tier FROM farms WHERE id=3").fetchone()
        conn.close()
        assert row[0] == "premium"

    def test_downgrade_removes_tier_column(self, tmp_path):
        """downgrade() removes tier column (full round-trip)."""
        db_path = str(tmp_path / "roundtrip.db")
        _nonfresh_db(db_path)
        _apply_upgrade(db_path)
        assert "tier" in _cols(db_path, "farms")
        _apply_downgrade(db_path)
        assert "tier" not in _cols(db_path, "farms")

    def test_migration_file_exists(self):
        """The alembic migration file for tier must exist in alembic/versions/."""
        import os
        versions_dir = os.path.join(
            os.path.dirname(__file__), "..", "alembic", "versions"
        )
        migration_files = os.listdir(versions_dir)
        tier_migrations = [f for f in migration_files if "farm_tier" in f and f.endswith(".py")]
        assert len(tier_migrations) == 1, (
            f"Expected exactly 1 migration file for farm_tier, found: {tier_migrations}"
        )
