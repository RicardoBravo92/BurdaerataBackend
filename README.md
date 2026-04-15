# Burdaerata Backend

FastAPI backend for Burdaerata - a Cards Against Humanity style party game.

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

## API Endpoints

### Games

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/games` | Create a new game |
| GET | `/api/v1/games/{id}` | Get game by ID |
| GET | `/api/v1/games/by-code/{code}` | Get game by code |
| POST | `/api/v1/games/join` | Join a game |
| GET | `/api/v1/games/{id}/players` | Get game players |
| POST | `/api/v1/games/{id}/start` | Start the game |
| POST | `/api/v1/games/{id}/leave` | Leave a game |

### Rounds

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/games/{id}/rounds/last` | Get last round |
| POST | `/api/v1/games/{id}/rounds/next` | Start next round |
| GET | `/api/v1/rounds/{id}/answers` | Get round answers |
| POST | `/api/v1/rounds/{id}/answers` | Submit answer |
| POST | `/api/v1/rounds/{id}/winner` | Select winner |

### Cards

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/cards/questions` | List all questions |
| GET | `/api/v1/cards/questions/{id}` | Get question with text |
| GET | `/api/v1/cards/answers` | List all answers |
| GET | `/api/v1/cards/answers/{id}` | Get answer with text |

### WebSocket

Connect: `WS /api/v1/ws/{game_id}?token={clerk_token}`

**Events:**
- `player_joined` - Player joined the game
- `player_left` - Player left the game
- `game_started` - Game has started
- `new_round` - New round started
- `answer_submitted` - Player submitted an answer
- `round_finished` - Round winner selected
- `game_finished` - Game has ended

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

### Render

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set environment variables
4. Deploy

Or use `render.yaml` for automatic setup.

## License

MIT
