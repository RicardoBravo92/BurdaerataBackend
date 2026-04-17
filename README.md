# Burdaerata Backend

FastAPI backend for Burdaerata - a Cards Against Humanity style party game.

👉 **Frontend Repository:** [https://github.com/RicardoBravo92/Burdaerata](https://github.com/RicardoBravo92/Burdaerata)

## Tech Stack

- **FastAPI** - Modern async Python web framework
- **SQLAlchemy/SQLModel** - ORM with async support
- **PostgreSQL** - Production database
- **SQLite** - Development database
- **Clerk** - Authentication
- **WebSockets** - Real-time game updates
- **Docker** - Containerization
- **Alembic** - Database migrations

## Features

- Game lobby system with unique join codes
- Real-time WebSocket notifications
- Card dealing and management
- Round-based gameplay
- Score tracking
- JWT authentication via Clerk

## Project Structure

```
Backend/
├── app/
│   ├── api/v1/endpoints/   # API routes
│   ├── core/               # Config, database, WebSocket manager
│   ├── models/             # SQLModel models
│   ├── repositories/       # Data access layer
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic
│   └── main.py             # FastAPI app
├── alembic/               # Database migrations
├── cards_data.json         # Game cards data
└── docker-compose.yml      # Docker setup
```

## Setup

### Prerequisites

- Python 3.12+
- PostgreSQL (or Docker)
- Clerk account for authentication

### Local Development

1. Clone and install dependencies:
```bash
cd Backend
cp .env.example .env
# Edit .env with your CLERK_SECRET_KEY
uv sync
```

2. Run the server:
```bash
uv run uvicorn app.main:app --reload --port 8000
```

3. Access the API:
- API: http://localhost:8000/api/v1
- Docs: http://localhost:8000/docs

### Docker

```bash
docker-compose up --build
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Production |
| `CLERK_SECRET_KEY` | Clerk API secret key | Yes |
| `AUTHORIZED_PARTIES` | Allowed frontend origins | Yes |

## Database Migrations

```bash
# Create new migration
uv run alembic revision --autogenerate -m "add description"

# Apply migrations
uv run alembic upgrade head

# Rollback
uv run alembic downgrade -1
```

## Deployment

### Docker

```bash
docker-compose -f docker-compose.yml up -d
```

## License

MIT
