.PHONY: format lint typecheck test

format:
	uv run ruff check --fix --select I .
	uv run ruff format .

lint: typecheck
	uv run ruff check .
	uv run ruff format --check .

typecheck:
	uv run mypy

test:
	uv run pytest demo
