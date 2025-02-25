build:
	docker compose -f docker-compose.yaml up --build -d --remove-orphans

up:
	docker compose -f docker-compose.yaml up

down:
	docker compose -f docker-compose.yaml down

down_volumes:
	docker compose -f docker-compose.yaml down -v

shortener-format:
	docker compose -f docker-compose.yaml exec shortener isort . && \
	docker compose -f docker-compose.yaml exec shortener black . && \
	docker compose -f docker-compose.yaml exec shortener flake8 . && \
	docker compose -f docker-compose.yaml exec shortener mypy .

analytics-format:
	docker compose -f docker-compose.yaml exec analytics isort . && \
	docker compose -f docker-compose.yaml exec analytics black . && \
	docker compose -f docker-compose.yaml exec analytics flake8 . && \
	docker compose -f docker-compose.yaml exec analytics mypy .
