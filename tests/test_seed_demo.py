"""Tests for the demo data seeder script."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from cultivos.db.models import (
    Base, Farm, Field, HealthScore, SoilAnalysis,
    NDVIResult, ThermalResult, TreatmentRecord, WeatherRecord,
)


@pytest.fixture
def seed_db():
    """Fresh in-memory DB for seeder tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def _run_seed(session):
    """Import and run the seeder with the given session."""
    from scripts.seed_demo import seed_demo_data
    seed_demo_data(session)


class TestSeedDemoRuns:
    """Seeder runs without error and creates expected data."""

    def test_runs_without_error(self, seed_db):
        _run_seed(seed_db)

    def test_creates_three_farms(self, seed_db):
        _run_seed(seed_db)
        assert seed_db.query(Farm).count() == 3

    def test_creates_fields_per_farm(self, seed_db):
        _run_seed(seed_db)
        farms = seed_db.query(Farm).all()
        for farm in farms:
            assert len(farm.fields) >= 2, f"Farm '{farm.name}' has fewer than 2 fields"

    def test_creates_ndvi_results(self, seed_db):
        _run_seed(seed_db)
        # Each field should have 5+ NDVI results
        fields = seed_db.query(Field).all()
        for field in fields:
            count = seed_db.query(NDVIResult).filter_by(field_id=field.id).count()
            assert count >= 5, f"Field '{field.name}' has only {count} NDVI results (need 5+)"

    def test_creates_soil_analyses(self, seed_db):
        _run_seed(seed_db)
        assert seed_db.query(SoilAnalysis).count() > 0

    def test_creates_thermal_results(self, seed_db):
        _run_seed(seed_db)
        assert seed_db.query(ThermalResult).count() > 0

    def test_creates_health_scores(self, seed_db):
        _run_seed(seed_db)
        assert seed_db.query(HealthScore).count() > 0

    def test_creates_treatments(self, seed_db):
        _run_seed(seed_db)
        assert seed_db.query(TreatmentRecord).count() > 0

    def test_creates_weather_records(self, seed_db):
        _run_seed(seed_db)
        assert seed_db.query(WeatherRecord).count() > 0

    def test_health_scores_show_improvement(self, seed_db):
        """Health scores over time should trend upward (improving)."""
        _run_seed(seed_db)
        fields = seed_db.query(Field).all()
        improving_count = 0
        for field in fields:
            scores = (
                seed_db.query(HealthScore)
                .filter_by(field_id=field.id)
                .order_by(HealthScore.scored_at)
                .all()
            )
            if len(scores) >= 2 and scores[-1].score > scores[0].score:
                improving_count += 1
        # At least half the fields should show improvement
        assert improving_count >= len(fields) // 2


class TestSeedDemoIdempotent:
    """Running the seeder twice should not duplicate data."""

    def test_idempotent_farm_count(self, seed_db):
        _run_seed(seed_db)
        count_first = seed_db.query(Farm).count()
        _run_seed(seed_db)
        count_second = seed_db.query(Farm).count()
        assert count_first == count_second

    def test_idempotent_field_count(self, seed_db):
        _run_seed(seed_db)
        count_first = seed_db.query(Field).count()
        _run_seed(seed_db)
        count_second = seed_db.query(Field).count()
        assert count_first == count_second

    def test_idempotent_ndvi_count(self, seed_db):
        _run_seed(seed_db)
        count_first = seed_db.query(NDVIResult).count()
        _run_seed(seed_db)
        count_second = seed_db.query(NDVIResult).count()
        assert count_first == count_second
