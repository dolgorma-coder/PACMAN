"""Build a playable level from a maze.

Rules (from the subject):
    * the player starts in the middle of the maze;
    * the 4 ghosts start in the 4 corners;
    * the super-pacgums are in the 4 corners;
    * pacgums fill the other corridors.

Only cells reachable from the player's spawn are ever used, so the level
can always be completed.
"""

from __future__ import annotations

from collections.abc import Iterable

from src.models.entity_models import Ghost, Position
from src.models.level_models import Level
from src.models.maze_models import Maze, MazeError

GHOST_NAMES = ("blinky", "pinky", "inky", "clyde")
# Corner of each ghost, as an index in `Level.ghost_homes` (top-left,
# top-right, bottom-left, bottom-right). They are the scatter corners of the
# original game: Blinky upper-right, Pinky upper-left, Inky lower-right and
# Clyde lower-left.
GHOST_CORNERS = {"blinky": 1, "pinky": 0, "inky": 3, "clyde": 2}


def _nearest(cells: Iterable[Position], target: Position) -> Position:
    """Return the cell closest to `target`.

    Ties are broken by row, then column, so the result is always the same
    for the same maze (the game stays reproducible with a fixed seed).
    """
    return min(cells, key=lambda cell: (cell.distance_to(target),
                                        cell.y, cell.x))


def find_spawn(maze: Maze) -> Position:
    """Return the corridor cell closest to the center of the maze.

    The center itself may be solid (the generator draws a "42" there), so
    the closest walkable cell is used instead.

    Raises:
        MazeError: If the maze has no corridor at all.
    """
    walkable = [Position(x, y)
                for y in range(maze.height)
                for x in range(maze.width)
                if maze.is_walkable(Position(x, y))]
    if not walkable:
        raise MazeError("The maze has no corridor.")
    center = Position(maze.width // 2, maze.height // 2)
    return _nearest(walkable, center)


def find_corners(maze: Maze, cells: set[Position]) -> tuple[Position, ...]:
    """Return, for each corner of the maze, the closest cell of `cells`."""
    last_x, last_y = maze.width - 1, maze.height - 1
    corners = (Position(0, 0), Position(last_x, 0),
               Position(0, last_y), Position(last_x, last_y))
    return tuple(_nearest(cells, corner) for corner in corners)


def build_level(maze: Maze) -> Level:
    """Create a level from a maze.

    Args:
        maze: A validated maze.

    Returns:
        The level, with spawn, ghost homes, pacgums and super-pacgums.

    Raises:
        MazeError: If the maze is too small or too broken to hold a level
            (no corridor, or spawn and corners are not 5 different cells).
    """
    spawn = find_spawn(maze)
    reachable = maze.reachable_from(spawn)
    corners = find_corners(maze, reachable)

    if len(set(corners) | {spawn}) != 5:
        raise MazeError("The maze is too small to place the player, "
                        "the ghosts and the super-pacgums.")

    # Everything reachable gets a pacgum, except the special cells.
    pacgums = reachable - {spawn} - set(corners)
    return Level(maze=maze, spawn=spawn, ghost_homes=corners,
                 pacgums=pacgums, super_pacgums=set(corners))


def create_ghosts(level: Level, speed: float) -> list[Ghost]:
    """Create the four ghosts, each one in its own corner.

    Args:
        level: The level whose ghost homes are used.
        speed: Ghost speed, in cells per second.
    """
    return [Ghost(name=name, home=level.ghost_homes[GHOST_CORNERS[name]],
                  speed=speed)
            for name in GHOST_NAMES]
