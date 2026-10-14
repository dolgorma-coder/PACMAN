"""Entry point of the game.

Usage:
    python3 pac-man.py config.json
"""

from __future__ import annotations

import logging
import sys

from src.ui_example import ui
from src.app import App
from src.config import ConfigError, load_config


def main(argv: list[str]) -> int:
    """Run the game.

    Args:
        argv: Command line arguments, the program name included.

    Returns:
        The exit code of the process: 0 if everything went well.
    """
    if len(argv) != 2:
        print("Usage: python3 pac-man.py <config.json>", file=sys.stderr)
        return 1
    logging.basicConfig(level=logging.WARNING,
                        format="%(levelname)s: %(message)s")
    try:
        config = load_config(argv[1])
    except ConfigError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    try:
        ui.run(App(config))
    except ui.UIError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
    except Exception as error:
        # Last safety net: the player must never see a traceback.
        print(f"Unexpected error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
