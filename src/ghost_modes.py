"""The scatter / chase rhythm shared by all the ghosts.

As in the original game, the ghosts alternate between two phases:

    SCATTER: every ghost goes to its own corner, so the player can breathe.
    CHASE:   every ghost hunts the player in its own way.

The schedule below is the one of the first level of the original game: the
last chase never ends.
"""

from __future__ import annotations

import math
from enum import Enum, auto


class GhostMode(Enum):
    """The phase the ghosts are in."""

    SCATTER = auto()
    CHASE = auto()


# (mode, seconds). The last phase lasts forever.
DEFAULT_SCHEDULE: tuple[tuple[GhostMode, float], ...] = (
    (GhostMode.SCATTER, 7.0),
    (GhostMode.CHASE, 20.0),
    (GhostMode.SCATTER, 7.0),
    (GhostMode.CHASE, 20.0),
    (GhostMode.SCATTER, 5.0),
    (GhostMode.CHASE, 20.0),
    (GhostMode.SCATTER, 5.0),
    (GhostMode.CHASE, math.inf),
)


class ModeSchedule:
    """Keeps track of the current phase and when it ends."""

    def __init__(self, phases: tuple[tuple[GhostMode, float], ...]
                 = DEFAULT_SCHEDULE) -> None:
        """Start on the first phase.

        Raises:
            ValueError: If `phases` is empty.
        """
        if not phases:
            raise ValueError("A schedule needs at least one phase.")
        self._phases = phases
        self._index = 0
        self._seconds_left = phases[0][1]

    @property
    def mode(self) -> GhostMode:
        """The current phase."""
        return self._phases[self._index][0]

    def reset(self) -> None:
        """Start again from the first phase."""
        self._index = 0
        self._seconds_left = self._phases[0][1]

    def update(self, delta_time: float) -> bool:
        """Let time pass.

        Returns:
            True if the mode is different from before (the ghosts then
            have to turn around).
        """
        before = self.mode
        self._seconds_left -= delta_time
        while self._seconds_left <= 0 and self._index < len(self._phases) - 1:
            self._index += 1
            self._seconds_left += self._phases[self._index][1]
        return self.mode != before
