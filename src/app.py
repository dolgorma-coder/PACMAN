"""Application logic: which screen is shown and what each command does.

The UI only has to forward the player's input and draw what it finds here:

    app.handle_command(command)   # a key press, as a `Command`
    app.handle_text(text)         # typed characters (name entry)
    app.update(delta_time)        # once per frame
    app.screen, app.menu_index, app.highscores, app.engine ...  # to draw

Nothing here depends on a graphics library, and no input can crash it.
"""

from __future__ import annotations

from collections.abc import Callable

from src.models.app_models import Command, MenuItem, Screen
from src.models.config_models import GameConfig
from src.models.entity_models import Direction
from src.game_engine import GameEngine
from src.models.game_state import GameStatus
from src.highscore_manager import (add_highscore,
                                   load_highscores, save_highscores)
from src.models.highscore_models import MAX_NAME_LENGTH, is_allowed_char
from src.models.maze_models import MazeError

DIRECTION_COMMANDS: dict[Command, Direction] = {
    Command.UP: Direction.UP,
    Command.DOWN: Direction.DOWN,
    Command.LEFT: Direction.LEFT,
    Command.RIGHT: Direction.RIGHT,
}

CHEAT_COMMANDS: dict[Command, Callable[[GameEngine], None]] = {
    Command.CHEAT_MODE: GameEngine.toggle_cheat_mode,
    Command.CHEAT_INVINCIBLE: GameEngine.toggle_invincible,
    Command.CHEAT_FREEZE: GameEngine.toggle_freeze_ghosts,
    Command.CHEAT_SPEED: GameEngine.toggle_fast_player,
    Command.CHEAT_SKIP: GameEngine.skip_level,
    Command.CHEAT_LIFE: GameEngine.add_life,
}


def _move_selection(index: int, count: int, command: Command) -> int:
    """Move a menu selection up or down, wrapping around the ends."""
    if command == Command.UP:
        return (index - 1) % count
    if command == Command.DOWN:
        return (index + 1) % count
    return index


class App:
    """The whole application state, driven by commands.

    Attributes:
        config: Game settings.
        screen: The screen to show.
        running: False once the player chose Exit.
        highscores: The highscore table (best first).
        menu_index: Selected entry of the main menu (see `MenuItem`).
        engine: The game in progress, if any.
        message: One-line notice to display (errors), empty if none.
        final_score: Score of the game that just ended.
        won: True if that game ended with a victory.
        name_buffer: Name being typed at the end of a game.
    """

    def __init__(self, config: GameConfig) -> None:
        """Create the app on the main menu and load the highscores."""
        self.config = config
        self.screen = Screen.MENU
        self.running = True
        self.highscores = load_highscores(config.highscore_filename)
        self.menu_index = 0
        self.engine: GameEngine | None = None
        self.message = ""
        self.final_score = 0
        self.won = False
        self.name_buffer = ""
        self._handlers: dict[Screen, Callable[[Command], None]] = {
            Screen.MENU: self._menu_command,
            Screen.HIGHSCORES: self._info_command,
            Screen.INSTRUCTIONS: self._info_command,
            Screen.GAME: self._game_command,
            Screen.GAME_END: self._end_command,
        }

    # -----------------------------------------------------------------
    # Input from the UI
    # -----------------------------------------------------------------

    def handle_command(self, command: Command) -> None:
        """React to a command, according to the current screen."""
        self.message = ""
        self._handlers[self.screen](command)

    def handle_text(self, text: str) -> None:
        """Add typed characters to the name (only on the end screen).

        Characters that are not allowed in a name are ignored, and the name
        never grows beyond MAX_NAME_LENGTH.
        """
        if self.screen != Screen.GAME_END:
            return
        for char in text:
            if len(self.name_buffer) >= MAX_NAME_LENGTH:
                break
            if is_allowed_char(char):
                self.name_buffer += char

    def update(self, delta_time: float) -> None:
        """Advance the game and detect its end. Call it once per frame."""
        if self.screen != Screen.GAME or self.engine is None:
            return
        self.engine.update(delta_time)
        status = self.engine.state.status
        if status in (GameStatus.GAME_OVER, GameStatus.VICTORY):
            self.final_score = self.engine.state.player.score
            self.won = status == GameStatus.VICTORY
            self.name_buffer = ""
            self.screen = Screen.GAME_END

    # -----------------------------------------------------------------
    # Main menu and information screens
    # -----------------------------------------------------------------

    def _menu_command(self, command: Command) -> None:
        """Navigate the main menu."""
        items = list(MenuItem)
        self.menu_index = _move_selection(self.menu_index, len(items),
                                          command)
        if command != Command.CONFIRM:
            return
        item = items[self.menu_index]
        if item == MenuItem.START:
            self._start_game()
        elif item == MenuItem.HIGHSCORES:
            self.screen = Screen.HIGHSCORES
        elif item == MenuItem.INSTRUCTIONS:
            self.screen = Screen.INSTRUCTIONS
        else:
            self.running = False

    def _info_command(self, command: Command) -> None:
        """Highscores and instructions: any 'back' key returns to menu."""
        if command in (Command.BACK, Command.CONFIRM):
            self.screen = Screen.MENU

    def _start_game(self) -> None:
        """Start a new game, or show why it cannot be started."""
        try:
            self.engine = GameEngine(self.config)
        except MazeError as error:
            self.message = f"Cannot start the game: {error}"
            return
        self.pause_index = 0
        self.screen = Screen.GAME

    # -----------------------------------------------------------------
    # Game and pause menu
    # -----------------------------------------------------------------

    def _game_command(self, command: Command) -> None:
        """Handle the commands of a game in progress."""
        engine = self.engine
        if engine is None:                    # Should not happen.
            self.screen = Screen.MENU
            return
        if engine.state.status == GameStatus.PAUSED:
            self._pause_command(engine, command)
        elif command in DIRECTION_COMMANDS:
            engine.set_direction(DIRECTION_COMMANDS[command])
        elif command in (Command.PAUSE, Command.BACK):
            engine.toggle_pause()
        elif command in CHEAT_COMMANDS:
            CHEAT_COMMANDS[command](engine)

    def _pause_command(self, engine: GameEngine, command: Command) -> None:
        """Pause screen: P / Escape resume, M goes to the main menu."""
        if command in (Command.PAUSE, Command.BACK):
            engine.toggle_pause()
        elif command == Command.MAIN_MENU:     # Leave without saving.
            self.engine = None
            self.screen = Screen.MENU
            
    # -----------------------------------------------------------------
    # End of game
    # -----------------------------------------------------------------

    def _end_command(self, command: Command) -> None:
        """Name entry: erase a letter, or confirm and save the score."""
        if command == Command.ERASE:
            self.name_buffer = self.name_buffer[:-1]
        elif command == Command.CONFIRM:
            self._submit_score()

    def _submit_score(self) -> None:
        """Save the score (an empty name becomes a default one)."""
        self.highscores = add_highscore(
            self.highscores, self.name_buffer, self.final_score)
        if not save_highscores(self.config.highscore_filename,
                               self.highscores):
            self.message = "The highscores could not be saved."
        self.engine = None
        self.name_buffer = ""
        self.screen = Screen.MENU
