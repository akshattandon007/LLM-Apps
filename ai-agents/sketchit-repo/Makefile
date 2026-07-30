# SketchIt — common dev commands
.PHONY: help install dev test lint format clean package icons

help:
	@echo "SketchIt — make targets"
	@echo ""
	@echo "  make install    Install backend dependencies (incl. dev)"
	@echo "  make dev        Start the backend with debug logging"
	@echo "  make test       Run backend tests"
	@echo "  make lint       Run ruff check"
	@echo "  make format     Run ruff format"
	@echo "  make icons      Regenerate extension icons from the SVG mark"
	@echo "  make package    Build a distributable zip of the extension"
	@echo "  make clean      Remove caches and build artefacts"

install:
	cd backend && pip install -r requirements-dev.txt

dev:
	cd backend && FLASK_DEBUG=1 python server.py

test:
	cd backend && pytest

lint:
	cd backend && ruff check .

format:
	cd backend && ruff format .

icons:
	cd extension && python generate_icons.py

package:
	cd extension && rm -f ../sketchit-extension.zip && \
		zip -r ../sketchit-extension.zip . \
		-x "generate_icons.py" "*.DS_Store" "__pycache__/*"
	@echo "✓ Built sketchit-extension.zip"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/.coverage backend/htmlcov
	rm -f sketchit-extension.zip
	@echo "✓ Cleaned"
