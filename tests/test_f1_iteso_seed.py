"""F1 — Tests for seed_iteso_demo: 3 ITESO demo farms x 3 fields, mixed health scores.

TDD tests written BEFORE implementation.
Acceptance criteria:
  - Exactly 3 named farms in Jalisco
  - Exactly 9 fields (3 per farm)
  - Health distribution: 3 green (latest >70), 4 yellow (40<=score<=70), 2 red (<40)
  - 5 HealthScore rows per field
  - 6 NDVIResult rows per field
  - 1 ThermalResult per field
  - 1 SoilAnalysis per field
  - Idempotent: running twice produces same row counts
"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from cultivos.db.models import (
    Base, Farm, Field, HealthScore, NDVIResult, ThermalResult, SoilAnalysis,
)

ITESO_FARM_NAMES = [
    "Rancho Don Manuel [DEMO]",
    "Aguacates La Joya [DEMO]",
    "Tierras Altas [DEMO]",
]


@pytest.fixture
def iteso_db():
    """Fresh in-memory DB for ITESO seeder tests."""
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


def _run_iteso_seed(session):
    """Import and run the ITESO demo seeder."""
    from scripts.seed_demo import seed_iteso_demo
    seed_iteso_demo(session)


def _get_iteso_farms(session):
    return (
        session.query(Farm)
        .filter(Farm.name.in_(ITESO_FARM_NAMES))
        .all()
    )


def _get_iteso_fields(session):
    farms = _get_iteso_farms(session)
    farm_ids = [f.id for f in farms]
    return session.query(Field).filter(Field.farm_id.in_(farm_ids)).all()


def _latest_score(session, field_id: int) -> float:
    """Return the latest HealthScore.score for a field."""
    hs = (
        session.query(HealthScore)
        .filter_by(field_id=field_id)
        .order_by(HealthScore.scored_at.desc())
        .first()
    )
    return hs.score if hs else None


class TestF1ItesoFarmsAndFields:
    """Farm and field counts."""

    def test_creates_3_farms(self, iteso_db):
        _run_iteso_seed(iteso_db)
        farms = _get_iteso_farms(iteso_db)
        assert len(farms) == 3, f"Expected 3 ITESO farms, got {len(farms)}"

    def test_creates_9_fields(self, iteso_db):
        _run_iteso_seed(iteso_db)
        fields = _get_iteso_fields(iteso_db)
        assert len(fields) == 9, f"Expected 9 fields total, got {len(fields)}"

    def test_3_fields_per_farm(self, iteso_db):
        _run_iteso_seed(iteso_db)
        farms = _get_iteso_farms(iteso_db)
        for farm in farms:
            count = iteso_db.query(Field).filter_by(farm_id=farm.id).count()
            assert count == 3, f"Farm '{farm.name}' has {count} fields (expected 3)"

    def test_farms_in_jalisco(self, iteso_db):
        _run_iteso_seed(iteso_db)
        farms = _get_iteso_farms(iteso_db)
        for farm in farms:
            assert farm.state == "Jalisco", f"Farm '{farm.name}' state={farm.state}"


class TestF1HealthScores:
    """Health scores per field and overall distribution."""

    def test_5_health_scores_per_field(self, iteso_db):
        _run_iteso_seed(iteso_db)
        fields = _get_iteso_fields(iteso_db)
        for field in fields:
            count = iteso_db.query(HealthScore).filter_by(field_id=field.id).count()
            assert count == 5, f"Field '{field.name}' has {count} health scores (expected 5)"

    def test_health_distribution_3_green_4_yellow_2_red(self, iteso_db):
        """Latest health score per field: 3 green (>70), 4 yellow (40-70), 2 red (<40)."""
        _run_iteso_seed(iteso_db)
        fields = _get_iteso_fields(iteso_db)
        assert len(fields) == 9, "Need 9 fields for distribution test"

        green = yellow = red = 0
        for field in fields:
            score = _latest_score(iteso_db, field.id)
            assert score is not None, f"Field '{field.name}' has no health scores"
            if score > 70:
                green += 1
            elif score >= 40:
                yellow += 1
            else:
                red += 1

        assert green == 3, f"Expected 3 green fields (score>70), got {green}"
        assert yellow == 4, f"Expected 4 yellow fields (40<=score<=70), got {yellow}"
        assert red == 2, f"Expected 2 red fields (score<40), got {red}"

    def test_health_scores_are_ordered_in_time(self, iteso_db):
        """Each field's 5 scores should have distinct timestamps, weekly apart."""
        _run_iteso_seed(iteso_db)
        fields = _get_iteso_fields(iteso_db)
        for field in fields:
            scores = (
                iteso_db.query(HealthScore)
                .filter_by(field_id=field.id)
                .order_by(HealthScore.scored_at)
                .all()
            )
            assert len(scores) == 5
            for i in range(1, 5):
                diff_days = (scores[i].scored_at - scores[i - 1].scored_at).days
                assert diff_days >= 6, (
                    f"Field '{field.name}' scores {i-1}-{i} only {diff_days} days apart"
                )


class TestF1SensorData:
    """NDVIResult, ThermalResult, SoilAnalysis per field."""

    def test_6_ndvi_per_field(self, iteso_db):
        _run_iteso_seed(iteso_db)
        fields = _get_iteso_fields(iteso_db)
        for field in fields:
            count = iteso_db.query(NDVIResult).filter_by(field_id=field.id).count()
            assert count == 6, f"Field '{field.name}' has {count} NDVI rows (expected 6)"

    def test_1_thermal_per_field(self, iteso_db):
        _run_iteso_seed(iteso_db)
        fields = _get_iteso_fields(iteso_db)
        for field in fields:
            count = iteso_db.query(ThermalResult).filter_by(field_id=field.id).count()
            assert count == 1, f"Field '{field.name}' has {count} thermal rows (expected 1)"

    def test_1_soil_per_field(self, iteso_db):
        _run_iteso_seed(iteso_db)
        fields = _get_iteso_fields(iteso_db)
        for field in fields:
            count = iteso_db.query(SoilAnalysis).filter_by(field_id=field.id).count()
            assert count == 1, f"Field '{field.name}' has {count} soil rows (expected 1)"

    def test_ndvi_spans_6_weeks(self, iteso_db):
        """NDVI records span at least 35 days (5 week intervals across 6 records)."""
        _run_iteso_seed(iteso_db)
        fields = _get_iteso_fields(iteso_db)
        for field in fields:
            records = (
                iteso_db.query(NDVIResult)
                .filter_by(field_id=field.id)
                .order_by(NDVIResult.analyzed_at)
                .all()
            )
            assert len(records) == 6
            span = (records[-1].analyzed_at - records[0].analyzed_at).days
            assert span >= 35, f"Field '{field.name}' NDVI spans {span} days (need >=35)"


class TestF1Idempotent:
    """Running seed_iteso_demo twice produces identical row counts (no duplicates)."""

    def test_idempotent_farm_count(self, iteso_db):
        _run_iteso_seed(iteso_db)
        count1 = len(_get_iteso_farms(iteso_db))
        _run_iteso_seed(iteso_db)
        count2 = len(_get_iteso_farms(iteso_db))
        assert count1 == count2 == 3

    def test_idempotent_field_count(self, iteso_db):
        _run_iteso_seed(iteso_db)
        count1 = len(_get_iteso_fields(iteso_db))
        _run_iteso_seed(iteso_db)
        count2 = len(_get_iteso_fields(iteso_db))
        assert count1 == count2 == 9

    def test_idempotent_health_score_count(self, iteso_db):
        _run_iteso_seed(iteso_db)
        farms = _get_iteso_farms(iteso_db)
        farm_ids = [f.id for f in farms]
        fields = iteso_db.query(Field).filter(Field.farm_id.in_(farm_ids)).all()
        field_ids = [f.id for f in fields]
        count1 = iteso_db.query(HealthScore).filter(HealthScore.field_id.in_(field_ids)).count()

        _run_iteso_seed(iteso_db)
        farms = _get_iteso_farms(iteso_db)
        farm_ids = [f.id for f in farms]
        fields = iteso_db.query(Field).filter(Field.farm_id.in_(farm_ids)).all()
        field_ids = [f.id for f in fields]
        count2 = iteso_db.query(HealthScore).filter(HealthScore.field_id.in_(field_ids)).count()

        assert count1 == count2 == 45  # 9 fields × 5 scores

    def test_idempotent_does_not_touch_other_farms(self, iteso_db):
        """Re-seeding should not delete or modify non-ITESO farms."""
        from cultivos.db.models import Farm as FarmModel
        # Create a non-DEMO farm
        other_farm = FarmModel(name="Mi Rancho Real", state="Jalisco")
        iteso_db.add(other_farm)
        iteso_db.commit()

        _run_iteso_seed(iteso_db)
        _run_iteso_seed(iteso_db)

        # Non-demo farm must survive both runs
        surviving = iteso_db.query(FarmModel).filter_by(name="Mi Rancho Real").first()
        assert surviving is not None, "Non-DEMO farm was deleted by seed_iteso_demo"
