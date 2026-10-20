"""Game entities: grid basics, the player and the ghosts.

Positions are expressed in maze cells, not in screen pixels. This module
knows nothing about the maze generator, the config file or the graphics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Protocol


# ---------------------------------------------------------------------------
# Grid basics
# ---------------------------------------------------------------------------

class Direction(Enum):
    """Movement directions. The value is the (dx, dy) step on the grid.

    The y axis points down (like on screen), so UP means y - 1.
    """

    UP = (0, -1)
    RIGHT = (1, 0)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    NONE = (0, 0)

    @property
    def dx(self) -> int:
        """Horizontal step: -1, 0 or 1."""
        step: tuple[int, int] = self.value
        return step[0]

    @property
    def dy(self) -> int:
        """Vertical step: -1, 0 or 1."""
        step: tuple[int, int] = self.value
        return step[1]

    @property
    def opposite(self) -> Direction:
        """The direction pointing the other way (NONE stays NONE)."""
        step: tuple[int, int] = self.value
        return Direction((-step[0], -step[1]))


@dataclass(frozen=True)
class Position:
    """A maze cell. Frozen, so it can be used in sets and as dict key.

    Attributes:
        x: Column, 0 is the left-most one.
        y: Row, 0 is the top one.
    """

    x: int
    y: int

    def moved(self, direction: Direction) -> Position:
        """Return the neighbouring cell one step in `direction`."""
        return Position(self.x + direction.dx, self.y + direction.dy)

    def distance_to(self, other: Position) -> int:
        """Return the Manhattan distance (|dx| + |dy|) to `other`."""
        return abs(self.x - other.x) + abs(self.y - other.y)


# ---------------------------------------------------------------------------
# Continuous movement
#
# Players and ghosts glide from cell to cell: `position` is the cell they
# left, `direction` is where they are heading and `move_progress` (0 to 1)
# tells how much of the way to the next cell is done.
# ---------------------------------------------------------------------------

class Moving(Protocol):
    """Anything that glides from cell to cell (the player and the ghosts)."""

    position: Position
    direction: Direction
    move_progress: float


def exact_position(mover: Moving) -> tuple[float, float]:
    """Return where a mover really is, in cells (fractions allowed).

    This is what has to be drawn and used for collisions.
    """
    progress = min(1.0, max(0.0, mover.move_progress))
    return (mover.position.x + mover.direction.dx * progress,
            mover.position.y + mover.direction.dy * progress)


def current_tile(mover: Moving) -> Position:
    """Return the cell the mover is closest to."""
    if mover.move_progress >= 0.5:
        return mover.position.moved(mover.direction)
    return mover.position


# ---------------------------------------------------------------------------
# Player
# ---------------------------------------------------------------------------

@dataclass
class Player:
    """The Pac-Man controlled by the human player.

    Attributes:
        spawn: Cell where the player starts and respawns.
        lives: Remaining lives. The game is over when it reaches 0.
        speed: Cells per second.
        score: Current score. It never decreases.
        position: Cell the player left (starts on `spawn`).
        direction: Direction of the current movement (NONE = standing).
        next_direction: Direction requested by the keyboard, applied as soon
            as the way is free (makes turning feel responsive).
        move_progress: Part of the way to the next cell already done (0-1).
        facing: Last direction the player moved in. The ghosts use it to
            guess where the player is going, even if it is standing.
    """

    spawn: Position
    lives: int = 3
    speed: float = 6.0
    score: int = 0
    position: Position = field(init=False)
    direction: Direction = Direction.NONE
    next_direction: Direction = Direction.NONE
    move_progress: float = 0.0
    facing: Direction = Direction.LEFT

    def __post_init__(self) -> None:
        """Start on the spawn cell."""
        self.position = self.spawn

    @property
    def is_alive(self) -> bool:
        """True while at least one life is left."""
        return self.lives > 0

    def add_score(self, points: int) -> None:
        """Add points. Negative values are ignored: the score never drops."""
        self.score += max(0, points)

    def lose_life(self) -> None:
        """Remove one life (never going below zero)."""
        self.lives = max(0, self.lives - 1)

    def respawn(self) -> None:
        """Go back to the spawn cell and stop moving."""
        self.position = self.spawn
        self.direction = Direction.NONE
        self.next_direction = Direction.NONE
        self.move_progress = 0.0
        self.facing = Direction.LEFT

    def start_level(self, spawn: Position) -> None:
        """Prepare for a new level: new spawn, same lives and score."""
        self.spawn = spawn
        self.respawn()


# ---------------------------------------------------------------------------
# Ghosts
# ---------------------------------------------------------------------------

class GhostState(Enum):
    """Behaviour mode of a ghost."""

    CHASING = auto()   # Normal: hunts the player (or goes to its corner).
    EDIBLE = auto()    # Super-pacgum eaten: runs away, can be eaten.
    EATEN = auto()     # Was eaten: eyes go back home as original pacman



@dataclass
class Ghost:
    """An enemy ghost.

    Attributes:
        name: Identifier of the ghost. It also selects its personality.
        home: Corner where the ghost starts, respawns and hides in the
            scatter phases.
        position: Cell the ghost left (starts on `home`).
        speed: Cells per second.
        direction: Direction of the current movement (NONE = standing).
        state: Current behaviour mode.
        timer: Seconds left in the EDIBLE or EATEN state.
        edible_left: Seconds of super-pacgum effect that remain while the
            ghost is EATEN. When it comes back it is edible again for
            that time, so it stays blue until the effect ends.
        move_progress: Part of the way to the next cell already done (0-1).
        angry: True while the ghost is in its "angry" mode (Blinky when few
            pacgums are left): it is faster and never stops chasing.
    """

    name: str
    home: Position
    position: Position = field(init=False)
    speed: float = 5.0
    direction: Direction = Direction.NONE
    state: GhostState = GhostState.CHASING
    timer: float = 0.0
    edible_left: float = 0.0
    move_progress: float = 0.0
    angry: bool = False

    def __post_init__(self) -> None:
        """Start on the home cell."""
        self.position = self.home

    @property
    def is_edible(self) -> bool:
        """True if the player can eat this ghost right now."""
        return self.state == GhostState.EDIBLE
   
    @property
    def at_home(self) -> bool:
        """True when the ghost is standing still on its home cell."""
        return (self.position == self.home
                and self.direction == Direction.NONE
                and self.move_progress == 0.0)
    
    @property
    def is_eaten(self) -> bool:
        """True while the ghost waits at home to respawn."""
        return self.state == GhostState.EATEN

    def make_edible(self, duration: float) -> None:
        """Become edible for `duration` seconds.

        If the ghost is eaten, it will come back already edible, for
        whatever is left of the effect.
        """
        if self.is_eaten:
            self.edible_left = duration
        else:
            self.state = GhostState.EDIBLE
            self.timer = duration

    def get_eaten(self, respawn_delay: float) -> None:
        """Become eyes: go home and wait `respawn_delay` seconds there.

        The ghost keeps moving from where it was eaten (the engine steers it
        home). The remaining edible time is kept, so it comes back blue if
        the super-pacgum effect is still running.
        """
        self.edible_left = self.timer if self.is_edible else 0.0
        self.state = GhostState.EATEN
        self.timer = respawn_delay

    def update_timer(self, delta_time: float) -> None:
        """Advance the countdown.

        EDIBLE ends in CHASING. EATEN waits until the ghost is back home,
        then counts the respawn delay and ends in EDIBLE if the
        super-pacgum effect is still active, or in CHASING otherwise.
        """
        if self.state == GhostState.CHASING:
            return
        if self.state == GhostState.EATEN:
            # The effect keeps running while the eyes travel and wait.
            self.edible_left = max(0.0, self.edible_left - delta_time)
            if not self.at_home:
                return
            self.timer -= delta_time
            if self.timer > 0:
                return
            if self.edible_left > 0:
                self.state = GhostState.EDIBLE
                self.timer = self.edible_left
            else:
                self.state = GhostState.CHASING
                self.timer = 0.0
            self.edible_left = 0.0
            return
        self.timer -= delta_time
        if self.timer <= 0:
            self.timer = 0.0
            self.state = GhostState.CHASING

            
    def reset(self, home: Position | None = None) -> None:
        """Go home and become dangerous again (life lost or new level)."""
        if home is not None:
            self.home = home
        self.position = self.home
        self.direction = Direction.NONE
        self.state = GhostState.CHASING
        self.timer = 0.0
        self.edible_left = 0.0
        self.move_progress = 0.0