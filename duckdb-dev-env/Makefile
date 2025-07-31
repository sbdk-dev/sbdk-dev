.PHONY: setup test lint format notebook

setup:
	uv venv .venv && source .venv/bin/activate && \
	uv pip install --upgrade pip setuptools wheel && \
	uv pip install dlt duckdb pandas numpy jupyter pytest black flake8 mypy pre-commit && \
	pre-commit install

test:
	source .venv/bin/activate && pytest -s tests/

lint:
	source .venv/bin/activate && flake8 src/ tests/

format:
	source .venv/bin/activate && black src/ tests/

notebook:
	source .venv/bin/activate && jupyter lab
