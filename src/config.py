"""Loading and validation of the configuration file (JSON with comments).

Error policy:
    * File problems (missing, unreadable, broken JSON) raise `ConfigError`.
      The caller prints the message and decides what to do.
    * Value problems (missing key, wrong type, out of range) never stop the
      game: the value is clamped or replaced by its default, and a warning
      is logged.
    * Unknown keys are ignored.
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any

from src.models.config_models import GameConfig, LevelConfig, default_levels

logger = logging.getLogger(__name__)

MAX_SEED = 2 ** 31 - 1
MAX_POINTS = 1_000_000
MAX_LEVELS = 100

# key -> (minimum, maximum). Int bounds are used for int settings and float
# bounds for float settings: the type is taken from the default value.
GAME_LIMITS: dict[str, tuple[float, float]] = {
    "lives": (1, 99),
    "points_per_pacgum": (0, MAX_POINTS),
    "points_per_super_pacgum": (0, MAX_POINTS),
    "points_per_ghost": (0, MAX_POINTS),
    "seed": (0, MAX_SEED),
    "level_max_time": (10, 3600),
    "super_pacgum_duration": (1.0, 60.0),
    "ghost_respawn_delay": (1.0, 60.0),
    "player_speed": (1.0, 20.0),
    "ghost_speed": (1.0, 20.0),
}
LEVEL_SIZE_LIMITS = (10, 60)


class ConfigError(Exception):
    """Raised when the configuration file itself cannot be used."""


# ---------------------------------------------------------------------------
# Value readers: they always return a usable value, whatever the input.
# ---------------------------------------------------------------------------

def _is_valid_number(value: Any, wants_int: bool) -> bool:
    """Tell if `value` is a usable number of the wanted kind."""
    if isinstance(value, bool):          # bool is an int subclass: reject it
        return False
    if wants_int:
        return isinstance(value, int)
    if isinstance(value, int):
        return True
    return isinstance(value, float) and math.isfinite(value)  # no NaN / inf


def _read_number(data: dict[str, Any], key: str, default: int | float,
                 limits: tuple[float, float],
                 where: str = "") -> int | float:
    """Read a number from `data`, clamped to `limits`.

    The result has the same type as `default` (int or float). If the key is
    missing or invalid, `default` is returned.

    Args:
        data: Dictionary to read from.
        key: Key to read.
        default: Fallback value, also defines the expected type.
        limits: (minimum, maximum), both included.
        where: Location prefix for log messages, e.g. "levels[2]".
    """
    label = f"{where}.{key}" if where else key
    if key not in data:
        logger.warning("Config: '%s' is missing, using %s.", label, default)
        return default
    value = data[key]
    wants_int = isinstance(default, int)
    if not _is_valid_number(value, wants_int):
        logger.warning("Config: '%s' has an invalid value (%.40r), "
                       "using %s.", label, value, default)
        return default
    clamped = max(limits[0], min(limits[1], value))
    if clamped != value:
        logger.warning("Config: '%s' is out of range [%s, %s], using %s.",
                       label, limits[0], limits[1], clamped)
    return int(clamped) if wants_int else float(clamped)


def _read_filename(data: dict[str, Any], default: str) -> str:
    """Read the highscore filename, or return `default` if unusable."""
    value = data.get("highscore_filename")
    if isinstance(value, str) and value.strip() and "\0" not in value:
        return value
    logger.warning("Config: 'highscore_filename' is missing or invalid, "
                   "using %r.", default)
    return default


# ---------------------------------------------------------------------------
# Levels
# ---------------------------------------------------------------------------

def _read_level(entry: Any, index: int,
                default_seed: int) -> LevelConfig | None:
    """Read one level of the "levels" list (None if it is not an object)."""
    where = f"levels[{index}]"
    if not isinstance(entry, dict):
        logger.warning("Config: %s must be an object, skipping it.", where)
        return None
    size = default_levels()[0].width
    width = _read_number(entry, "width", size, LEVEL_SIZE_LIMITS, where)
    height = _read_number(entry, "height", size, LEVEL_SIZE_LIMITS, where)
    seed = default_seed                  # a level seed is optional
    if "seed" in entry:
        seed = int(_read_number(entry, "seed", default_seed,
                                GAME_LIMITS["seed"], where))
    return LevelConfig(int(width), int(height), int(seed))


def _read_levels(data: dict[str, Any], seed: int) -> tuple[LevelConfig, ...]:
    """Read the "levels" list, falling back to the default levels.

    The global `seed` goes to the first valid level without its own seed;
    the other levels are random.
    """
    raw_levels = data.get("levels")
    if not isinstance(raw_levels, list) or not raw_levels:
        logger.warning("Config: 'levels' is missing or invalid, "
                       "using default levels.")
        return default_levels(seed)
    if len(raw_levels) > MAX_LEVELS:
        logger.warning("Config: too many levels, keeping the first %d.",
                       MAX_LEVELS)
        raw_levels = raw_levels[:MAX_LEVELS]

    levels: list[LevelConfig] = []
    for index, entry in enumerate(raw_levels, start=1):
        level = _read_level(entry, index, seed if not levels else 0)
        if level is not None:
            levels.append(level)
    if not levels:
        logger.warning("Config: no valid level, using default levels.")
        return default_levels(seed)
    return tuple(levels)


def strip_comments(text: str) -> str:
    """Blank out comment lines (starting with `#` or `//`).

    Lines are emptied, not removed, so JSON error line numbers still match
    the user's file.
    """
    return "\n".join(
        "" if line.lstrip().startswith(("#", "//")) else line
        for line in text.splitlines()
    )


def parse_config(data: dict[str, Any]) -> GameConfig:
    """Build a valid GameConfig from a dictionary. It never fails."""
    defaults = GameConfig()
    values: dict[str, Any] = {}
    for key, limits in GAME_LIMITS.items():
        values[key] = _read_number(data, key, getattr(defaults, key), limits)
    values["highscore_filename"] = _read_filename(
        data, defaults.highscore_filename)
    values["levels"] = _read_levels(data, values["seed"])
    return GameConfig(**values)


def load_config(path: str | Path) -> GameConfig:
    """Load and validate the configuration file.

    Args:
        path: Path of the JSON (with comments) file.

    Returns:
        A fully valid configuration.

    Raises:
        ConfigError: If the file is missing, unreadable, not valid JSON, or
            if its top level is not a JSON object.
    """
    try:
        with open(path, encoding="utf-8-sig") as config_file:
            text = config_file.read()
    except FileNotFoundError:
        raise ConfigError(f"Configuration file not found: {path}") from None
    except (OSError, ValueError) as error:   # includes decoding errors
        raise ConfigError(f"Cannot read {path}: {error}") from error

    try:
        data = json.loads(strip_comments(text))
    except (ValueError, RecursionError) as error:
        raise ConfigError(f"Invalid JSON in {path}: {error}") from error
    if not isinstance(data, dict):
        raise ConfigError(f"Invalid {path}: top level must be an object.")
    return parse_config(data)
