"""Keyboard input: turns key presses into game commands and typed text.

With the keyboard of the current graphics library, this is the only module
(with `ui_canvas.py`) that has to change if the library changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pygame  # type: ignore

from src.models.app_models import Command, Screen

KEY_COMMANDS: dict[int, Command] = {
    pygame.K_UP: Command.UP, pygame.K_w: Command.UP,
    pygame.K_DOWN: Command.DOWN, pygame.K_s: Command.DOWN,
    pygame.K_LEFT: Command.LEFT, pygame.K_a: Command.LEFT,
    pygame.K_RIGHT: Command.RIGHT, pygame.K_d: Command.RIGHT,
    pygame.K_RETURN: Command.CONFIRM, pygame.K_KP_ENTER: Command.CONFIRM,
    pygame.K_ESCAPE: Command.BACK,
    pygame.K_p: Command.PAUSE,
    pygame.K_BACKSPACE: Command.ERASE,
    pygame.K_F1: Command.CHEAT_MODE,
    pygame.K_F2: Command.CHEAT_INVINCIBLE,
    pygame.K_F3: Command.CHEAT_FREEZE,
    pygame.K_F4: Command.CHEAT_SPEED,
    pygame.K_F5: Command.CHEAT_SKIP,
    pygame.K_F6: Command.CHEAT_LIFE,
}
# Keys that only work during the game: on the name screen digits and
# letters are text. The number keys repeat the cheats for keyboards where
# F-keys need "Fn"; M leaves the pause screen for the main menu.

GAME_ONLY_KEYS: dict[int, Command] = {
    pygame.K_1: Command.CHEAT_MODE,
    pygame.K_2: Command.CHEAT_INVINCIBLE,
    pygame.K_3: Command.CHEAT_FREEZE,
    pygame.K_4: Command.CHEAT_SPEED,
    pygame.K_5: Command.CHEAT_SKIP,
    pygame.K_6: Command.CHEAT_LIFE,
    pygame.K_m: Command.MAIN_MENU,
}

@dataclass
class FrameInput:
    """What the player did since the last frame.

    Attributes:
        quit: True if the window was closed.
        actions: Commands and typed text, in the order they happened (a
            `Command` is a key command, a `str` is typed text).
    """

    quit: bool = False
    actions: list[Command | str] = field(default_factory=list)


def read_input(screen: Screen) -> FrameInput:
    """Collect the events of this frame.

    Args:
        screen: The screen being shown. On the name-entry screen letters
            and digits are typed text; on the others they are commands.
    """
    frame = FrameInput()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            frame.quit = True
        elif event.type == pygame.KEYDOWN:
            _read_key(event.key, event.unicode, screen, frame)
    return frame


def _read_key(key: int, typed: str, screen: Screen,
              frame: FrameInput) -> None:
    """Add the action of one key press to `frame`."""
    if screen == Screen.GAME_END:
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            frame.actions.append(Command.CONFIRM)
        elif key == pygame.K_BACKSPACE:
            frame.actions.append(Command.ERASE)
        elif typed.isprintable() and typed:
            frame.actions.append(typed)
        return
    command = KEY_COMMANDS.get(key)
    if command is None and screen == Screen.GAME:
        command = GAME_ONLY_KEYS.get(key)
    if command is not None:
        frame.actions.append(command)
