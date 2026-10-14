"""Persistent highscore table: the top 10 scores stored in a JSON file.

File format:
    {"highscores": [{"name": "Ana", "score": 1200}, ...]}

Nothing in this module may crash the game: a missing, corrupted or
unwritable file is logged and handled.
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
from pathlib import Path
from typing import Any

from src.models.highscore_models import (MAX_SCORE, HighscoreEntry,
                                         sanitize_name)

logger = logging.getLogger(__name__)

MAX_ENTRIES = 10
MAX_FILE_CHARS = 1_000_000     # Refuse absurdly big files.
DEFAULT_NAME = "PLAYER"        # Used if the player types no valid name.


def _top_entries(entries: list[HighscoreEntry]) -> list[HighscoreEntry]:
    """Return the best MAX_ENTRIES entries, best first.

    The sort is stable: with equal scores, the older entry stays first.
    """
    return sorted(entries, key=lambda entry: -entry.score)[:MAX_ENTRIES]


def _parse_entries(data: Any) -> list[HighscoreEntry]:
    """Convert untrusted JSON data to entries, skipping the invalid ones."""
    raw_entries = data.get("highscores") if isinstance(data, dict) else None
    if not isinstance(raw_entries, list):
        logger.warning("Highscores: unexpected file format, ignoring it.")
        return []
    entries = []
    for raw_entry in raw_entries:
        try:
            entries.append(HighscoreEntry.from_dict(raw_entry))
        except ValueError as error:
            logger.warning("Highscores: skipping invalid entry (%s).", error)
    return entries


def load_highscores(path: str | Path) -> list[HighscoreEntry]:
    """Load the highscores. Any problem gives an empty (or partial) list.

    Args:
        path: Path of the highscore file.

    Returns:
        Up to MAX_ENTRIES valid entries, best first.
    """
    try:
        with open(path, encoding="utf-8-sig") as score_file:
            text = score_file.read(MAX_FILE_CHARS + 1)
    except FileNotFoundError:
        return []                         # Normal on the first run.
    except (OSError, ValueError) as error:    # includes decoding errors
        logger.warning("Highscores: cannot read %s (%s).", path, error)
        return []
    if len(text) > MAX_FILE_CHARS:
        logger.warning("Highscores: %s is too big, ignoring it.", path)
        return []

    try:
        data = json.loads(text)
    except (ValueError, RecursionError) as error:
        logger.warning("Highscores: invalid JSON in %s (%s).", path, error)
        return []
    return _top_entries(_parse_entries(data))


def add_highscore(entries: list[HighscoreEntry], name: str,
                  score: int) -> list[HighscoreEntry]:
    """Return a new table with the given result added.

    The name is cleaned (see `sanitize_name`) and the score is kept in the
    valid range, so any input is accepted. `entries` is not modified.

    Args:
        entries: Current table.
        name: Name typed by the player.
        score: Final score of the player.

    Returns:
        The best MAX_ENTRIES entries, best first.
    """
    clean_name = sanitize_name(name) or DEFAULT_NAME
    clean_score = max(0, min(MAX_SCORE, score))
    return _top_entries([*entries, HighscoreEntry(clean_name, clean_score)])


def save_highscores(path: str | Path, entries: list[HighscoreEntry]) -> bool:
    """Save the table to disk.

    The data is written to a temporary file first and then moved over the
    real one, so a crash while saving cannot corrupt the existing table.

    Args:
        path: Path of the highscore file.
        entries: Table to save.

    Returns:
        True if the file was saved, False if saving failed (already logged).
    """
    target = Path(path)
    temp_file = target.with_name(target.name + ".tmp")
    data = {"highscores": [entry.to_dict()
                           for entry in _top_entries(list(entries))]}
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_file, "w", encoding="utf-8") as score_file:
            json.dump(data, score_file, indent=2)
        os.replace(temp_file, target)
    except (OSError, ValueError) as error:
        logger.warning("Highscores: cannot save %s (%s).", path, error)
        with contextlib.suppress(OSError, ValueError):
            temp_file.unlink(missing_ok=True)
        return False
    return True
