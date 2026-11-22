SHELL := /bin/bash
COMPOSE := docker compose -f infra/docker-compose.yml
PY := backend/.venv/bin/python
PIP := backend/.venv/bin/pip

.PHONY: help up down be fe install-be install-fe db-reset wait-db psql logs health build test migrate seed revision reset-all

help:
	@echo "make up          - start postgres (docker)"
	@echo "make be          - run backend (uvicorn :8000)"
	@echo "make fe          - run frontend (vite :5173)"
	@echo "make db-reset    - hapus volume db & buat ulang (tunggu healthy)"
	@echo "make psql        - shell psql ke database"
	@echo "make health      - cek endpoint health"
	@echo "make build       - build frontend (typecheck + bundle)"
	@echo "make test        - jalankan pytest"
	@echo "make migrate     - alembic upgrade head"
	@echo "make seed        - isi data contoh (idempotent)"
	@echo "make revision m=... - buat file migrasi baru"
	@echo "make reset-all   - db-reset + migrate + seed"

up:
	$(COMPOSE) up -d db

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f db

be:
	cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

fe:
	cd frontend && npm run dev

install-be:
	python3 -m venv backend/.venv && $(PIP) install -U pip && $(PIP) install -r backend/requirements.txt

install-fe:
	cd frontend && npm install

db-reset:
	$(COMPOSE) down -v
	$(COMPOSE) up -d db
	$(MAKE) wait-db

# Tunggu sampai healthcheck Postgres benar-benar "healthy".
# Jangan pakai "sleep 5" — di mesin lambat itu tidak cukup, di mesin cepat buang waktu.
wait-db:
	@printf "menunggu postgres"
	@for i in $$(seq 1 60); do \
		status=$$(docker inspect --format '{{.State.Health.Status}}' cs-ticketing-db 2>/dev/null); \
		if [ "$$status" = "healthy" ]; then echo " siap."; exit 0; fi; \
		printf "."; sleep 2; \
	done; \
	echo " GAGAL (cek: make logs)"; exit 1

psql:
	$(COMPOSE) exec db psql -U ticketing -d ticketing

health:
	@curl -s localhost:8000/api/v1/health | python3 -m json.tool

build:
	cd frontend && npm run build

test:
	cd backend && .venv/bin/pytest -q

migrate:
	cd backend && .venv/bin/alembic upgrade head

seed:
	cd backend && .venv/bin/python -m scripts.seed

revision:
	cd backend && .venv/bin/alembic revision --autogenerate -m "$(m)"

reset-all: db-reset
	cd backend && .venv/bin/alembic upgrade head && .venv/bin/python -m scripts.seed
