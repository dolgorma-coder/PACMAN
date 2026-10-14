"""Highscore data: name rules and the validated table entry.

Only data and validation live here. Reading and writing the highscore file
belongs to a separate module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

MAX_NAME_LENGTH = 10
MAX_SCORE = 999_999_999


def is_allowed_char(char: str) -> bool:
    """True for ASCII letters, digits and the space character."""
    return char.isascii() and (char.isalnum() or char == " ")


def sanitize_name(raw_name: str) -> str:
    """Turn text typed by the player into a valid name.

    Forbidden characters are dropped, surrounding spaces removed and the
    result is cut to MAX_NAME_LENGTH. It can be empty if nothing was valid.
    """
    cleaned = "".join(char for char in raw_name if is_allowed_char(char))
    return cleaned.strip()[:MAX_NAME_LENGTH]


def is_valid_name(name: str) -> bool:
    """True if `name` has 1 to MAX_NAME_LENGTH allowed characters.

    A name made only of spaces is not valid.
    """
    return (
        0 < len(name) <= MAX_NAME_LENGTH
        and bool(name.strip())
        and all(is_allowed_char(char) for char in name)
    )


@dataclass(frozen=True)
class HighscoreEntry:
    """One line of the highscore table.

    Attributes:
        name: Player name, see `is_valid_name`.
        score: Final score, between 0 and MAX_SCORE.

    Raises:
        ValueError: On creation, if the name or the score is invalid. An
            invalid entry can therefore never exist.
    """

    name: str
    score: int

    def __post_init__(self) -> None:
        """Validate the values."""
        if not is_valid_name(self.name):
            raise ValueError(f"Invalid highscore name: {self.name!r}")
        if not 0 <= self.score <= MAX_SCORE:
            raise ValueError(f"Invalid highscore score: {self.score!r}")

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly dictionary."""
        return {"name": self.name, "score": self.score}

    @classmethod
    def from_dict(cls, data: Any) -> HighscoreEntry:
        """Build an entry from untrusted data (e.g. read from a file).

        Raises:
            ValueError: If `data` is not a dict with a valid "name" (str)
                and "score" (int).
        """
        if not isinstance(data, dict):
            raise ValueError("A highscore entry must be an object.")
        name = data.get("name")
        score = data.get("score")
        if not isinstance(name, str):
            raise ValueError("A highscore name must be a string.")
        if isinstance(score, bool) or not isinstance(score, int):
            raise ValueError("A highscore score must be an integer.")
        return cls(name, score)
