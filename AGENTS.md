# Mac Loving Backend

## Stack
- **FastAPI** + **SQLAlchemy 2.0 async** + **PostgreSQL 16**
- Auth: JWT (python-jose) + bcrypt (passlib)
- Redis: caching, rate limiting, Celery broker
- S3 (boto3) for file storage
- Stripe for subscription billing
- Structlog for structured logging
- Celery for async tasks (configured but no tasks yet)
- Alembic directory exists but is empty (no migrations)

## Architecture
```
app/
  api/v1/routers/   — FastAPI route handlers
  application/
    schemas/        — Pydantic request/response models
    services/       — Business logic (auth, subscription, album, memory)
  domain/
    models/         — SQLAlchemy ORM models
    enums/          — Python enums
  infra/
    db/             — Async engine, session factory, Base
    repositories/   — Data access layer (generic BaseRepository)
    cache/          — Redis cache helpers
    storage/        — S3 upload/presigned URL helpers
  core/
    config.py       — Pydantic Settings (reads .env)
    security.py     — Password hashing, JWT create/verify, input sanitization
    dependencies/   — FastAPI Depends (auth, premium, rate-limit, ownership)
    exceptions.py   — Custom HTTPException subclasses
  middleware/
    logging.py      — Request-id + structlog middleware
```

## Key patterns
- **All DB access is async**: use `AsyncSession`, `await session.execute()`, `await session.flush()`
- **Session committed in `get_db_session` generator**: do NOT commit manually; flush is fine
- **Repositories extend `BaseRepository[ModelT]`**: generic CRUD with `session` injected via constructor
- **Services take `db: AsyncSession` and/or `redis` in constructor**; no DI framework
- **Auth dependency chain**: `get_current_user` → `require_couple` → `require_premium` → `PremiumUser`

## Known issues (fix before using)
- `app/core/rate_limit.py` references `settings.RATE_LIMIT_DEFAULT` — config only has `RATE_LIMIT_PER_MINUTE` and `RATE_LIMIT_AUTH_PER_MINUTE` (will crash)
- `app/api/v1/routers/auth.py` imports from `app.infra.db.deps` — that module does not exist; the actual deps are in `app/core/dependencies/auth.py`
- `app/domain/models/plan.py` uses `from domain.enums...` instead of `from app.domain.enums...` (will fail)
- `app/domain/models/couple_models/audit_log.py` uses `from infra.db.base...` instead of `from app.infra.db.base...`
- `app/main.py` only has a root `GET /` returning "Helloworld" — middleware, routers, and CORS are NOT wired up yet
- Duplicate property `allowed_origins_list` and `origins_list` in `Settings`
- `User` model has both `albums` (as member) and `albums_created` relationship to `Album`

## Commands
```bash
# Start PostgreSQL + Redis
docker compose up -d

# Activate venv
.venv\Scripts\Activate.ps1

# Run dev server
uvicorn app.main:app --reload

# No tests exist yet (pytest/pytest-asyncio in deps)
```

## Environment (.env)
Copy from `.env.example` or create with at minimum:
```
DATABASE_URL=postgresql+asyncpg://arsene:pass@localhost:5432/album_db
SECRET_KEY=<random>
JWT_SECRET_KEY=<random>
```
Note: DATABASE_URL uses `asyncpg` driver (SQLAlchemy async), but psycopg2-binary is also installed. The connection URL in `.env.example` uses `postgresql://` — it should be `postgresql+asyncpg://` for async.

## Config loading
- `app/core/config.py`: `Settings` reads from `.env` via `pydantic-settings`
- Singleton via `@lru_cache` on `get_settings()`; import `settings` directly

## Deployment deps
Redis is required for rate limiting, caching, and Celery. No migration scripts exist yet (Alembic empty).
