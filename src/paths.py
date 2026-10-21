"""Resolve resource paths from the sources and from a frozen build.

When the game is packaged with PyInstaller, the bundled files (assets, ...)
are unpacked in the ``_internal`` folder and exposed through
``sys._MEIPASS``. When it runs from the sources, they live in the project
root. Use :func:`resource_path` for every read-only file shipped with the
game, and :func:`user_data_path` for files the game writes.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    """Tell whether the game runs from a PyInstaller build.

    Returns:
        True if frozen, False if it runs from the sources.
    """
    return bool(getattr(sys, "frozen", False))


def resource_path(relative: str) -> Path:
    """Return the absolute path of a file bundled with the game.

    Args:
        relative: Path relative to the project root, e.g. ``"assets"``.

    Returns:
        The absolute path, valid both from the sources and when frozen.
    """
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root is not None:
        root = Path(str(frozen_root))
    else:
        root = Path(__file__).resolve().parent.parent
    return root / relative


def default_config_path() -> Path:
    """Return the configuration file used when none is given.

    In a frozen build it is the ``config.json`` placed next to the
    executable, so the player can edit it. From the sources it is the one in
    the project root.

    Returns:
        The path of the default configuration file.
    """
    if is_frozen():
        return Path(sys.executable).resolve().parent / "config.json"
    return resource_path("config.json")


def enter_game_directory() -> None:
    """Make the folder of the executable the working directory.

    Only done in a frozen build, so that relative paths (such as the
    highscore file) always end up next to the game, wherever it was
    launched from. Does nothing when running from the sources.
    """
    if is_frozen():
        os.chdir(Path(sys.executable).resolve().parent)


def user_data_path(file_name: str) -> Path:
    """Return the path of a file the game writes, such as the highscores.

    The file lives in the current working directory, which in a frozen
    build is the folder of the executable (see
    :func:`enter_game_directory`), never the read-only bundle.

    Args:
        file_name: Name of the file, e.g. ``"highscores.json"``.

    Returns:
        The absolute path of the file in the working directory.
    """
    return Path.cwd() / file_name
