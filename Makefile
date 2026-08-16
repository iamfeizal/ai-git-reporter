.PHONY: help install run docker-up docker-down clean

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
	@echo "  make install     - Create a virtual environment and install dependencies"
	@echo "  make run         - Run the application locally (without Docker)"
	@echo "  make docker-up   - Start the application using Docker Compose"
	@echo "  make docker-down - Stop the Docker containers"
	@echo "  make clean       - Remove the virtual environment and cached files"

install:
	python -m venv $(VENV)
	$(PIP) install -r requirements.txt

run:
	$(UVICORN) app.main:app --reload

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

clean:
ifeq ($(OS),Windows_NT)
	if exist $(VENV) rmdir /s /q $(VENV)
	if exist local.db del /q local.db
else
	rm -rf $(VENV) __pycache__ .pytest_cache local.db
endif
