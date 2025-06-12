build:
	docker compose -f docker-compose.yaml up --build -d --remove-orphans

up:
	docker compose -f docker-compose.yaml up

down:
	docker compose -f docker-compose.yaml down

down_volumes:
	docker compose -f docker-compose.yaml down -v

into_shortener:
	docker compose -f docker-compose.yaml exec shortener bash

into_analytics:
	docker compose -f docker-compose.yaml exec analytics bash

logs-frontend:
	docker compose -f docker-compose.yaml logs -f frontend

logs-shortener:
	docker compose -f docker-compose.yaml logs -f shortener

logs-analytics:
	docker compose -f docker-compose.yaml logs -f analytics

logs-all:
	docker compose -f docker-compose.yaml logs -f

shortener-lint:
	docker compose -f docker-compose.yaml exec shortener ruff check .

analytics-lint:
	docker compose -f docker-compose.yaml exec analytics ruff check .

lint: shortener-lint analytics-lint

shortener-format:
	docker compose -f docker-compose.yaml exec shortener ruff check --fix . && \
	docker compose -f docker-compose.yaml exec shortener black .

analytics-format:
	docker compose -f docker-compose.yaml exec analytics ruff check --fix . && \
	docker compose -f docker-compose.yaml exec analytics black .

format: shortener-format analytics-format

shortener-typecheck:
	docker compose -f docker-compose.yaml exec shortener mypy .

analytics-typecheck:
	docker compose -f docker-compose.yaml exec analytics mypy .

typecheck: shortener-typecheck analytics-typecheck

shortener-check: shortener-lint shortener-typecheck

analytics-check: analytics-lint analytics-typecheck

check: lint typecheck

db-init:
	docker compose -f docker-compose.yaml exec postgres bash /docker-entrypoint-initdb.d/init-db.sh

migrate:
	docker compose -f docker-compose.yaml exec shortener alembic upgrade head && \
	docker compose -f docker-compose.yaml exec analytics alembic upgrade head

db-init-and-migrate: db-init migrate

shortener-test:
	docker compose -f docker-compose.yaml exec shortener python -m pytest tests/ -v

analytics-test:
	docker compose -f docker-compose.yaml exec analytics python -m pytest tests/ -v

test: shortener-test analytics-test

shortener-test-cov:
	docker compose -f docker-compose.yaml exec shortener python -m pytest tests/ -v --cov=app --cov-report=term-missing

analytics-test-cov:
	docker compose -f docker-compose.yaml exec analytics python -m pytest tests/ -v --cov=app --cov-report=term-missing

test-cov: shortener-test-cov analytics-test-cov
