SHELL := /bin/bash
COMPOSE := docker compose -f infra/docker-compose.yml
PY := backend/.venv/bin/python
PIP := backend/.venv/bin/pip

.PHONY: help up down be fe install-db install-be install-fe db-reset psql logs health build test

help:
	@echo "make up          - start postgres (docker)"
	@echo "make be          - run backend (uvicorn :8000)"
	@echo "make fe          - run frontend (vite :5173)"
	@echo "make db-reset    - hapus volume db & buat ulang"
	@echo "make psql        - shell psql ke database"
	@echo "make health      - cek endpoint health"
	@echo "make build       - build frontend (typecheck + bundle)"
	@echo "make test        - jalankan pytest"

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

psql:
	$(COMPOSE) exec db psql -U ticketing -d ticketing

health:
	@curl -s localhost:8000/api/v1/health | python3 -m json.tool

build:
	cd frontend && npm run build

test:
	cd backend && .venv/bin/pytest -q
