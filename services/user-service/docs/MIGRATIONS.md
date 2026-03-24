# Database migrations (Alembic)

This service uses [Alembic](https://alembic.sqlalchemy.org/) with SQLAlchemy models under `app/models/`. The FastAPI app connects with **async** SQLAlchemy (`postgresql+asyncpg`). Alembic runs migrations with a **sync** driver (`psycopg2`), configured in `alembic/env.py` by rewriting `+asyncpg` to `+psycopg2` on the same `DATABASE_URL`.

## Prerequisites

- PostgreSQL reachable with credentials matching `DATABASE_URL` in `.env` (see `.env.example`).
- From the **service root** (`services/user-service/`), so `app` imports and `.env` resolve correctly.

## Common commands

Run these with `uv` from `services/user-service/`:

| Task | Command |
|------|---------|
| Apply all pending migrations | `uv run alembic upgrade head` |
| Roll back one revision | `uv run alembic downgrade -1` |
| Show current DB revision | `uv run alembic current` |
| Show migration history | `uv run alembic history` |

### New migration after model changes

1. Edit or add models under `app/models/` and export new models in `app/models/__init__.py` so Alembic loads them (see `alembic/env.py`).
2. Generate a revision (compares models to the live DB):

   ```bash
   uv run alembic revision --autogenerate -m "describe_change"
   ```

3. **Review** the file under `alembic/versions/` — autogenerate can miss or mis-detect changes (constraints, renames, data backfills).
4. Apply:

   ```bash
   uv run alembic upgrade head
   ```

### Empty migration (manual SQL / data)

```bash
uv run alembic revision -m "manual_step"
```

Edit the new revision’s `upgrade()` / `downgrade()` by hand.

## Layout

| Path | Role |
|------|------|
| `alembic.ini` | Alembic entry config (`script_location`, logging). |
| `alembic/env.py` | Builds sync URL, sets `target_metadata` from `Base`, runs migrations. |
| `alembic/versions/` | Revision scripts (one file per migration chain node). |
| `app/db/base.py` | `Base` declarative class; models inherit from it. |
| `app/models/__init__.py` | Import models here so metadata is complete for autogenerate. |

## CI / Docker

- Ensure `DATABASE_URL` is set (or load `.env`) in the environment that runs `alembic upgrade head` (e.g. deploy job or container entrypoint **before** starting the API).
- For a fresh database, `upgrade head` creates all tables from the revision chain.

## Troubleshooting

- **`ModuleNotFoundError: No module named 'app'`** — Run Alembic from `services/user-service/` (see `prepend_sys_path` in `alembic.ini`).
- **Wrong database** — `DATABASE_URL` comes from `DatabaseSettings` (`DATABASE_*` in `.env`); verify host, db name, and user.
- **Async URL** — Keep using `postgresql+asyncpg://` in `.env` for the app; do not switch the app URL to psycopg2. Alembic handles the rewrite internally.
