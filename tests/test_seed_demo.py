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

    def test_creates_five_farms(self, seed_db):
        _run_seed(seed_db)
        assert seed_db.query(Farm).count() == 5

    def test_creates_fields_per_farm(self, seed_db):
        _run_seed(seed_db)
        farms = seed_db.query(Farm).all()
        for farm in farms:
            assert len(farm.fields) >= 2, f"Farm '{farm.name}' has fewer than 2 fields"

    def test_creates_ndvi_results(self, seed_db):
        _run_seed(seed_db)
        # Each field should have 24+ NDVI results (weekly over 6 months)
        fields = seed_db.query(Field).all()
        for field in fields:
            count = seed_db.query(NDVIResult).filter_by(field_id=field.id).count()
            assert count >= 24, f"Field '{field.name}' has only {count} NDVI results (need 24+)"

    def test_creates_soil_analyses(self, seed_db):
        _run_seed(seed_db)
        # Each field should have 6+ soil analyses (monthly over 6 months)
        fields = seed_db.query(Field).all()
        for field in fields:
            count = seed_db.query(SoilAnalysis).filter_by(field_id=field.id).count()
            assert count >= 6, f"Field '{field.name}' has only {count} soil analyses (need 6+)"

    def test_creates_thermal_results(self, seed_db):
        _run_seed(seed_db)
        # Each field should have 12+ thermal results (bi-weekly over 6 months)
        fields = seed_db.query(Field).all()
        for field in fields:
            count = seed_db.query(ThermalResult).filter_by(field_id=field.id).count()
            assert count >= 12, f"Field '{field.name}' has only {count} thermal results (need 12+)"

    def test_creates_health_scores(self, seed_db):
        _run_seed(seed_db)
        # Each field should have 24+ health scores (weekly, matching NDVI)
        fields = seed_db.query(Field).all()
        for field in fields:
            count = seed_db.query(HealthScore).filter_by(field_id=field.id).count()
            assert count >= 24, f"Field '{field.name}' has only {count} health scores (need 24+)"

    def test_creates_treatments(self, seed_db):
        _run_seed(seed_db)
        # Each field should have 4+ treatments at intervals
        fields = seed_db.query(Field).all()
        for field in fields:
            count = seed_db.query(TreatmentRecord).filter_by(field_id=field.id).count()
            assert count >= 4, f"Field '{field.name}' has only {count} treatments (need 4+)"

    def test_creates_weather_records(self, seed_db):
        _run_seed(seed_db)
        # Each farm should have 50+ weather records (every other day over 6 months)
        farms = seed_db.query(Farm).all()
        for farm in farms:
            count = seed_db.query(WeatherRecord).filter_by(farm_id=farm.id).count()
            assert count >= 50, f"Farm '{farm.name}' has only {count} weather records (need 50+)"

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

    def test_data_spans_six_months(self, seed_db):
        """NDVI data should span at least 6 months (180 days)."""
        _run_seed(seed_db)
        fields = seed_db.query(Field).all()
        for field in fields:
            ndvi_records = (
                seed_db.query(NDVIResult)
                .filter_by(field_id=field.id)
                .order_by(NDVIResult.analyzed_at)
                .all()
            )
            assert len(ndvi_records) >= 2
            span_days = (ndvi_records[-1].analyzed_at - ndvi_records[0].analyzed_at).days
            assert span_days >= 170, f"Field '{field.name}' data spans only {span_days} days (need 170+)"

    def test_seasonal_data_has_temporal_and_secas(self, seed_db):
        """NDVI data should have records in both Jalisco seasons:
        temporal (rainy, June-October) and secas (dry, November-May)."""
        _run_seed(seed_db)
        fields = seed_db.query(Field).all()
        for field in fields:
            ndvi_records = (
                seed_db.query(NDVIResult)
                .filter_by(field_id=field.id)
                .all()
            )
            temporal_months = {6, 7, 8, 9, 10}
            has_temporal = any(r.analyzed_at.month in temporal_months for r in ndvi_records)
            has_secas = any(r.analyzed_at.month not in temporal_months for r in ndvi_records)
            assert has_temporal, f"Field '{field.name}' has no temporal (rainy season) data"
            assert has_secas, f"Field '{field.name}' has no secas (dry season) data"

    def test_improvement_arc_before_and_after(self, seed_db):
        """Health scores should show clear before/after regenerative improvement:
        first quarter avg < last quarter avg."""
        _run_seed(seed_db)
        fields = seed_db.query(Field).all()
        for field in fields:
            scores = (
                seed_db.query(HealthScore)
                .filter_by(field_id=field.id)
                .order_by(HealthScore.scored_at)
                .all()
            )
            assert len(scores) >= 8, f"Field '{field.name}' needs 8+ health scores for arc test"
            quarter = len(scores) // 4
            first_avg = sum(s.score for s in scores[:quarter]) / quarter
            last_avg = sum(s.score for s in scores[-quarter:]) / quarter
            assert last_avg > first_avg + 15, (
                f"Field '{field.name}': first quarter avg {first_avg:.1f}, "
                f"last quarter avg {last_avg:.1f} — need >15 point improvement"
            )


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
