"""Game view: draws the maze, items, entities, HUD, pause menu and charts.
This module uses only basic primitives
and contains no graphical library imports.
"""

from __future__ import annotations

import pygame

from src.app import App
from src.models.game_state import GameStatus
from src.ui_example.ui_canvas import Canvas
from src.ui_example.ui_theme import (DARK_BLUE, WHITE, NEON_YELLOW,
                                     TEXT_WHITE,
                                     LIGHT_BLUE)


class GameView:
    """The view of a game in progress: splits the screen into HUD and maze."""

    def __init__(self, canvas: Canvas) -> None:
        """Initialize the game view with a canvas and a game renderer."""
        self.canvas = canvas

        pygame_screen = getattr(canvas, '_target', None)
        if pygame_screen is None:
            pygame_screen = getattr(
                canvas, '_screen', pygame.display.get_surface())

    def draw(self, app: App, now: int) -> None:
        """Draw the game view, including maze,
        entities, HUD, and pause menu."""
        if app.engine is None:
            return

        self.canvas.clear(DARK_BLUE)

        state_obj = app.engine.state
        maze_obj = state_obj.level.maze

        grid_matrix = None
        for attr_name in ['grid', '_grid', 'matrix', 'map', 'board', 'cells']:
            if hasattr(maze_obj, attr_name):
                grid_matrix = getattr(maze_obj, attr_name)
                break
        else:
            return

        canvas_w = self.canvas.width
        canvas_h = self.canvas.height

        offset_x, offset_y, final_maze_w = self.canvas.draw_game_field(
            110, 65, grid_matrix,
            state_obj.level.pacgums, state_obj.level.super_pacgums,
            state_obj.player, state_obj.ghosts
        )

        col1_center = 160
        col2_center = 480
        col3_center = 800
        col4_center = 1120

        text_y = 25
        digits_y = 34

        player_model = state_obj.player
        current_score = getattr(player_model, 'score', 0)
        score_str = str(current_score)
        total_score_w = (7 * 16) + (len(score_str) * 20)
        start_score_x = col1_center - total_score_w // 2

        self.canvas.text("SCORE: ", start_score_x, text_y, LIGHT_BLUE, 20)
        self.canvas.text(
            score_str, start_score_x + (7 * 16), digits_y, WHITE, 16)

        # --- 2. АВТОЛЕЙАУТ ДЛЯ TIME (Живой таймер из бэкенда Джамаля) ---
        time_left_secs = int(getattr(state_obj, 'time_left', 0))
        minutes = time_left_secs // 60
        seconds = time_left_secs % 60
        time_digits = f"{minutes:02d}:{seconds:02d}"

        total_time_w = (6 * 16) + (5 * 20)
        start_time_x = col2_center - total_time_w // 2

        self.canvas.text("TIME: ", start_time_x, text_y, LIGHT_BLUE, 20)
        self.canvas.text(
            time_digits, start_time_x + (6 * 16), digits_y, WHITE, 16)

        # --- 3. АВТОЛЕЙАУТ ДЛЯ LEVEL ---
        level_str = str(state_obj.level_number)
        total_level_w = (7 * 16) + (len(level_str) * 20)
        start_level_x = col3_center - total_level_w // 2

        self.canvas.text("LEVEL: ", start_level_x, text_y, LIGHT_BLUE, 20)
        self.canvas.text(
            level_str, start_level_x + (7 * 16), digits_y, WHITE, 16)

        # --- 4. АВТОЛЕЙАУТ ДЛЯ HIGH SCORE (Считываем из списка) ---
        high_score: int = 0
        if hasattr(app,
                   'highscores') and app.highscores and len(app.highscores
                                                            ) > 0:
            first_entry = app.highscores[0]
            if hasattr(first_entry, 'score'):
                high_score = int(first_entry.score)
            elif isinstance(first_entry, dict) and 'score' in first_entry:
                high_score = first_entry['score']  # type: ignore

        hs_str = str(high_score)  # type: ignore
        total_hs_w = (12 * 16) + (len(hs_str) * 20)
        start_hs_x = col4_center - total_hs_w // 2

        self.canvas.text("HIGH SCORE: ", start_hs_x, text_y, LIGHT_BLUE, 20)
        self.canvas.text(hs_str, start_hs_x + (12 * 16), digits_y, WHITE, 16)

        # --- 5. СТРОКА ПОДСКАЗОК ЧИТ-РЕЖИМА ---
        if getattr(app,
                   'cheat_mode', False) or (hasattr(state_obj, 'cheats')
                                            and state_obj.cheats.enabled):
            cheat_hint = "CHEAT MODE ACTIVE:  F2: INVINCIBLE  |" \
                "F3: FREEZE GHOSTS  |  F5: SKIP LEVEL"
            self.canvas.text(
                cheat_hint, canvas_w // 2, 70, NEON_YELLOW, 14, "center")

        # =====================================================================
        # ❤️ ДИНАМИЧЕСКАЯ НИЖНЯЯ ПАНЕЛЬ ЖИЗНЕЙ (Strictly using get_pacman_tile)
        # =====================================================================
        lives_y = offset_y + final_maze_w + 20
        self.canvas.text("LIVES: ", offset_x, lives_y, WHITE, 16)

        for i in range(player_model.lives):
            life_x = offset_x + 95 + (i * 38)
            if hasattr(self.canvas, 'game_renderer'):
                life_sprite = self.canvas.game_renderer.get_pacman_tile(2, 0)
                self.canvas._target.blit(   # type: ignore
                    life_sprite, (life_x, lives_y - 6))

        # =====================================================================
        # 👑 БЛОК ПАУЗЫ (Полностью на твоем PNG-спрайте 520х280 из Figma)
        # =====================================================================
        if state_obj.status == GameStatus.PAUSED:
            self.canvas.dim((16, 16, 28, 180))
            pause_img = self.canvas.pause_img
            if pause_img is not None:
                menu_x = (canvas_w - pause_img.get_width()) // 2
                menu_y = (canvas_h - pause_img.get_height()) // 2
                self.canvas.draw_image(pause_img, menu_x, menu_y)
            else:
                # Fallback if pause.png is missing
                self.canvas.text("PAUSED", canvas_w // 2, canvas_h // 2 - 40,
                                 NEON_YELLOW, 22, "center")
                self.canvas.text("[P]/[ESC] resume  |  [M] main menu",
                                 canvas_w // 2, canvas_h // 2 + 10,
                                 TEXT_WHITE, 14, "center")
