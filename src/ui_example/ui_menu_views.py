"""Drawing of the menu-like screens: main menu, highscores, instructions
and the end-of-game screen with the name prompt.
This module contains no graphical library imports and relies only on Canvas.
"""

from __future__ import annotations

from src.app import App
from src.models.app_models import INSTRUCTION_LINES, MenuItem
from src.models.highscore_models import HighscoreEntry
from src.ui_example.ui_canvas import Canvas
from src.ui_example.ui_theme import (GRAY, RED,
                                     WHITE, YELLOW, NEON_ORANGE, NEON_YELLOW,
                                     DARK_BLUE, TEXT_WHITE, LIGHT_BLUE)

MENU_TOP = 230
MENU_SPACING = 56
MESSAGE_MAX_CHARS = 90

CHEAT_LINES: tuple[str, ...] = (
    "",
    "Cheat mode (for reviewers)",
    "  F1 or 1: cheat mode on / off",
    "  F2 or 2: invincible          F3 or 3: freeze ghosts",
    "  F4 or 4: fast player         F5 or 5: skip level",
    "  F6 or 6: extra life",
    "  (F2 to F6 only work while the cheat mode is on)",
)


def _draw_footer(canvas: Canvas, hint: str, message: str = "") -> None:
    """Draw an optional error message and a key hint at the bottom."""
    center = canvas.width // 2
    if message:
        canvas.text(message[:MESSAGE_MAX_CHARS], center,
                    canvas.height - 72, RED, 14, "center")
    canvas.text(hint, center, canvas.height - 36, GRAY, 14, "center")


def _draw_scores(canvas: Canvas, entries: list[HighscoreEntry], top: int,
                 limit: int, spacing: int, size: int) -> None:
    """Draw a highscore table: rank, name and score in three columns."""
    center = canvas.width // 2
    if not entries:
        canvas.text("No scores yet", center, top, GRAY, size, "center")
        return
    for rank, entry in enumerate(entries[:limit], start=1):
        y = top + (rank - 1) * spacing
        canvas.text(f"{rank}.", center - 170, y, TEXT_WHITE, size)
        canvas.text(entry.name, center - 130, y, TEXT_WHITE, size)
        canvas.text(str(entry.score), center + 160, y, YELLOW, size, "right")


def draw_menu(canvas: Canvas, app: App) -> None:
    """Draw the main menu with a background, logo, ready text,"""
    center = canvas.width // 2

    canvas.draw_image(canvas.menu_bg, 0, 0)

    # 2. РЕНДЕРИНГ ГРАФИЧЕСКОГО ЛОГОТИПА ИЗ FIGMA
    logo_y = 60
    if canvas.menu_logo_img:
        logo_x = center - canvas.menu_logo_img.get_width() // 2
        canvas.draw_image(canvas.menu_logo_img, logo_x, logo_y)
        ready_y = logo_y + canvas.menu_logo_img.get_height() + 18
    else:
        canvas.text("PAC-MAN", center, logo_y, YELLOW, 42, "center")
        ready_y = logo_y + 60

    # 3. НАДПИСЬ "READY!"
    canvas.text("READY!", center, ready_y, NEON_YELLOW, 24, "center")

    # 4. ПРОГРАММНЫЕ ИНТЕРАКТИВНЫЕ КНОПКИ (Нарезка из общего ui_sprites.png)
    start_buttons_y = ready_y + 60
    button_width, button_height = 320, 42  # Твои точные размеры кнопки
    button_spacing = 12

    for index, item in enumerate(MenuItem):
        btn_x = center - button_width // 2
        btn_y = start_buttons_y + index * (button_height + button_spacing)

        selected = index == app.menu_index
        text_color = NEON_ORANGE if selected else TEXT_WHITE

        # НАСТРОЙКА КООРДИНАТ ИЗ FIGMA:
        if selected:
            # Например, активная кнопка лежит на Y = 42
            btn_frame = canvas.get_ui_sprite(
                0, 62, button_width, button_height)
        else:
            # Обычная кнопка лежит в самом верху на Y = 0
            btn_frame = canvas.get_ui_sprite(
                0, 0, button_width, button_height)

        # Выводим вырезанную рамку на экран
        if btn_frame:
            canvas.draw_image(btn_frame, btn_x, btn_y)
        else:
            canvas.outline_rect(
                btn_x, btn_y, button_width, button_height, border_color)
        # Накладываем текст кнопки по центру
        btn_label = item.value.replace("_", " ").upper()
        canvas.text(btn_label, center, btn_y + 13, text_color, 16, "center")

    # 5. ТАБЛИЦА РЕКОРДОВ В НИЖНЕЙ ЧАСТИ МЕНЮ (Лимит 10 строк, зазор 26)
    canvas.text("TOP SCORES", center, 450, LIGHT_BLUE, 16, "center")
    _draw_scores(canvas, app.highscores, 480, 10, 20, 12)

    # 6. ФУТЕР
    _draw_footer(canvas, "Up / Down: select    Enter: confirm", app.message)


def draw_highscores(canvas: Canvas, app: App) -> None:
    """Draw the highscores screen with a title and a table of scores."""
    canvas.clear(DARK_BLUE)
    canvas.text("HIGHSCORES", canvas.width // 2, 50, NEON_YELLOW, 24, "center")

    # Исправлено: лимит 10 строк, вертикальный зазор 36 пикселей для
    _draw_scores(canvas, app.highscores, 160, 10, 36, 16)
    _draw_footer(canvas, "Enter or Esc: back")


def draw_instructions(canvas: Canvas) -> None:
    """Controls, rules and cheat keys с выровненными отступами X."""
    canvas.clear(DARK_BLUE)
    canvas.text(
        "INSTRUCTIONS", canvas.width // 2, 36, NEON_YELLOW, 24, "center")

    # Смещаем левое поле, чтобы широкие пиксельные строчки читов поместились
    left_margin = 40
    for index, line in enumerate(INSTRUCTION_LINES + CHEAT_LINES):
        is_heading = bool(line) and not line.startswith(" ")
        font_size = 14 if is_heading else 12
        canvas.text(line, left_margin, 95 + index * 24,
                    LIGHT_BLUE if is_heading else WHITE, font_size)

    _draw_footer(canvas, "Enter or Esc: back")


def draw_game_end(canvas: Canvas, app: App, now_ms: int) -> None:
    """Draw the end-of-game screen with a name
    input field and a final score."""
    center = canvas.width // 2
    canvas.clear(DARK_BLUE)

    start_y = 130

    # 1. ЗАГЛОВКИ И ПОЗДРАВЛЕНИЯ С ТВОЕГО МАКЕТА
    if app.won:
        canvas.text(
            "Congratulations!", center, start_y, NEON_YELLOW, 24, "center")
        canvas.text(
            "You won!", center, start_y + 35, NEON_YELLOW, 24, "center")
    else:
        canvas.text(
            "GAME OVER", center, start_y + 15, NEON_YELLOW, 24, "center")

    # 2. ФИНАЛЬНЫЙ СЧЕТ (SCORE: XXX) НА ОДНОЙ ГОРИЗОНТАЛЬНОЙ ЛИНИИ
    score_y = start_y + 100
    canvas.text("SCORE: ", center - 50, score_y, WHITE, 16)
    canvas.text(str(app.final_score), center + 70, score_y + 0, WHITE, 16)

    # 3. ПОЛЕ ВВОДА ИМЕНИ ИГРОКА (W=260, H=42, нарезка из общего ui_sprites
    input_label_y = score_y + 60
    canvas.text("Enter your name:", center, input_label_y, WHITE, 16, "center")

    input_w, input_h = 320, 42
    input_x = center - input_w // 2
    input_y = input_label_y + 40

    # НАСТРОЙКА КООРДИНАТ ИЗ FIGMA:
    # Укажи точную высоту Y, где на твоем листе нарисована синяя плашка
    input_frame = canvas.get_ui_sprite(0, 124, input_w, input_h)

    if input_frame:
        canvas.draw_image(input_frame, input_x, input_y)
    else:
        canvas.fill_rect(input_x, input_y, input_w, input_h, (20, 60, 220))
        canvas.outline_rect(
            input_x, input_y, input_w, input_h, WHITE, thickness=1)

    # Имя поверх плашки
    cursor = "_" if (now_ms // 500) % 2 == 0 else " "
    player_name = app.name_buffer + cursor
    canvas.text(player_name, center, input_y + 13, WHITE, 16, "center")

    # 4. ЛАКОНИЧНАЯ ПОДПИСЬ ИЗ ТВОЕГО ДИЗАЙНА
    hint_text = "(max 10 characters, alphanumeric and spaces only)"
    canvas.text(hint_text, center, input_y + input_h + 15, GRAY, 12, "center")

    # 5. НИЖНИЙ ФУТЕР
    if app.message:
        canvas.text(
            app.message[:MESSAGE_MAX_CHARS],
            center, canvas.height - 80, RED, 14, "center")

    canvas.text(
        "Enter: save and go back to the menu",
        center, canvas.height - 36, GRAY, 14, "center")
