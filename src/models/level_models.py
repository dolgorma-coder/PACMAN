"""Level data: a maze with its collectibles and starting positions.

This module only stores the state of the board. How a level is built from
a maze is done in `level_builder.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.models.entity_models import Position
from src.models.maze_models import Maze


@dataclass
class Level:
    """The board of one level.

    Attributes:
        maze: The maze (walls and corridors).
        spawn: Cell where the player starts and respawns.
        ghost_homes: Cell where each ghost starts and respawns.
        pacgums: Cells that still hold a pacgum (small dot).
        super_pacgums: Cells that still hold a super-pacgum (power pellet).
    """

    maze: Maze
    spawn: Position
    ghost_homes: tuple[Position, ...]
    pacgums: set[Position] = field(default_factory=set)
    super_pacgums: set[Position] = field(default_factory=set)

    @property
    def is_complete(self) -> bool:
        """True when every pacgum has been eaten (the level is won)."""
        return not self.pacgums

    def eat_pacgum(self, position: Position) -> bool:
        """Remove the pacgum at `position`.

        Returns:
            True if there was a pacgum there, False otherwise.
        """
        if position in self.pacgums:
            self.pacgums.remove(position)
            return True
        return False

    def eat_super_pacgum(self, position: Position) -> bool:
        """Remove the super-pacgum at `position`.

        Returns:
            True if there was a super-pacgum there, False otherwise.
        """
        if position in self.super_pacgums:
            self.super_pacgums.remove(position)
            return True
        return False
