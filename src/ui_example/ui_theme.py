"""Colors and sizes used by the interface."""

from __future__ import annotations

Color = tuple[int, int, int]

WINDOW_WIDTH = 960
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Pac-Man"
FPS = 60

HUD_HEIGHT = 56            # Top bar: score, lives, level, time.
FOOTER_HEIGHT = 30         # Bottom bar: pause and cheat hints.
MIN_CELL_SIZE = 4          # Pixels per maze cell, smallest and biggest.
MAX_CELL_SIZE = 48
END_SCREEN_LOCK_MS = 600   # Input ignored right after a game ends, so keys
#                            used to play do not end up in the name.

BLACK: Color = (0, 0, 0)
WHITE: Color = (255, 255, 255)
GRAY: Color = (150, 150, 150)
YELLOW: Color = (255, 221, 0)
GOLD: Color = (255, 190, 40)
RED: Color = (235, 60, 60)
GREEN: Color = (80, 220, 100)
WALL_BLUE: Color = (50, 80, 255)
SOLID_CELL: Color = (20, 30, 90)
PELLET: Color = (255, 205, 160)
HIGHLIGHT: Color = (30, 40, 110)
PANEL: Color = (15, 15, 45)
SCARED_BLUE: Color = (60, 90, 255)

GHOST_COLORS: dict[str, Color] = {
    "blinky": (240, 50, 50),
    "pinky": (255, 150, 200),
    "inky": (60, 220, 230),
    "clyde": (255, 160, 40),
}
