.PHONY: help install run docker-up docker-down clean frontend-install frontend-dev frontend-build

VENV = venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
UVICORN = $(VENV)/bin/uvicorn

# Detect Windows vs Linux/Mac for paths and clean commands
ifeq ($(OS),Windows_NT)
	PYTHON = $(VENV)/Scripts/python.exe
	PIP = $(VENV)/Scripts/pip.exe
	UVICORN = $(VENV)/Scripts/uvicorn.exe
endif

help:
	@echo "Available commands:"
	@echo "  make install          - Create a virtual environment and install backend dependencies"
	@echo "  make run              - Run the backend locally (without Docker)"
	@echo "  make frontend-install - Install frontend (Vite + React) dependencies"
	@echo "  make frontend-dev     - Run the frontend dev server (port 5173)"
	@echo "  make frontend-build   - Build the frontend for production"
	@echo "  make dev              - Run both backend and frontend in parallel"
	@echo "  make docker-up        - Start the application using Docker Compose"
	@echo "  make docker-down      - Stop the Docker containers"
	@echo "  make clean            - Remove virtual env, node_modules, and cached files"

install:
	python -m venv $(VENV)
	$(PIP) install -r requirements.txt

run:
	$(UVICORN) app.main:app --reload

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

dev:
	@echo "Starting backend (port 8000) and frontend (port 5173)..."
	@$(MAKE) run &
	@$(MAKE) frontend-dev

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

clean:
ifeq ($(OS),Windows_NT)
	if exist $(VENV) rmdir /s /q $(VENV)
	if exist local.db del /q local.db
	if exist frontend\node_modules rmdir /s /q frontend\node_modules
else
	rm -rf $(VENV) __pycache__ .pytest_cache local.db
	rm -rf frontend/node_modules frontend/dist
endif
