"""Vocabulary shared by the application logic and the user interface.

The UI translates keyboard events into `Command` values and reads the
`Screen`, `MenuItem` and `PauseItem` values to know what to draw.
"""

from __future__ import annotations

from enum import Enum, auto


class Screen(Enum):
    """The screens of the game loop:
    menu > game > end of game (name entry) > menu.
    """

    MENU = auto()
    HIGHSCORES = auto()
    INSTRUCTIONS = auto()
    GAME = auto()         # Includes the pause menu.
    GAME_END = auto()     # Game over / victory, with the name prompt.


class Command(Enum):
    """Something the player asked for, independent of the keyboard layout."""

    UP = auto()           # Arrow up / W
    DOWN = auto()         # Arrow down / S
    LEFT = auto()         # Arrow left / A
    RIGHT = auto()        # Arrow right / D
    CONFIRM = auto()      # Enter
    BACK = auto()         # Escape
    PAUSE = auto()        # P
    ERASE = auto()        # Backspace (name entry)
    CHEAT_MODE = auto()
    CHEAT_INVINCIBLE = auto()
    CHEAT_FREEZE = auto()
    CHEAT_SPEED = auto()
    CHEAT_SKIP = auto()
    CHEAT_LIFE = auto()


class MenuItem(Enum):
    """Main menu entries. The value is the label to display."""

    START = "Start Game"
    HIGHSCORES = "View Highscores"
    INSTRUCTIONS = "Instructions"
    EXIT = "Exit"


class PauseItem(Enum):
    """Pause menu entries. The value is the label to display."""

    RESUME = "Resume the game"
    MAIN_MENU = "Return to the main menu"


INSTRUCTION_LINES: tuple[str, ...] = (
    "Controls",
    "  Arrow keys or WASD: move",
    "  P or Escape: pause / resume",
    "  Enter: confirm        Escape: go back",
    "",
    "Rules",
    "  Eat all the pacgums to complete a level.",
    "  Super-pacgums make the ghosts edible for a short time.",
    "  Touching a ghost costs a life; edible ghosts give points.",
    "  Each level has a time limit: when it ends you lose a life.",
    "  Complete all the levels to win the game.",
)
