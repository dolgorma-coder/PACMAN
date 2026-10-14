"""Adapter between the assigned A-Maze-ing package and our `Maze` model.

The package is used as-is. If its interface is different from what is
expected here, only this file has to change.
"""

from __future__ import annotations

from typing import Any

from src.models.config_models import LevelConfig
from src.models.maze_models import Maze, MazeError

# Largest valid cell value: the four wall bits set (1 + 2 + 4 + 8).
MAX_CELL_VALUE = 15


def _is_valid_cell(cell: Any) -> bool:
    """True if `cell` is an int made only of the four wall bits."""
    return (isinstance(cell, int) and not isinstance(cell, bool)
            and 0 <= cell <= MAX_CELL_VALUE)


def _build_maze(raw: Any, width: int, height: int) -> Maze:
    """Check the generator output and convert it to an immutable Maze.

    Raises:
        MazeError: If the output is not a `height` x `width` grid of
            valid cell values.
    """
    if not isinstance(raw, list) or len(raw) != height:
        raise MazeError("The generator returned a maze of the wrong size.")
    rows = []
    for row in raw:
        if not isinstance(row, list) or len(row) != width:
            raise MazeError("The generator returned a malformed row.")
        if not all(_is_valid_cell(cell) for cell in row):
            raise MazeError("The generator returned an invalid cell value.")
        rows.append(tuple(row))
    return Maze(width, height, tuple(rows))


def load_maze(level: LevelConfig) -> Maze:
    """Generate the maze of a level.

    Args:
        level: Size and seed of the level (seed 0 = random maze).

    Returns:
        A validated maze.

    Raises:
        MazeError: If the generator fails or returns unusable data.
    """
    try:
        # Package assigned to us (change this import if its name is
        # different). It is imported here so that a missing package is a
        # clean MazeError instead of a crash at start-up.
        from mazegenerator import MazeGenerator  # type: ignore

        # perfect=False makes loops and removes dead ends: corridors that
        # are good for Pac-Man (required by the subject).
        generator = MazeGenerator(size=(level.width, level.height),
                                  perfect=False, seed=level.seed)
        raw = generator.maze
    except Exception as error:
        # Third-party code: any exception type is possible, and none of
        # them may crash the game.
        raise MazeError(f"Maze generation failed: {error}") from error
    return _build_maze(raw, level.width, level.height)
