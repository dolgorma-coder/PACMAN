CONFIG ?= config.json
MAIN = pac-man.py
RUN = uv run --python=3.12 python3

.PHONY: install run debug clean lint lint-strict

install:
	uv pip install *.whl 
	uv sync

run:
	$(RUN) $(MAIN) $(CONFIG)

debug:
	$(RUN) -m pdb $(MAIN) $(CONFIG)

clean:
	find . -path ./.venv -prune -o -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache
	rm -f highscores.json

lint:
	uv run flake8 .
	uv run mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	uv run flake8 .
	uv run mypy . --strict
