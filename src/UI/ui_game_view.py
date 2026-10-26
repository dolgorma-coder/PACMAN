"""Game view: draws the maze, items, entities, HUD, pause menu and charts.

This module uses only the basic primitives of the canvas and contains no
direct graphical library imports.
"""

from __future__ import annotations

from typing import Any

from src.app import App
from src.models.game_state import GameStatus
from src.UI.ui_canvas import Canvas
from src.UI.ui_theme import (DARK_BLUE, LIGHT_BLUE, NEON_YELLOW,
                             TEXT_WHITE, WHITE)

# Horizontal centre of each HUD column, in pixels.
SCORE_CENTER_X: int = 160
TIME_CENTER_X: int = 480
LEVEL_CENTER_X: int = 800
HIGH_SCORE_CENTER_X: int = 1120

# Vertical position of the HUD labels and of their values.
HUD_LABEL_Y: int = 25
HUD_VALUE_Y: int = 34

# Approximate pixel width of one character of a label / of a value.
LABEL_CHAR_WIDTH: int = 16
VALUE_CHAR_WIDTH: int = 20

# Attribute names under which the maze grid may be stored.
GRID_ATTRIBUTES: tuple[str, ...] = (
    "grid", "_grid", "matrix", "map", "board", "cells")

CHEAT_HINT: str = ("CHEAT MODE ACTIVE:  F2: INVINCIBLE  |  "
                   "F3: FREEZE GHOSTS  |  F5: SKIP LEVEL")


class GameView:
    """The view of a game in progress: splits the screen into HUD and maze."""

    def __init__(self, canvas: Canvas) -> None:
        """Initialize the game view.

        Args:
            canvas: The canvas every element of the view is drawn on.
        """
        self.canvas: Canvas = canvas

    # -----------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------

    @staticmethod
    def _find_grid(maze: Any) -> list[list[int]] | None:
        """Look up the grid matrix of a maze under its possible names.

        Args:
            maze: The maze model of the current level.

        Returns:
            The grid matrix, or ``None`` if the maze exposes none.
        """
        for attr_name in GRID_ATTRIBUTES:
            if hasattr(maze, attr_name):
                grid: list[list[int]] = getattr(maze, attr_name)
                return grid
        return None

    @staticmethod
    def _best_score(app: App) -> int:
        """Read the best score from the high score list.

        Args:
            app: The application holding the ``highscores`` list.

        Returns:
            The score of the first entry, or 0 if there is none.
        """
        scores = getattr(app, "highscores", None)
        if not scores:
            return 0
        first_entry = scores[0]
        if hasattr(first_entry, "score"):
            return int(first_entry.score)
        if isinstance(first_entry, dict) and "score" in first_entry:
            return int(first_entry["score"])
        return 0

    @staticmethod
    def _is_cheat_mode(app: App, state: Any) -> bool:
        """Tell whether the cheat mode is active.

        Args:
            app: The application, which may carry a ``cheat_mode`` flag.
            state: The game state, which may carry a ``cheats`` object.

        Returns:
            True if the cheats were enabled by either of them.
        """
        if getattr(app, "cheat_mode", False):
            return True
        cheats = getattr(state, "cheats", None)
        return cheats is not None and bool(cheats.enabled)

    # -----------------------------------------------------------------
    # Drawing
    # -----------------------------------------------------------------

    def _draw_stat(self, label: str, value: str, center_x: int) -> None:
        """Draw a ``LABEL: value`` pair centred on a HUD column.

        Args:
            label: The label text, including its trailing ``": "``.
            value: The value shown right after the label.
            center_x: Horizontal centre of the whole pair.
        """
        label_width = len(label) * LABEL_CHAR_WIDTH
        total_width = label_width + len(value) * VALUE_CHAR_WIDTH
        start_x = center_x - total_width // 2

        self.canvas.text(label, start_x, HUD_LABEL_Y, LIGHT_BLUE, 20)
        self.canvas.text(value, start_x + label_width, HUD_VALUE_Y,
                         WHITE, 16)

    def _draw_hud(self, app: App, state: Any) -> None:
        """Draw the top bar: score, time, level and high score.

        Args:
            app: The application, source of the high scores.
            state: The game state, source of score, time and level.
        """
        self._draw_stat("SCORE: ", str(getattr(state.player, "score", 0)),
                        SCORE_CENTER_X)

        # Live countdown coming from the backend.
        minutes, seconds = divmod(int(getattr(state, "time_left", 0)), 60)
        self._draw_stat("TIME: ", f"{minutes:02d}:{seconds:02d}",
                        TIME_CENTER_X)

        self._draw_stat("LEVEL: ", str(state.level_number), LEVEL_CENTER_X)
        self._draw_stat("HIGH SCORE: ", str(self._best_score(app)),
                        HIGH_SCORE_CENTER_X)

        if self._is_cheat_mode(app, state):
            self.canvas.text(CHEAT_HINT, self.canvas.width // 2, 70,
                             NEON_YELLOW, 14, "center")

    def _draw_lives(self, lives: int, offset_x: int) -> None:
        """Draw the bottom row of lives, one Pac-Man sprite per life.

        Args:
            lives: Number of lives left.
            offset_x: Left edge of the maze, where the row starts.
        """
        base_y = self.canvas.height
        self.canvas.text("LIVES: ", offset_x, base_y - 62, WHITE, 16)

        renderer = getattr(self.canvas, "game_renderer", None)
        target = getattr(self.canvas, "_target", None)
        if renderer is None or target is None:
            return

        life_sprite = renderer.get_pacman_tile(2, 0)
        for i in range(lives):
            target.blit(life_sprite, (offset_x + 95 + i * 38, base_y - 68))

    def _draw_pause(self) -> None:
        """Draw the dimmed overlay and the pause menu image."""
        canvas_w = self.canvas.width
        canvas_h = self.canvas.height

        self.canvas.dim((16, 16, 28, 180))
        pause_img = self.canvas.pause_img
        if pause_img is not None:
            menu_x = (canvas_w - pause_img.get_width()) // 2
            menu_y = (canvas_h - pause_img.get_height()) // 2
            self.canvas.draw_image(pause_img, menu_x, menu_y)
        else:
            # Fallback if pause.png is missing.
            self.canvas.text("PAUSED", canvas_w // 2, canvas_h // 2 - 40,
                             NEON_YELLOW, 22, "center")
            self.canvas.text("[P]/[ESC] resume  |  [M] main menu",
                             canvas_w // 2, canvas_h // 2 + 10,
                             TEXT_WHITE, 14, "center")

    def draw(self, app: App, now: int) -> None:
        """Draw the game view: maze, entities, HUD and pause menu.

        Args:
            app: The application holding the running game engine.
            now: Current time in milliseconds.
        """
        if app.engine is None:
            return

        self.canvas.clear(DARK_BLUE)

        state = app.engine.state
        grid = self._find_grid(state.level.maze)
        if grid is None:
            return

        offset_x, _, _ = self.canvas.draw_game_field(
            110, 65, grid,
            state.level.pacgums, state.level.super_pacgums,
            state.player, state.ghosts)

        self._draw_hud(app, state)
        self._draw_lives(state.player.lives, offset_x)

        if state.status == GameStatus.PAUSED:
            self._draw_pause()
