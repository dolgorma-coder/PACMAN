"""Drawing of the menu-like screens: main menu, highscores, instructions
and the end-of-game screen with the name prompt.
"""

from __future__ import annotations

from src.app import App
from src.models.app_models import INSTRUCTION_LINES, MenuItem
from src.models.highscore_models import MAX_NAME_LENGTH, HighscoreEntry
from src.ui_example.ui_canvas import Canvas
from src.ui_example.ui_theme import (GOLD, GRAY, GREEN,
                                     HIGHLIGHT, RED, WHITE, YELLOW)

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
                    canvas.height - 72, RED, 24, "center")
    canvas.text(hint, center, canvas.height - 36, GRAY, 22, "center")


def _draw_scores(canvas: Canvas, entries: list[HighscoreEntry], top: int,
                 limit: int, spacing: int, size: int) -> None:
    """Draw a highscore table: rank, name and score in three columns."""
    center = canvas.width // 2
    if not entries:
        canvas.text("No scores yet", center, top, GRAY, size, "center")
        return
    for rank, entry in enumerate(entries[:limit], start=1):
        y = top + (rank - 1) * spacing
        canvas.text(f"{rank}.", center - 220, y, GRAY, size)
        canvas.text(entry.name, center - 150, y, WHITE, size)
        canvas.text(str(entry.score), center + 220, y, YELLOW, size, "right")


def draw_menu(canvas: Canvas, app: App) -> None:
    """Main menu, with the best scores below it."""
    center = canvas.width // 2
    canvas.text("PAC-MAN", center, 80, YELLOW, 120, "center")
    for index, item in enumerate(MenuItem):
        y = MENU_TOP + index * MENU_SPACING
        selected = index == app.menu_index
        if selected:
            canvas.fill_rect(center - 200, y - 8, 400, 46, HIGHLIGHT)
        canvas.text(item.value, center, y, YELLOW if selected else WHITE,
                    40, "center")
    canvas.text("TOP SCORES", center, 470, GRAY, 28, "center")
    _draw_scores(canvas, app.highscores, 505, 5, 30, 26)
    _draw_footer(canvas, "Up / Down: select    Enter: confirm", app.message)


def draw_highscores(canvas: Canvas, app: App) -> None:
    """The full top 10."""
    canvas.text("HIGHSCORES", canvas.width // 2, 50, YELLOW, 72, "center")
    _draw_scores(canvas, app.highscores, 150, 10, 46, 36)
    _draw_footer(canvas, "Enter or Esc: back")


def draw_instructions(canvas: Canvas) -> None:
    """Controls, rules and cheat keys."""
    canvas.text("INSTRUCTIONS", canvas.width // 2, 36, YELLOW, 64, "center")
    for index, line in enumerate(INSTRUCTION_LINES + CHEAT_LINES):
        is_heading = bool(line) and not line.startswith(" ")
        canvas.text(line, 110, 115 + index * 26,
                    YELLOW if is_heading else WHITE, 24)
    _draw_footer(canvas, "Enter or Esc: back")


def draw_game_end(canvas: Canvas, app: App, now_ms: int) -> None:
    """Game over / victory screen with the name prompt."""
    center = canvas.width // 2
    if app.won:
        canvas.text("VICTORY!", center, 100, GOLD, 120, "center")
        canvas.text("Congratulations, you completed all the levels!",
                    center, 220, WHITE, 34, "center")
    else:
        canvas.text("GAME OVER", center, 100, RED, 120, "center")
    canvas.text(f"Final score: {app.final_score}", center, 290, YELLOW, 54,
                "center")

    canvas.text("Enter your name:", center, 400, WHITE, 32, "center")
    canvas.fill_rect(center - 200, 445, 400, 56, HIGHLIGHT)
    canvas.outline_rect(center - 200, 445, 400, 56, YELLOW)
    cursor = "_" if (now_ms // 500) % 2 == 0 else " "
    canvas.text(app.name_buffer + cursor, center, 456, WHITE, 40, "center")
    canvas.text(f"{len(app.name_buffer)} / {MAX_NAME_LENGTH} characters",
                center, 510, GRAY, 22, "center")
    if app.message:
        canvas.text(app.message[:MESSAGE_MAX_CHARS], center, 560, RED, 24,
                    "center")
    canvas.text("Letters, digits and spaces only. Enter: save and go back "
                "to the menu.", center, canvas.height - 36, GREEN, 22,
                "center")
