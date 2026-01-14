.PHONY: install test lint format typecheck clean

install:
	uv sync --all-extras

test:
	uv run pytest -v

test-cov:
	uv run pytest -v --cov=langgraph.checkpoint.neo4j --cov-report=term-missing

lint:
	uv run ruff check .

format:
	uv run ruff format .
	uv run ruff check --fix .

typecheck:
	uv run mypy langgraph/checkpoint/neo4j

clean:
	rm -rf .pytest_cache .coverage .mypy_cache __pycache__ dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Demo commands
demo-up:
	docker-compose -f docker-compose.dev.yml up -d

demo-down:
	docker-compose -f docker-compose.dev.yml down

demo-logs:
	docker-compose -f docker-compose.dev.yml logs -f
