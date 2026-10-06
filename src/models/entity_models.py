"""Game entities: grid basics, the player and the ghosts.

Positions are expressed in maze cells, not in screen pixels. This module
knows nothing about the maze generator, the config file or the graphics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


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
        """Return the¡ distance (|dx| + |dy|) to `other` position."""
        return abs(self.x - other.x) + abs(self.y - other.y)


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
        position: Current cell (starts on `spawn`).
        direction: Direction of the current movement.
        next_direction: Direction requested by the keyboard, applied as soon
            as the way is free (makes turning feel responsive).
    """

    spawn: Position
    lives: int = 3
    speed: float = 6.0
    score: int = 0
    position: Position = field(init=False)
    direction: Direction = Direction.NONE
    next_direction: Direction = Direction.NONE

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

    def start_level(self, spawn: Position) -> None:
        """Prepare for a new level: new spawn, same lives and score."""
        self.spawn = spawn
        self.respawn()


# ---------------------------------------------------------------------------
# Ghosts
# ---------------------------------------------------------------------------

class GhostState(Enum):
    """Behaviour mode of a ghost."""

    CHASING = auto()   # Normal: hunts the player.
    EDIBLE = auto()    # Super-pacgum eaten: runs away, can be eaten.
    EATEN = auto()     # Was eaten: waits at home before coming back.


@dataclass
class Ghost:
    """An enemy ghost.

    Attributes:
        name: Identifier of the ghost (also useful to pick its colour).
        home: Corner where the ghost starts and respawns.
        position: Current cell (starts on `home`).
        speed: Cells per second.
        direction: Direction of the current movement.
        state: Current behaviour mode.
        timer: Seconds left in the EDIBLE or EATEN state.
    """

    name: str
    home: Position
    position: Position = field(init=False)
    speed: float = 5.0
    direction: Direction = Direction.NONE
    state: GhostState = GhostState.CHASING
    timer: float = 0.0

    def __post_init__(self) -> None:
        """Start on the home cell."""
        self.position = self.home

    @property
    def is_edible(self) -> bool:
        """True if the player can eat this ghost right now."""
        return self.state == GhostState.EDIBLE

    @property
    def is_eaten(self) -> bool:
        """True while the ghost waits at home to respawn."""
        return self.state == GhostState.EATEN

    def make_edible(self, duration: float) -> None:
        """Become edible for `duration` seconds (ignored if eaten)."""
        if not self.is_eaten:
            self.state = GhostState.EDIBLE
            self.timer = duration

    def get_eaten(self, respawn_delay: float) -> None:
        """Go back home and wait `respawn_delay` seconds before chasing."""
        self.state = GhostState.EATEN
        self.timer = respawn_delay
        self.position = self.home
        self.direction = Direction.NONE

    def update_timer(self, delta_time: float) -> None:
        """Advance the countdown; at zero the ghost goes back to CHASING."""
        if self.state == GhostState.CHASING:
            return
        self.timer -= delta_time
        if self.timer <= 0:
            self.timer = 0.0
            self.state = GhostState.CHASING

    def reset(self, home: Position | None = None) -> None:
        """Go home and become dangerous again (life lost or new level).

        Args:
            home: New home cell for a new maze. None keeps the current one.
        """
        if home is not None:
            self.home = home
        self.position = self.home
        self.direction = Direction.NONE
        self.state = GhostState.CHASING
        self.timer = 0.0
