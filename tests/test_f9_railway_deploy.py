"""
F9 — Railway deploy tests.
Covers:
- DATABASE_URL env var (Railway convention) overrides db_url in Settings
- DB_URL env var backward-compatibility still works
- railway.toml has healthcheck at /api/health + startCommand with alembic
- psycopg2-binary present in requirements.txt
- alembic upgrade head / downgrade base roundtrip on fresh SQLite
"""

import os
import subprocess
import tomllib
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# Settings env-var tests
# ---------------------------------------------------------------------------


def test_database_url_env_var_overrides_db_url(monkeypatch):
    """DATABASE_URL (Railway Postgres add-on convention) must be accepted as db_url."""
    from cultivos.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/cultivOS")
    monkeypatch.delenv("DB_URL", raising=False)
    try:
        settings = get_settings()
        assert settings.db_url == "postgresql://user:pass@localhost/cultivOS", (
            f"DATABASE_URL not picked up; got {settings.db_url!r}"
        )
    finally:
        get_settings.cache_clear()


def test_db_url_env_var_backward_compat(monkeypatch):
    """DB_URL env var must still work after DATABASE_URL support is added."""
    from cultivos.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("DB_URL", "sqlite:///local.db")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    try:
        settings = get_settings()
        assert settings.db_url == "sqlite:///local.db", (
            f"DB_URL not respected; got {settings.db_url!r}"
        )
    finally:
        get_settings.cache_clear()


def test_db_url_takes_precedence_over_database_url(monkeypatch):
    """When both DB_URL and DATABASE_URL set, DB_URL wins (explicit local override)."""
    from cultivos.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("DB_URL", "sqlite:///local.db")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/cultivOS")
    try:
        settings = get_settings()
        assert settings.db_url == "sqlite:///local.db", (
            f"DB_URL should win over DATABASE_URL; got {settings.db_url!r}"
        )
    finally:
        get_settings.cache_clear()


# ---------------------------------------------------------------------------
# railway.toml config tests
# ---------------------------------------------------------------------------


def test_railway_toml_has_healthcheck():
    """railway.toml must declare a healthcheck at /api/health."""
    toml_path = PROJECT_ROOT / "railway.toml"
    assert toml_path.exists(), "railway.toml not found"
    with open(toml_path, "rb") as f:
        config = tomllib.load(f)
    deploy = config.get("deploy", {})
    assert "healthcheck" in deploy, (
        "Missing [deploy.healthcheck] in railway.toml"
    )
    healthcheck = deploy["healthcheck"]
    assert healthcheck.get("path") == "/api/health", (
        f"Healthcheck path must be /api/health; got {healthcheck.get('path')!r}"
    )


def test_railway_toml_start_command_includes_alembic():
    """railway.toml startCommand must run alembic upgrade head before starting server."""
    toml_path = PROJECT_ROOT / "railway.toml"
    with open(toml_path, "rb") as f:
        config = tomllib.load(f)
    start_cmd = config.get("deploy", {}).get("startCommand", "")
    assert start_cmd, "Missing startCommand in [deploy] section of railway.toml"
    assert "alembic" in start_cmd, (
        f"startCommand must invoke alembic; got {start_cmd!r}"
    )
    assert "upgrade" in start_cmd, (
        f"startCommand must run alembic upgrade; got {start_cmd!r}"
    )


# ---------------------------------------------------------------------------
# requirements.txt test
# ---------------------------------------------------------------------------


def test_psycopg2_in_requirements():
    """psycopg2-binary must be in requirements.txt for Postgres support on Railway."""
    req_path = PROJECT_ROOT / "requirements.txt"
    content = req_path.read_text()
    assert "psycopg2" in content, (
        "psycopg2-binary not found in requirements.txt — needed for Railway Postgres"
    )


# ---------------------------------------------------------------------------
# Alembic migration roundtrip
# ---------------------------------------------------------------------------


def test_alembic_upgrade_downgrade_roundtrip(tmp_path):
    """alembic upgrade head then downgrade base must both succeed on fresh SQLite."""
    db_file = tmp_path / "alembic_test.db"
    env = os.environ.copy()
    env["DB_URL"] = f"sqlite:///{db_file}"
    env.pop("DATABASE_URL", None)
    # Clear lru_cache so alembic env picks up the new DB_URL
    # (alembic runs in subprocess so cache isolation is automatic)

    result_up = subprocess.run(
        ["alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(PROJECT_ROOT),
    )
    assert result_up.returncode == 0, (
        f"alembic upgrade head failed:\nSTDOUT: {result_up.stdout}\nSTDERR: {result_up.stderr}"
    )
    assert db_file.exists(), "DB file not created after alembic upgrade head"

    result_down = subprocess.run(
        ["alembic", "downgrade", "base"],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(PROJECT_ROOT),
    )
    assert result_down.returncode == 0, (
        f"alembic downgrade base failed:\nSTDOUT: {result_down.stdout}\nSTDERR: {result_down.stderr}"
    )
