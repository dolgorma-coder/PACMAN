"""Menu-like screens: main menu, highscores, instructions and game end.

The end-of-game screen includes the name prompt. This module contains no
graphical library imports and relies only on Canvas.
"""

from __future__ import annotations

from src.app import App
from src.models.app_models import INSTRUCTION_LINES, MenuItem
from src.models.highscore_models import HighscoreEntry
from src.UI.ui_canvas import Canvas
from src.UI.ui_theme import (DARK_BLUE, GRAY, LIGHT_BLUE,
                             NEON_ORANGE, NEON_YELLOW, RED,
                             TEXT_WHITE, WHITE, YELLOW)

MENU_TOP: int = 230
MENU_SPACING: int = 56
MESSAGE_MAX_CHARS: int = 90

# Size of the menu buttons and of the name input field, in pixels.
BUTTON_WIDTH: int = 320
BUTTON_HEIGHT: int = 42
BUTTON_SPACING: int = 12
INPUT_WIDTH: int = 320
INPUT_HEIGHT: int = 42

# Y position of each frame in the shared ui_sprites sheet.
SPRITE_Y_BUTTON: int = 0
SPRITE_Y_BUTTON_SELECTED: int = 62
SPRITE_Y_INPUT: int = 124

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
    """Draw an optional error message and a key hint at the bottom.

    Args:
        canvas: The canvas to draw on.
        hint: Key hint shown on the last line.
        message: Optional error message shown above the hint.
    """
    center = canvas.width // 2
    if message:
        canvas.text(message[:MESSAGE_MAX_CHARS], center,
                    canvas.height - 72, RED, 14, "center")
    canvas.text(hint, center, canvas.height - 36, GRAY, 14, "center")


def _draw_scores(canvas: Canvas, entries: list[HighscoreEntry], top: int,
                 limit: int, spacing: int, size: int) -> None:
    """Draw a highscore table: rank, name and score in three columns.

    Args:
        canvas: The canvas to draw on.
        entries: Highscore entries, best first.
        top: Y position of the first row.
        limit: Maximum number of rows to draw.
        spacing: Vertical distance between two rows.
        size: Font size of the table.
    """
    center = canvas.width // 2
    if not entries:
        canvas.text("No scores yet", center, top, GRAY, size, "center")
        return
    for rank, entry in enumerate(entries[:limit], start=1):
        y = top + (rank - 1) * spacing
        canvas.text(f"{rank}.", center - 170, y, TEXT_WHITE, size)
        canvas.text(entry.name, center - 130, y, TEXT_WHITE, size)
        canvas.text(str(entry.score), center + 160, y, YELLOW, size, "right")


def _draw_title(canvas: Canvas, center: int) -> int:
    """Draw the game logo, or a text title if the image is missing.

    Args:
        canvas: The canvas to draw on.
        center: Horizontal centre of the screen.

    Returns:
        The Y position where the next element should start.
    """
    logo_y = 60
    logo = canvas.menu_logo_img
    if logo:
        logo_x = center - int(logo.get_width()) // 2
        canvas.draw_image(logo, logo_x, logo_y)
        return logo_y + int(logo.get_height()) + 18

    canvas.text("PAC-MAN", center, logo_y, YELLOW, 42, "center")
    return logo_y + 60


def _draw_menu_buttons(canvas: Canvas, center: int, top: int,
                       selected_index: int) -> None:
    """Draw the menu buttons, highlighting the selected one.

    Args:
        canvas: The canvas to draw on.
        center: Horizontal centre of the screen.
        top: Y position of the first button.
        selected_index: Index of the highlighted menu item.
    """
    btn_x = center - BUTTON_WIDTH // 2

    for index, item in enumerate(MenuItem):
        btn_y = top + index * (BUTTON_HEIGHT + BUTTON_SPACING)
        selected = index == selected_index
        text_color = NEON_ORANGE if selected else TEXT_WHITE

        # Frame cut from the shared ui_sprites sheet.
        sprite_y = SPRITE_Y_BUTTON_SELECTED if selected else SPRITE_Y_BUTTON
        btn_frame = canvas.get_ui_sprite(0, sprite_y,
                                         BUTTON_WIDTH, BUTTON_HEIGHT)
        if btn_frame:
            canvas.draw_image(btn_frame, btn_x, btn_y)
        else:
            canvas.outline_rect(btn_x, btn_y, BUTTON_WIDTH, BUTTON_HEIGHT,
                                text_color)

        # Button label, centred on the frame.
        btn_label = item.value.replace("_", " ").upper()
        canvas.text(btn_label, center, btn_y + 13, text_color, 16, "center")


def draw_menu(canvas: Canvas, app: App) -> None:
    """Draw the main menu: background, logo, buttons and top scores.

    Args:
        canvas: The canvas to draw on.
        app: The application, source of the selection, scores and message.
    """
    center = canvas.width // 2

    canvas.draw_image(canvas.menu_bg, 0, 0)

    ready_y = _draw_title(canvas, center)
    canvas.text("READY!", center, ready_y, NEON_YELLOW, 24, "center")

    _draw_menu_buttons(canvas, center, ready_y + 60, app.menu_index)

    # Highscore table at the bottom: 10 rows, 20 px apart.
    canvas.text("TOP SCORES", center, 450, LIGHT_BLUE, 16, "center")
    _draw_scores(canvas, app.highscores, 480, 10, 20, 12)

    _draw_footer(canvas, "Up / Down: select    Enter: confirm", app.message)


def draw_highscores(canvas: Canvas, app: App) -> None:
    """Draw the highscores screen with a title and a table of scores.

    Args:
        canvas: The canvas to draw on.
        app: The application, source of the highscores.
    """
    canvas.clear(DARK_BLUE)
    canvas.text("HIGHSCORES", canvas.width // 2, 50,
                NEON_YELLOW, 24, "center")

    # 10 rows, 36 px apart.
    _draw_scores(canvas, app.highscores, 160, 10, 36, 16)
    _draw_footer(canvas, "Enter or Esc: back")


def draw_instructions(canvas: Canvas) -> None:
    """Draw the controls, rules and cheat keys with aligned X offsets.

    Args:
        canvas: The canvas to draw on.
    """
    canvas.clear(DARK_BLUE)
    canvas.text(
        "INSTRUCTIONS", canvas.width // 2, 36, NEON_YELLOW, 24, "center")

    # Left margin wide enough for the long cheat lines to fit.
    left_margin = 40
    for index, line in enumerate((*INSTRUCTION_LINES, *CHEAT_LINES)):
        is_heading = bool(line) and not line.startswith(" ")
        font_size = 14 if is_heading else 12
        canvas.text(line, left_margin, 95 + index * 24,
                    LIGHT_BLUE if is_heading else WHITE, font_size)

    _draw_footer(canvas, "Enter or Esc: back")


def _draw_name_input(canvas: Canvas, center: int, top: int,
                     text: str) -> None:
    """Draw the name input field with the typed text on top of it.

    Args:
        canvas: The canvas to draw on.
        center: Horizontal centre of the screen.
        top: Y position of the field.
        text: Text to show inside the field (including the cursor).
    """
    input_x = center - INPUT_WIDTH // 2

    # Blue plate cut from the shared ui_sprites sheet.
    input_frame = canvas.get_ui_sprite(0, SPRITE_Y_INPUT,
                                       INPUT_WIDTH, INPUT_HEIGHT)
    if input_frame:
        canvas.draw_image(input_frame, input_x, top)
    else:
        canvas.fill_rect(input_x, top, INPUT_WIDTH, INPUT_HEIGHT,
                         (20, 60, 220))
        canvas.outline_rect(input_x, top, INPUT_WIDTH, INPUT_HEIGHT,
                            WHITE, thickness=1)

    canvas.text(text, center, top + 13, WHITE, 16, "center")


def draw_game_end(canvas: Canvas, app: App, now_ms: int) -> None:
    """Draw the end-of-game screen with a name input and the final score.

    Args:
        canvas: The canvas to draw on.
        app: The application, source of the result, name and message.
        now_ms: Current time in milliseconds, used to blink the cursor.
    """
    center = canvas.width // 2
    canvas.clear(DARK_BLUE)

    start_y = 130

    # Headline.
    if app.won:
        canvas.text(
            "Congratulations!", center, start_y, NEON_YELLOW, 24, "center")
        canvas.text(
            "You won!", center, start_y + 35, NEON_YELLOW, 24, "center")
    else:
        canvas.text(
            "GAME OVER", center, start_y + 15, NEON_YELLOW, 24, "center")

    # Final score on a single horizontal line.
    score_y = start_y + 100
    canvas.text("SCORE: ", center - 50, score_y, WHITE, 16)
    canvas.text(str(app.final_score), center + 70, score_y, WHITE, 16)

    # Name prompt with a blinking cursor.
    input_label_y = score_y + 60
    canvas.text("Enter your name:", center, input_label_y,
                WHITE, 16, "center")

    input_y = input_label_y + 40
    cursor = "_" if (now_ms // 500) % 2 == 0 else " "
    _draw_name_input(canvas, center, input_y, app.name_buffer + cursor)

    hint_text = "(max 10 characters, alphanumeric and spaces only)"
    canvas.text(hint_text, center, input_y + INPUT_HEIGHT + 15,
                GRAY, 12, "center")

    # Footer.
    if app.message:
        canvas.text(
            app.message[:MESSAGE_MAX_CHARS],
            center, canvas.height - 80, RED, 14, "center")

    canvas.text(
        "Enter: save and go back to the menu",
        center, canvas.height - 36, GRAY, 14, "center")
