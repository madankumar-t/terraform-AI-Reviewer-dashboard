.PHONY: help setup dev test clean docker-up docker-down install-frontend install-backend

help:
	@echo "Available commands:"
	@echo "  make setup          - Set up local development environment"
	@echo "  make install-frontend - Install frontend dependencies"
	@echo "  make install-backend  - Install backend dependencies"
	@echo "  make dev            - Start frontend development server"
	@echo "  make mock-api       - Start mock API server"
	@echo "  make test           - Run all tests"
	@echo "  make test-frontend  - Run frontend tests only"
	@echo "  make test-backend   - Run backend tests only"
	@echo "  make docker-up      - Start Docker services (DynamoDB, etc.)"
	@echo "  make docker-down    - Stop Docker services"
	@echo "  make clean          - Clean up generated files"

install-frontend:
	@cd frontend && npm install

install-backend:
	@cd backend/lambda && pip install -r requirements.txt

setup: install-frontend install-backend
	@bash scripts/testing/setup-local-env.sh

dev:
	@cd frontend && npm run dev

mock-api:
	@cd frontend && npm run mock-api

test:
	@cd frontend && npm test
	@cd backend/lambda && python -m pytest tests/ -v

test-backend:
	@cd backend/lambda && python -m pytest tests/ -v

test-frontend:
	@cd frontend && npm test

docker-up:
	@docker-compose up -d
	@echo "Docker services started"
	@echo "DynamoDB Local: http://localhost:8000"
	@echo "Mock API: http://localhost:3001"

docker-down:
	@docker-compose down
	@echo "Docker services stopped"

clean:
	@rm -rf frontend/.next
	@rm -rf frontend/node_modules/.cache
	@rm -rf backend/lambda/__pycache__
	@rm -rf backend/lambda/*.pyc
	@rm -rf .pytest_cache
	@echo "Cleanup complete"

