.DEFAULT_GOAL := check
.PHONY: sync lint format typecheck test test-fast slow cov check golden designs figures hooks

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

slow:  ## the slow tests: the Fusion 360 scripts from history, and the toolpaths
	uv run pytest -m slow

cov:
	uv run pytest --cov --cov-report=term-missing

check: lint typecheck test-fast  ## ruff, pyright and the fast tests; `make slow` runs the rest

golden:  ## rerun the original Fusion 360 code on the stand-in and rewrite tests/golden
	uv run python -m tools.legacy.golden

designs:  ## build every design `vedya list` names into out/; each file starts with its design's name
	for design in $$(uv run vedya list | cut -f1); do uv run vedya build "$$design" --out out || exit 1; done

figures:  ## build the designs and draw the README's images into docs/images/
	uv run --group docs python -m tools.figures

hooks:
	uv run pre-commit install
