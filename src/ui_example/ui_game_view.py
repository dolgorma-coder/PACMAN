"""Game view: draws the maze, items, entities, HUD, pause menu and charts.
This module uses only basic primitives and contains no graphical library imports.
"""

from __future__ import annotations

from src.app import App
from src.models.game_state import GameStatus
from src.renderer import GameRenderer
from src.ui_example.ui_canvas import Canvas
from src.ui_example.ui_theme import (DARK_BLUE, WHITE, NEON_YELLOW, GRAY, 
                                     NEON_ORANGE, GRAY_BORDER, TEXT_WHITE, 
                                     LIGHT_BLUE)


class GameView:
    """The view of a game in progress: splits the screen into HUD and maze."""

    def __init__(self, canvas: Canvas) -> None:
        """Инициализируем неоновый графический движок, сохраняя холст для HUD."""
        self.canvas = canvas
        
        # Безопасно вытаскиваем экран Pygame из буферов canvas
        pygame_screen = getattr(canvas, '_target', None)
        if pygame_screen is None:
            pygame_screen = getattr(canvas, '_screen', pygame.display.get_surface())

        # Передаем экран в твой кастомный рендерер лабиринта
        self.game_renderer = GameRenderer(pygame_screen, tile_size=32)

    def draw(self, app: App, now: int) -> None:
        """Рендерит игру, используя исключительно независимые примитивы Canvas и Renderer."""
        if app.engine is None:
            return

        # 1. ЗАДНИЙ ФОН: Полностью очищаем виртуальный холст тёмно-синим цветом темы
        self.canvas.clear(DARK_BLUE)

        state_obj = app.engine.state
        maze_obj = state_obj.level.maze
        
        # Безопасный перебор возможных имен буфера матрицы Джамаля
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

        # =====================================================================
        # 👑 МАТЕМАТИЧЕСКИЙ АВТОЛЕЙАУТ ВЕРХНЕЙ ПАНЕЛЕЙ HUD (Ширина окна 1280px)
        # =====================================================================
        col1_center = 160   # Зона SCORE 
        col2_center = 480   # Зона TIME  
        col3_center = 800   # Зона LEVEL 
        col4_center = 1120  # Зона HIGH SCORE 

        text_y = 25
        digits_y = 34

        # --- 1. АВТОЛЕЙАУТ ДЛЯ SCORE ---
        player_model = state_obj.player
        current_score = getattr(player_model, 'score', 0)
        score_str = str(current_score)
        total_score_w = (7 * 16) + (len(score_str) * 20)  # Буквы 16px, цифры 20px (DotGothic)
        start_score_x = col1_center - total_score_w // 2
        
        self.canvas.text("SCORE: ", start_score_x, text_y, LIGHT_BLUE, 20)
        self.canvas.text(score_str, start_score_x + (7 * 16), digits_y, WHITE, 16)

        # --- 2. АВТОЛЕЙАУТ ДЛЯ TIME (Живой таймер из бэкенда Джамаля) ---
        time_left_secs = int(getattr(state_obj, 'time_left', 0))
        minutes = time_left_secs // 60
        seconds = time_left_secs % 60
        time_digits = f"{minutes:02d}:{seconds:02d}"
        
        total_time_w = (6 * 16) + (5 * 20)  
        start_time_x = col2_center - total_time_w // 2
        
        self.canvas.text("TIME: ", start_time_x, text_y, LIGHT_BLUE, 20)
        self.canvas.text(time_digits, start_time_x + (6 * 16), digits_y, WHITE, 16)

        # --- 3. АВТОЛЕЙАУТ ДЛЯ LEVEL ---
        level_str = str(state_obj.level_number)
        total_level_w = (7 * 16) + (len(level_str) * 20)  
        start_level_x = col3_center - total_level_w // 2
        
        self.canvas.text("LEVEL: ", start_level_x, text_y, LIGHT_BLUE, 20)
        self.canvas.text(level_str, start_level_x + (7 * 16), digits_y, WHITE, 16)

        # --- 4. АВТОЛЕЙАУТ ДЛЯ HIGH SCORE (Считываем из списка) ---
        high_score = 0
        if hasattr(app, 'highscores') and app.highscores and len(app.highscores) > 0:
            first_entry = app.highscores[0]
            if hasattr(first_entry, 'score'):
                high_score = first_entry.score
            elif isinstance(first_entry, dict) and 'score' in first_entry:
                high_score = first_entry['score']
                
        hs_str = str(high_score)
        total_hs_w = (12 * 16) + (len(hs_str) * 20)  
        start_hs_x = col4_center - total_hs_w // 2
        
        self.canvas.text("HIGH SCORE: ", start_hs_x, text_y, LIGHT_BLUE, 20)
        self.canvas.text(hs_str, start_hs_x + (12 * 16), digits_y, WHITE, 16)

        # --- 5. СТРОКА ПОДСКАЗОК ЧИТ-РЕЖИМА ---
        if getattr(app, 'cheat_mode', False) or (hasattr(state_obj, 'cheats') and state_obj.cheats.enabled):
            cheat_hint = "CHEAT MODE ACTIVE:  F2: INVINCIBLE  |  F3: FREEZE GHOSTS  |  F5: SKIP LEVEL"
            self.canvas.text(cheat_hint, canvas_w // 2, 70, NEON_YELLOW, 14, "center")

        # =====================================================================
        # ❤️ ДИНАМИЧЕСКАЯ НИЖНЯЯ ПАНЕЛЬ ЖИЗНЕЙ (Strictly using get_pacman_tile)
        # =====================================================================
        lives_y = offset_y + final_maze_w + 20
        self.canvas.text("LIVES: ", offset_x, lives_y, WHITE, 16)
        
        for i in range(player_model.lives):
            life_x = offset_x + 95 + (i * 38)
            # ИСПРАВЛЕНО: Забираем Пакмана строго через твой унифицированный get_pacman_tile(2, 0)!
            if hasattr(self.canvas, 'game_renderer'):
                life_sprite = self.canvas.game_renderer.get_pacman_tile(2, 0)
                self.canvas._target.blit(life_sprite, (life_x, lives_y - 6))


        # =====================================================================
        # 👑 БЛОК ПАУЗЫ (Полностью на твоем PNG-спрайте 520х280 из Figma)
        # =====================================================================
        if state_obj.status == GameStatus.PAUSED:
            # Накладываем матовую темно-синюю вуаль на задний план игры
            self.canvas.fill_rect(0, 0, canvas_w, canvas_h, (16, 16, 28, 180))
            
            # Всплывающее окошко паузы строго по размерам твоего спрайта!
            menu_w, menu_h = 520, 280
            menu_x = canvas_w // 2 - menu_w // 2
            menu_y = canvas_h // 2 - menu_h // 2
            
            # Блиттим твою шикарную пиксельную графику окна вместо системных рамок Pygame
            if hasattr(self.canvas, 'dialog_img') and self.canvas.dialog_img:
                self.canvas.draw_image(self.canvas.dialog_img, menu_x, menu_y)
            else:
                # Безопасная подстраховка на случай, если файл dialog.png случайно удалят
                self.canvas.fill_rect(menu_x, menu_y, menu_w, menu_h, DARK_BLUE)
                self.canvas.outline_rect(menu_x, menu_y, menu_w, menu_h, NEON_ORANGE, thickness=2)
            
            # ТЕКСТ ПАУЗЫ (Идеально ложится поверх твоей картинки из Figma)
            self.canvas.text("GAME PAUSED", canvas_w // 2, menu_y + 80, NEON_YELLOW, 22, "center")
            self.canvas.text("Press P or ESC to Resume", canvas_w // 2, menu_y + 160, TEXT_WHITE, 14, "center")
