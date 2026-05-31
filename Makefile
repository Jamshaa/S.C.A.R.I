.PHONY: help install deploy docker-build docker-up docker-down \
        docker-logs docker-clean test lint format clean

# Default target
help:
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║              🚀 S.C.A.R.I Make Commands 🚀                   ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Quick Deploy:"
	@echo "  make deploy        - Deploy with Docker (recommended)"
	@echo ""
	@echo "Docker Targets:"
	@echo "  make docker-build  - Build Docker images"
	@echo "  make docker-up     - Start all services"
	@echo "  make docker-down   - Stop all services"
	@echo "  make docker-logs   - View service logs"
	@echo "  make docker-clean  - Remove containers & images"
	@echo ""
	@echo "Development:"
	@echo "  make install       - Install all dependencies"
	@echo "  make test          - Run test suite"
	@echo "  make lint          - Lint code"
	@echo "  make format        - Format code"
	@echo "  make train         - Train thermal-safe model"
	@echo ""
	@echo "Utilities:"
	@echo "  make health        - Check service health"
	@echo "  make reset         - Reset entire system"
	@echo "  make clean         - Clean temp files"
	@echo ""

# ============================================================================
# DEPLOYMENT TARGETS
# ============================================================================

## One-line Docker deployment
deploy: docker-build docker-up health
	@echo ""
	@echo "✅ Deployment Complete!"
	@echo "   Frontend:  http://localhost:5173"
	@echo "   API:       http://localhost:8000"
	@echo "   Docs:      http://localhost:8000/docs"

## Build Docker images
docker-build:
	@echo "🔨 Building Docker images..."
	docker-compose build --no-cache

## Start Docker containers
docker-up:
	@echo "🚀 Starting services..."
	docker-compose up -d
	@echo "⏳ Waiting for services..."
	@sleep 5

## Stop Docker containers
docker-down:
	@echo "🛑 Stopping services..."
	docker-compose down

## View service logs
docker-logs:
	@echo "📋 Backend logs (Ctrl+C to exit):"
	docker-compose logs -f backend

## Remove containers and images
docker-clean:
	@echo "🧹 Cleaning Docker..."
	docker-compose down -v
	docker system prune -f -a

## Restart services
docker-restart: docker-down docker-up
	@echo "✅ Services restarted"

# ============================================================================
# DEPENDENCY INSTALLATION
# ============================================================================

## Create virtual environment
venv:
	@echo "📦 Creating virtual environment..."
	python3 -m venv venv

## Install Python dependencies
install-py: venv
	@echo "📦 Installing Python dependencies..."
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r requirements.txt

## Install frontend dependencies
install-ui:
	@echo "📦 Installing frontend dependencies..."
	cd ui && npm install

## Install all dependencies
install: install-py install-ui
	@echo "✅ All dependencies installed"

# ============================================================================
# TESTING & VALIDATION
# ============================================================================

## Run all tests
test:
	@echo "🧪 Running test suite..."
	python -m pytest tests/ -v --tb=short

## Run specific test
test-%:
	@echo "🧪 Running test: $*"
	python -m pytest tests/test_$*.py -v

## Run tests with coverage
test-coverage:
	@echo "📊 Running tests with coverage..."
	python -m pytest tests/ --cov=src --cov-report=html
	@echo "   Report: htmlcov/index.html"

## Lint Python code
lint:
	@echo "🔍 Linting Python code..."
	python -m flake8 src --max-line-length=100 || true
	python -m pylint src --disable=all --enable=E,F || true

## Format code
format:
	@echo "✨ Formatting code..."
	python -m black src --line-length=100 2>/dev/null || echo "Black not installed"
	python -m isort src 2>/dev/null || echo "isort not installed"

## Run full validation
validate: lint test
	@echo "✅ Validation complete"

# ============================================================================
# TRAINING & MODEL MANAGEMENT
# ============================================================================

## Train thermal-safe model
train:
	@echo "🧠 Training thermal-safe model..."
	python -m src.train \
		--timesteps 600000 \
		--config configs/default.yaml \
		--name scari_thermal_safe_v2

## Training with custom parameters
train-%:
	@echo "🧠 Training custom model: $*"
	python -m src.train --name $*

## Evaluate model
eval:
	@echo "📊 Evaluating model..."
	python -m src.evaluate --steps 10000

## List available models
models:
	@echo "📦 Available models:"
	@ls -lh data/models/ 2>/dev/null || echo "   No models found"

# ============================================================================
# HEALTH CHECKS & STATUS
# ============================================================================

## Check service health
health:
	@echo "💚 Checking system health..."
	@curl -s http://localhost:8000/health | python -m json.tool || echo "Backend not responding"
	@echo ""
	@echo "📊 Docker containers:"
	@docker-compose ps 2>/dev/null || echo "   Docker not running"

## Check all dependencies
check-deps:
	@echo "✅ Checking dependencies..."
	@python --version
	@node --version
	@docker --version 2>/dev/null || echo "   Docker: NOT INSTALLED"
	@docker-compose --version 2>/dev/null || echo "   Docker Compose: NOT INSTALLED"

# ============================================================================
# CLEANUP & RESET
# ============================================================================

## Reset entire system
reset: docker-clean clean
	@echo "🔄 System reset complete"
	@echo "   Run 'make deploy' to start fresh"

## Clean temporary files
clean:
	@echo "🧹 Cleaning temporary files..."
	python -c "import pathlib, shutil; [p.unlink() for p in pathlib.Path('.').rglob('*.pyc')]; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__')]; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('.pytest_cache')]" 2>/dev/null || true
	@echo "✅ Cleanup complete"

## Show environment status
status:
	@echo "📊 System Status"
	@echo "================"
	@echo ""
	@if [ -f ".env" ]; then \
		echo "✅ .env file present"; \
	else \
		echo "⚠️  .env file MISSING"; \
	fi
	@if [ -d "data/models" ]; then \
		echo "✅ Models directory exists"; \
	else \
		echo "⚠️  Models directory missing"; \
	fi
	@echo ""
	@docker-compose ps 2>/dev/null && echo "✅ Docker running" || echo "⚠️  Docker not running"
	@echo ""

## Show make version
version:
	@echo "Makefile for S.C.A.R.I v2.0-thermal-safe"

.DEFAULT_GOAL := help
