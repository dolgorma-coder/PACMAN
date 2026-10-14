"""State of a game in progress: what the engine updates and the UI draws."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from src.models.entity_models import Ghost, Player
from src.models.level_models import Level


class GameStatus(Enum):
    """Where a game currently is."""

    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()    # All the lives were lost.
    VICTORY = auto()      # All the levels were completed.


@dataclass
class Cheats:
    """Cheat mode switches, meant to make the peer review easier.

    The individual cheats can only be switched on while the cheat mode is
    enabled, and turning the mode off clears all of them. So a switch that
    is True is always really active.

    Attributes:
        enabled: Master switch of the cheat mode.
        invincible: Ghosts and the level timer cannot take lives.
        freeze_ghosts: Ghosts do not move.
        fast_player: The player moves twice as fast.
    """

    enabled: bool = False
    invincible: bool = False
    freeze_ghosts: bool = False
    fast_player: bool = False

    def toggle_enabled(self) -> None:
        """Turn the cheat mode on or off (off clears every switch)."""
        self.enabled = not self.enabled
        if not self.enabled:
            self.invincible = False
            self.freeze_ghosts = False
            self.fast_player = False

    def toggle_invincible(self) -> None:
        """Switch invincibility (only works in cheat mode)."""
        if self.enabled:
            self.invincible = not self.invincible

    def toggle_freeze_ghosts(self) -> None:
        """Switch the ghost freeze (only works in cheat mode)."""
        if self.enabled:
            self.freeze_ghosts = not self.freeze_ghosts

    def toggle_fast_player(self) -> None:
        """Switch the extra player speed (only works in cheat mode)."""
        if self.enabled:
            self.fast_player = not self.fast_player


@dataclass
class GameState:
    """Everything that changes while a game is played.

    Attributes:
        player: The player (it also holds score and lives).
        ghosts: The ghosts of the current level.
        level: The board of the current level.
        level_index: Index of the current level, starting at 0.
        level_count: Total number of levels of the game.
        time_left: Seconds left to finish the current level.
        status: Whether the game is running, paused or finished.
        cheats: Cheat mode switches.
    """

    player: Player
    ghosts: list[Ghost]
    level: Level
    level_index: int
    level_count: int
    time_left: float
    status: GameStatus = GameStatus.PLAYING
    cheats: Cheats = field(default_factory=Cheats)

    @property
    def level_number(self) -> int:
        """Current level as shown to the player (starting at 1)."""
        return self.level_index + 1
