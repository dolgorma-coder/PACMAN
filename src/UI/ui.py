"""Graphical interface: window, main loop and choice of the screen to draw.

It does not contain any game rule. Every frame it:
    * reads the keyboard and gives it to the `App`;
    * lets the `App` advance the game;
    * draws the screen the `App` says is active.

The drawing itself is in `ui_game_view.py` and `ui_menu_views.py`, and all of
it goes through `ui_canvas.py`.
"""

from __future__ import annotations

from src.app import App
from src.models.app_models import Screen
from src.UI.ui_canvas import Canvas, CanvasError
from src.UI.ui_game_view import GameView
from src.UI.ui_input import read_input
from src.UI.ui_menu_views import (draw_game_end, draw_highscores,
                                  draw_instructions, draw_menu)
from src.UI.ui_theme import (BLACK, END_SCREEN_LOCK_MS,
                             FPS, WINDOW_HEIGHT, WINDOW_TITLE,
                             WINDOW_WIDTH)


class UIError(Exception):
    """Raised when the interface cannot start (for example, no display)."""


class Ui:
    """The window and the code that connects it to the `App`."""

    def __init__(self, app: App) -> None:
        """Open the window.

        Raises:
            UIError: If the window cannot be opened.
        """
        try:
            self.canvas = Canvas(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)
        except CanvasError as error:
            raise UIError(str(error)) from error
        self.app = app
        self.game_view = GameView(self.canvas)
        self._last_screen = app.screen
        self._locked_until = 0

    def frame(self) -> None:
        """Run one frame: wait, read the keyboard, update and draw."""
        delta_time = self.canvas.tick(FPS)
        self._handle_input()
        self.app.update(delta_time)
        self._draw()

    def close(self) -> None:
        """Close the window."""
        self.canvas.close()

    def _handle_input(self) -> None:
        """Give the keyboard to the app, in the order it was pressed."""
        now = self.canvas.ticks()
        screen = self.app.screen
        if screen != self._last_screen:
            self._last_screen = screen
            if screen == Screen.GAME_END:
                self._locked_until = now + END_SCREEN_LOCK_MS
        frame_input = read_input(screen)
        if frame_input.quit:
            self.app.running = False
            return
        if now < self._locked_until:
            return
        for action in frame_input.actions:
            if isinstance(action, str):
                self.app.handle_text(action)
            else:
                self.app.handle_command(action)

    def _draw(self) -> None:
        """Draw the active screen."""
        canvas, app = self.canvas, self.app
        canvas.clear(BLACK)
        if app.screen == Screen.MENU:
            draw_menu(canvas, app)
        elif app.screen == Screen.HIGHSCORES:
            draw_highscores(canvas, app)
        elif app.screen == Screen.INSTRUCTIONS:
            draw_instructions(canvas)
        elif app.screen == Screen.GAME:
            self.game_view.draw(app, canvas.ticks())
        else:
            draw_game_end(canvas, app, canvas.ticks())
        canvas.present()


def run(app: App) -> None:
    """Open the window and run the game until the player exits.

    Raises:
        UIError: If the window cannot be opened.
    """
    ui = Ui(app)
    try:
        while app.running:
            ui.frame()
    finally:
        ui.close()
