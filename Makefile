.DEFAULT_GOAL := check
.PHONY: sync lint format typecheck test test-fast cov check golden designs hooks

sync:  ## install the locked environment
	uv sync --locked --all-extras

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff check --fix .
	uv run ruff format .

typecheck:
	uv run pyright

test:
	uv run pytest

test-fast:
	uv run pytest -m "not slow"

cov:
	uv run pytest --cov --cov-report=term-missing

check: lint typecheck test

golden:  ## rerun the original Fusion 360 code on the stand-in and rewrite tests/golden
	uv run python -m tools.legacy.golden

designs:  ## build every design into out/
	uv run vedya build --all --out out

hooks:
	uv run pre-commit install
