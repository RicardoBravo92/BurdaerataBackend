# Burdaerata Backend

FastAPI backend for **Burdaerata** — a Cards Against Humanity style party game played in real time with friends. Venezuelan flavor, played over WebSockets.

- 👉 **Web App:** [github.com/RicardoBravo92/Burdaerata](https://github.com/RicardoBravo92/Burdaerata)
- 👉 **Mobile App:** [github.com/RicardoBravo92/Burdaerataexpo](https://github.com/RicardoBravo92/Burdaerataexpo)

## Tech Stack

- **FastAPI** — async Python web framework
- **SQLAlchemy / SQLModel** — async ORM
- **PostgreSQL (Neon, prod) / SQLite (dev)** — database
- **Clerk** — JWT authentication
- **WebSockets** — real-time game state
- **Alembic** — database migrations
- **Resend** — transactional email

## Features

- Game lobby with unique 6-digit join codes
- Real-time WebSocket updates (players, rounds, answers, chat)
- Round-based gameplay: question card → submit answers → judge picks a winner
- Automatic card dealing and refill after each submission
- Score tracking with configurable score-to-win
- Clerk JWT auth on REST and WebSocket (only players may open a socket)
- Winner selection, round transitions, and game history
- Chat (persisted) broadcast over WebSocket
- Password recovery + registration emails via Resend

## Project Structure

```
Backend/
├── app/
│   ├── api/v1/endpoints/   # REST + WebSocket routes
│   ├── core/               # config, async database, WebSocket manager
│   ├── models/             # SQLModel models
│   ├── repositories/       # Data access layer
│   ├── schemas/            # Pydantic v2 schemas (with from_attributes=True)
│   ├── services/           # Business logic (game, cards, email)
│   │   └── exceptions.py   # Custom exceptions with HTTP status codes
│   ├── main.py             # FastAPI app factory (create_app)
│   └── api/dependencies.py # Typed dependencies (DbDep, CurrentUserDep, etc.)
├── alembic/                # Database migrations (async env)
├── tests/                  # pytest suite (AsyncClient + pytest-asyncio)
├── cards_data.json         # Question + answer cards
└── render.yaml             # Render.com deployment
```

## Architecture Patterns Applied

This codebase follows **FastAPI best practices** per the [fastapi-patterns](https://github.com/vercel-labs/agent-skills) skill:

| Pattern | Implementation |
|---------|----------------|
| **App Factory** | `create_app()` in `app/main.py` with `lifespan` |
| **Config** | `pydantic-settings` v2 with `extra="forbid"`, computed properties |
| **Dependencies** | Typed aliases: `DbDep`, `CurrentUserDep`, `ActiveUserDep`, `ClerkUserIdDep` |
| **Schemas** | Pydantic v2, `model_config = ConfigDict(from_attributes=True)`, `Field` constraints |
| **Response Models** | All endpoints declare `response_model` (no ORM leakage) |
| **Service Layer** | Explicit transaction boundaries, custom exceptions |
| **Error Handling** | Typed exceptions → HTTP status mapping in router |
| **Repositories** | Pure data access, no session management |
| **Testing** | `AsyncClient` + `ASGITransport` + `pytest_asyncio` |

## Setup

### Prerequisites

- Python 3.12+
- PostgreSQL for production (SQLite is fine for local dev)
- A [Clerk](https://clerk.com) account for authentication
- (Optional) A [Resend](https://resend.com) API key for email features

### Local Development

```bash
cd Backend
cp .env.example .env
# Edit .env with your CLERK_SECRET_KEY and DATABASE_URL
uv sync
# Run with uv's Python (avoids "uv trampoline failed" on paths with spaces):
uv run python -m uvicorn app.main:app --reload --port 8000
# Or use FastAPI's dev CLI (auto-reload + pretty output):
uv run python -m fastapi dev app/main.py --port 8000
# OR use the venv directly:
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Database migrations run automatically on startup (`init_db` applies `alembic upgrade head`), so no manual step is needed to boot.

### API endpoints

- REST API: `http://localhost:8000/api/v1`
- OpenAPI docs: `http://localhost:8000/docs`

### Running tests

```bash
uv run python -m pytest
# or, if uv run fails on this machine:
.venv\Scripts\python.exe -m pytest
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | SQLAlchemy async URL (`sqlite+aiosqlite:///...` for dev, `postgresql+asyncpg://...` for prod) | Yes |
| `CLERK_SECRET_KEY` | Clerk secret key used to verify JWTs | Yes |
| `AUTHORIZED_PARTIES` | Comma-separated allowed frontend origins | No (default: `http://localhost:3000`) |
| `RESEND_API_KEY` | Resend key for transactional email | For email endpoints |

## Database Migrations

```bash
# Generate a new migration after model changes
uv run alembic revision --autogenerate -m "add description"

# Apply migrations manually (also done automatically at startup)
uv run alembic upgrade head

# Rollback one step
uv run alembic downgrade -1
```

Migrations are generated in `alembic/versions/`. The initial migration includes a baseline guard so databases previously created via `create_all` are stamped without error.

## Real-Time / WebSockets

- Endpoint: `/api/v1/ws/{game_id}?token=<clerk_jwt>`
- Auth: the Clerk JWT is verified before the socket is accepted; only members of the game may connect.
- Events: `game_started`, `new_round`, `answer_submitted`, `round_finished`, `game_finished`, `player_joined`, `player_left`, `game_deleted`, `new_chat_message`.

## Deployment (Render.com)

`render.yaml` describes the free-tier web service and database:

- **Build:** `uv sync --frozen && uv run alembic upgrade head`
- **Start:** `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health check:** `/health`

Set `CLERK_SECRET_KEY`, `RESEND_API_KEY`, and `AUTHORIZED_PARTIES` in the Render dashboard.

## License

MIT