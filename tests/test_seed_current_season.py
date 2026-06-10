"""Regression: the demo seed must populate the CURRENT season so the
seasonal-benchmark view is never empty on a fresh `./run.sh`, regardless of
which Jalisco season the seed runs in (temporal Jun-Oct / secas Nov-May).
"""

from datetime import datetime

import scripts.seed_demo as sd
from cultivos.db.models import Farm, HealthScore
from cultivos.services.intelligence.seasonal_benchmark import (
    _season_of,
    compute_seasonal_benchmark,
)


def test_seed_populates_current_season_for_every_field(db):
    sd.seed_demo_data(db)

    farms = db.query(Farm).all()
    assert farms, "seed produced no farms"

    for farm in farms:
        result = compute_seasonal_benchmark(farm, db)
        empty = [f for f in result["fields"] if f["current_avg"] is None]
        assert not empty, (
            f"{farm.name}: current season empty for {len(empty)} field(s) — "
            f"seasonal view would render null"
        )


def test_seed_current_season_topup_is_idempotent(db):
    sd.seed_demo_data(db)
    n1 = db.query(HealthScore).count()
    sd.seed_demo_data(db)  # re-run: heals existing demo, must not duplicate
    n2 = db.query(HealthScore).count()
    assert n1 == n2, f"re-seed duplicated scores: {n1} -> {n2}"


def test_seed_current_season_scores_land_in_current_season(db):
    sd.seed_demo_data(db)
    cur = _season_of(datetime.utcnow())
    field_id = db.query(HealthScore.field_id).first()[0]
    scores = db.query(HealthScore).filter(HealthScore.field_id == field_id).all()
    assert any(_season_of(h.scored_at) == cur for h in scores), (
        "no score falls in the current season"
    )
