"""Ghost behaviour, based on the original Pac-Man.

Every ghost has its own personality: the way it picks the cell it aims at
(its "target"). All the targets are in cells, and "ahead of Pac-Man" means
ahead in the direction it is facing.

    Blinky  Chases Pac-Man directly. In scatter mode he goes to the upper-
            right corner. When few pacgums are left he gets angry: he is
            faster and chases even in scatter mode.
    Pinky   Aims 4 cells ahead of Pac-Man. Original bug, kept on purpose: if
            Pac-Man faces up, the target is also 4 cells to the left.
            Scatter corner: upper-left.
    Inky    Takes the cell 2 ahead of Pac-Man (same bug) and doubles the
            vector that goes from Blinky to it: that is his target. Scatter
            corner: lower-right.
    Clyde   Chases Pac-Man, but when closer than 8 cells he runs to his
            scatter corner (lower-left) instead.

Every time a ghost reaches a cell it chooses where to go next:
    * it never turns back (unless there is no other way). The only
      exception is the scatter phase: a ghost that strays more than
      SCATTER_LEASH steps from its corner may turn back, so it keeps
      patrolling around the corner instead of crossing the whole maze;
    * an edible ghost takes the way that leads farthest from the player;
    * any other ghost takes the way with the shortest walk to its target
      (ties are broken in the order up, left, down, right, as in the
      original game).

Adaptation: the original game compares straight-line distances, which works
in its hand-made maze. Our mazes are random, so the ghosts use the real
walking distance instead. The targets, and therefore the personalities, are
exactly the original ones.
"""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass

from src.ghost_modes import GhostMode
from src.models.entity_models import Direction, Ghost, Position
from src.models.maze_models import DistanceField, Maze

PINKY_CELLS_AHEAD = 4
INKY_CELLS_AHEAD = 2
CLYDE_SHY_DISTANCE = 8
SCATTER_LEASH = 4          # Steps a scatter ghost may stray from its corner.
UNREACHABLE = 10 ** 9      # Distance given to cells that cannot be reached.
TIE_ORDER = (Direction.UP, Direction.LEFT, Direction.DOWN, Direction.RIGHT)


@dataclass(frozen=True)
class GhostContext:
    """What a ghost needs to know to decide where to go.

    Attributes:
        maze: The maze the ghosts walk in.
        player_tile: Cell the player is on.
        player_facing: Direction the player is facing.
        blinky_tile: Cell Blinky is on (Inky aims relative to it).
        mode: The current scatter / chase phase.
    """

    maze: Maze
    player_tile: Position
    player_facing: Direction
    blinky_tile: Position
    mode: GhostMode


def cells_ahead(tile: Position, facing: Direction, count: int) -> Position:
    """Return the cell `count` cells in front of `tile`.

    Reproduces the overflow bug of the original game: when facing up, the
    result is also `count` cells to the left.
    """
    if facing == Direction.UP:
        return Position(tile.x - count, tile.y - count)
    return Position(tile.x + facing.dx * count, tile.y + facing.dy * count)


# ---------------------------------------------------------------------------
# Personalities: where each ghost aims while chasing
# ---------------------------------------------------------------------------

def blinky_target(ghost: Ghost, context: GhostContext) -> Position:
    """Blinky aims straight at the player."""
    return context.player_tile


def pinky_target(ghost: Ghost, context: GhostContext) -> Position:
    """Pinky aims a few cells ahead of the player (an ambush)."""
    return cells_ahead(context.player_tile, context.player_facing,
                       PINKY_CELLS_AHEAD)


def inky_target(ghost: Ghost, context: GhostContext) -> Position:
    """Inky aims at the mirror of Blinky seen from a cell ahead of the player.

    The vector from Blinky to the cell 2 ahead of the player is doubled.
    """
    pivot = cells_ahead(context.player_tile, context.player_facing,
                        INKY_CELLS_AHEAD)
    blinky = context.blinky_tile
    return Position(2 * pivot.x - blinky.x, 2 * pivot.y - blinky.y)


def clyde_target(ghost: Ghost, context: GhostContext) -> Position:
    """Clyde chases the player, but is shy when he gets too close."""
    dx = ghost.position.x - context.player_tile.x
    dy = ghost.position.y - context.player_tile.y
    if dx * dx + dy * dy >= CLYDE_SHY_DISTANCE ** 2:
        return context.player_tile
    return ghost.home


CHASE_TARGETS: dict[str, Callable[[Ghost, GhostContext], Position]] = {
    "blinky": blinky_target,
    "pinky": pinky_target,
    "inky": inky_target,
    "clyde": clyde_target,
}


def target_cell(ghost: Ghost, context: GhostContext) -> Position:
    """Return the corridor cell the ghost aims at right now.

    In scatter mode that is its home corner (except for an angry ghost,
    which keeps chasing). The raw target can be a wall or be outside the
    maze, so it is moved to the closest corridor cell.
    """
    if context.mode == GhostMode.SCATTER and not ghost.angry:
        raw_target = ghost.home
    else:
        chase = CHASE_TARGETS.get(ghost.name, blinky_target)
        raw_target = chase(ghost, context)
    return context.maze.nearest_walkable(raw_target)


# ---------------------------------------------------------------------------
# Choosing the way
# ---------------------------------------------------------------------------

def _strayed_in_scatter(ghost: Ghost, context: GhostContext,
                        distances: DistanceField) -> bool:
    """True if a scatter ghost is too far from its corner and may turn back.

    `distances` are the walking distances to the ghost's target.
    """
    return (context.mode == GhostMode.SCATTER and not ghost.angry
            and distances.get(ghost.position, 0) >= SCATTER_LEASH)


def choose_direction(ghost: Ghost, context: GhostContext,
                     rng: random.Random) -> Direction:
    """Choose the direction a ghost takes from the cell it is on.

    Args:
        ghost: The ghost that has to move (standing on a cell).
        context: What the ghost knows about the game.
        rng: Random generator, used to break ties of an edible ghost
            (injected so tests can make it predictable).

    Returns:
        The chosen direction, or Direction.NONE if the ghost cannot move.
    """
    maze = context.maze
    options = maze.open_directions(ghost.position)
    if not options:
        return Direction.NONE

    if ghost.is_eaten:                        # Eyes: go straight home.
        if ghost.position == ghost.home:
            return Direction.NONE
        distances = maze.distance_field(ghost.home)
        return min(options, key=lambda d: (
            distances.get(ghost.position.moved(d), UNREACHABLE),
            TIE_ORDER.index(d)))

    # No turning back, unless it is the only way.
    ahead = [d for d in options if d != ghost.direction.opposite] or options

    if ghost.is_edible:
        distances = maze.distance_field(context.player_tile)
    else:
        distances = maze.distance_field(target_cell(ghost, context))
        if _strayed_in_scatter(ghost, context, distances):
            ahead = options

    def distance_after(direction: Direction) -> int:
        """Walking distance to the goal after moving in `direction`."""
        return distances.get(ghost.position.moved(direction), UNREACHABLE)

    if ghost.is_edible:                       # Run away.
        best = max(distance_after(d) for d in ahead)
        return rng.choice([d for d in ahead if distance_after(d) == best])
    best = min(distance_after(d) for d in ahead)
    candidates = [d for d in ahead if distance_after(d) == best]
    return min(candidates, key=TIE_ORDER.index)
