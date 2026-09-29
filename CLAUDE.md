# CLAUDE.md

## Project

AirbnbLite is a backend-only REST API for hotel booking. There is no frontend.
Guests search active hotels by city and dates, start a booking, attach saved
guests, pay through a mock gateway and cancel. Hotel admins create hotels and
rooms, manage per-date inventory and pricing, and pull booking lists and
reports for their hotels. Clients use it over HTTP; the only UI is FastAPI's
Swagger page at `/api/v1/docs` (plus a custom ReDoc at `/api/v1/redoc`).
Deployed to Render via `render.yaml`.

## Stack

- Python 3.11, FastAPI 0.109, Uvicorn
- PostgreSQL via asyncpg, SQLAlchemy 2.0 async ORM, Alembic migrations
- Pydantic v2 + pydantic-settings, JWT via python-jose, bcrypt via passlib
- Package manager: pip with a pinned `requirements.txt`. No poetry/uv.

## Layout

```
app/
  main.py              FastAPI app, CORS, /health, custom ReDoc route
  api/v1/router.py     mounts every endpoint module under a prefix + tag
  api/v1/endpoints/    thin route handlers, one module per area
  core/                config (Settings), security (JWT/bcrypt), dependencies (auth guards)
  db/                  declarative Base, async engine + get_db session
  models/              SQLAlchemy models and str enums
  schemas/             Pydantic request/response models
  services/            business logic, one *Service class per area
alembic/versions/      one initial migration so far
tests/                 empty
render.yaml, Dockerfile
```

## Commands

```bash
setup:     python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
dev:       uvicorn app.main:app --reload --port 8000
migrate:   alembic upgrade head
new mig:   alembic revision --autogenerate -m "describe change"
test:      pytest            # pytest + pytest-asyncio are installed, but tests/ is empty
docker:    docker build -t airbnblite . && docker run -p 8000:8000 --env-file .env airbnblite
```

No linter, formatter or type checker is configured. Don't claim one ran.

## Conventions

- Handlers stay thin: build `XService(db)` and return its result. Business rules,
  ownership checks and `HTTPException`s live in `app/services/`.
- Services `flush()` and `refresh()`; they never `commit()`. `get_db` in
  `app/db/session.py` commits on success and rolls back on any exception.
- Auth guards come from `app/core/dependencies.py`: `get_current_active_user`,
  `get_current_hotel_admin` (HOTEL_ADMIN or ADMIN), `get_current_admin`.
- Public and admin routes for one area live in the same module as
  `public_router` / `admin_router` (or `router` / `admin_router`), and
  `router.py` mounts them under different prefixes.
- Enums are `class X(str, enum.Enum)` with UPPERCASE values matching the name.
- Response schemas use `class Config: from_attributes = True`.
- Paths are mostly lowercase, but some existing ones are camelCase
  (`/myBookings`, `/{id}/addGuests`). Don't rename them; clients depend on them.
- All settings come from `app/core/config.py` (`settings`), loaded from `.env`.

## Testing

- Nothing exists yet. When adding tests, use pytest + pytest-asyncio with
  `httpx.AsyncClient` against `app.main:app`, and exercise behavior through
  HTTP endpoints.
- New code paths need a test. Bug fixes need a regression test that fails
  before the fix.

## Things that will bite you

- New hotels are created with `is_active=False`. They don't appear in search
  and can't be booked until `PATCH /admin/hotels/{id}/activate`.
- Creating a room seeds inventory for the next 90 days from today
  (`RoomService._initialize_inventory`). Bookings past that window fail with
  "No inventory available for date ...". Extend with the inventory PATCH endpoints.
- Availability is `available_count - booked_count` per date. Booking reserves by
  incrementing `booked_count`; cancel releases it. Keep both paths in sync.
- A completed payment on a cancelled booking is marked `REFUNDED`. A failed
  webhook sets the booking to `EXPIRED`.
- Payments are mocked. `POST /webhook/payment/capture` is unauthenticated on
  purpose so the webhook can be simulated by hand.
- README room types (Standard/Deluxe/Suite/Presidential) are wrong. The real
  `RoomType` enum is SINGLE, DOUBLE, DELUXE, SUITE, PENTHOUSE.
- `get_optional_current_user` returns an inner coroutine function, not a
  user. Don't use it as a dependency without fixing it first.
- Render hands out `postgres://` URLs; `settings.async_database_url` rewrites
  them to `postgresql+asyncpg://`. Use that, not `DATABASE_URL` directly.
- New models must be imported in `alembic/env.py` or autogenerate won't see them.

## How I want you to work

- Ask before installing a new dependency. Check if we already have
  something that does the job.
- Make the smallest change that solves the problem. Don't refactor
  adjacent code you weren't asked about.
- If you're guessing about a library API, read its source in the venv's
  site-packages or find an existing usage here. Don't invent method names.
- If a task needs more than about three files changed, outline the plan
  first and wait.
- Don't add comments that restate the code. Comment the why, not the what.
- Don't add defensive try/catch around things that can't fail.
- Type hints on every function signature. Prefer stdlib; justify new deps.

## Don't

- Don't commit, push, or open PRs unless I ask.
- Don't modify `.env`, `render.yaml`, CI config, or anything in `.github/`
  without asking.
- Don't edit a migration that's already been applied; add a new one.
- Don't change test assertions to make a failing test pass.
