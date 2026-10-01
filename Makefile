.PHONY: dev up down build logs ps

dev:
	uv run python -m uvicorn app.main:app --reload --port 8000

up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose build

logs:
	docker-compose logs -f

ps:
	docker-compose ps

migrate:
	uv run python -m alembic upgrade head

migrate-create:
	uv run python -m alembic revision --autogenerate -m "$(MSG)"

migrate-rollback:
	uv run python -m alembic downgrade -1

shell:
	docker-compose exec backend sh

db-shell:
	docker-compose exec db psql -U postgres -d burdaerata
