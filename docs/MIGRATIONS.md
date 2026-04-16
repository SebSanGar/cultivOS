# Database Migrations (alembic)

Baseline: `alembic/versions/0a265488d88f_baseline_schema_from_sqlalchemy_models.py` (2026-04-16).

## Apply migrations
```
alembic upgrade head
```

## Add a new migration
```
# after editing SQLAlchemy models
alembic revision --autogenerate -m "short description"
# review the generated file in alembic/versions/
alembic upgrade head
```

## Stamp an existing prod DB (one-time)
If the Railway DB already has the baseline schema from `Base.metadata.create_all`:
```
alembic stamp head
```
Then app.py can drop its startup `create_all` call and rely on migrations.
