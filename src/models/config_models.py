"""Data classes that hold the game configuration.

This module contains only data and the safe default values. Reading and
validating the configuration file is done in `config.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

DEFAULT_SEED = 42
DEFAULT_LEVEL_COUNT = 10
DEFAULT_MAZE_SIZE = 15


@dataclass(frozen=True)
class LevelConfig:
    """Settings of one level.

    Attributes:
        width: Maze width, in cells.
        height: Maze height, in cells.
        seed: Maze seed. 0 means "random maze" (as in the generator).
    """

    width: int
    height: int
    seed: int


def default_levels(seed: int = DEFAULT_SEED) -> tuple[LevelConfig, ...]:
    """Return the default levels: square mazes growing one cell per level.

    Args:
        seed: Seed of the first level. All the other levels are random.
    """
    levels = []
    for index in range(DEFAULT_LEVEL_COUNT):
        size = DEFAULT_MAZE_SIZE + index
        level_seed = seed if index == 0 else 0
        levels.append(LevelConfig(size, size, level_seed))
    return tuple(levels)


@dataclass(frozen=True)
class GameConfig:
    """All the game settings. The defaults are the safe fallback values.

    Attributes:
        highscore_filename: File where the highscores are stored.
        lives: Lives at the start of the game.
        points_per_pacgum: Score for a pacgum.
        points_per_super_pacgum: Score for a super-pacgum.
        points_per_ghost: Score for an edible ghost.
        seed: Seed of the first level's maze (0 = random).
        level_max_time: Time limit of each level, in seconds.
        super_pacgum_duration: Seconds the ghosts stay edible.
        ghost_respawn_delay: Seconds an eaten ghost waits before returning.
        player_speed: Player speed, in cells per second.
        ghost_speed: Ghost speed, in cells per second.
        levels: Settings of every level, in play order.
    """

    highscore_filename: str = "highscores.json"
    lives: int = 3
    points_per_pacgum: int = 10
    points_per_super_pacgum: int = 50
    points_per_ghost: int = 200
    seed: int = DEFAULT_SEED
    level_max_time: int = 90
    levels: tuple[LevelConfig, ...] = field(default_factory=default_levels)

    super_pacgum_duration: float = 8.0
    ghost_respawn_delay: float = 5.0
    player_speed: float = 6.0
    ghost_speed: float = 5.0
