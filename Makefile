CONFIG ?= config.json
MAIN = pac-man.py
RUN = uv run --python=3.12 python3
ITCH_TARGET ?= YOUR_USER/pacman

.PHONY: install run debug clean lint lint-strict package publish

install:
	uv pip install *.whl
	uv sync

run:
	$(RUN) $(MAIN) $(CONFIG)

debug:
	$(RUN) -m pdb $(MAIN) $(CONFIG)

clean:
	find . -path ./.venv -prune -o -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache build dist
	rm -f highscores.json

lint:
	uv run flake8 src/. pac-man.py
	uv run mypy src/. pac-man.py --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	uv run flake8 src/. pac-man.py
	uv run mypy src/. pac-man.py --strict

package:
	uv run pyinstaller --noconfirm --clean pacman.spec
	cp config.json PLAYER_README.txt dist/pacman/
	cd dist && zip -r pacman-linux.zip pacman

publish: package
	butler push dist/pacman-linux.zip $(ITCH_TARGET):linux