"""Drawing layer: the only module that draws on the screen.

Everything else in the interface draws through `Canvas`, using a few
primitives that every simple graphics library (MLX included) has: a window,
filled rectangles and circles, lines, text, off-screen images and a frame
loop. To change the graphics library, only this module and `ui_input.py`
have to be rewritten.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Literal

import pygame  # type: ignore

from src.ui_example.ui_theme import WHITE, Color

Align = Literal["left", "center", "right"]

VSYNC_FPS_LIMIT = 240      # Safety limit if the display ignores the vsync.


class CanvasError(Exception):
    """Raised when the window cannot be opened."""


class Layer:
    """An off-screen picture that can be drawn many times (see `record`)."""

    def __init__(self, surface: pygame.Surface) -> None:
        """Wrap a surface."""
        self.surface = surface


def _open_window(width: int, height: int) -> pygame.Surface:
    """Open the window, synchronised with the screen refresh if possible.

    Synchronising with the screen (vsync) is what makes the movement look
    smooth: every frame is shown exactly once per screen refresh.
    """
    try:
        return pygame.display.set_mode((width, height), pygame.SCALED,
                                       vsync=1)
    except pygame.error:
        return pygame.display.set_mode((width, height))


class Canvas:
    """A window with simple drawing operations.

    Coordinates are pixels, (0, 0) is the top-left corner.
    """

    def __init__(self, width: int, height: int, title: str) -> None:
        """Open the window.

        Raises:
            CanvasError: If the window cannot be opened (for example when
                there is no display).
        """
        try:
            pygame.display.init()
            pygame.font.init()
            self._screen = _open_window(width, height)
        except pygame.error as error:
            raise CanvasError(f"Cannot open the window: {error}") from error
        pygame.display.set_caption(title)
        self.width = width
        self.height = height
        self._target = self._screen          # Where the drawing goes.
        self._clock = pygame.time.Clock()
        self._last_frame = time.perf_counter()
        self._vsync = False
        # self._vsync = bool(pygame.display.is_vsync())
        self._fonts: dict[int, pygame.font.Font] = {}

    # -----------------------------------------------------------------
    # Drawing
    # -----------------------------------------------------------------

    def clear(self, color: Color) -> None:
        """Fill the whole target with one color."""
        self._target.fill(color)

    def fill_rect(self, x: int, y: int, width: int, height: int,
                  color: Color) -> None:
        """Draw a filled rectangle."""
        pygame.draw.rect(self._target, color, (x, y, width, height))

    def outline_rect(self, x: int, y: int, width: int, height: int,
                     color: Color, thickness: int = 2) -> None:
        """Draw the border of a rectangle."""
        pygame.draw.rect(self._target, color, (x, y, width, height),
                         thickness)

    def fill_circle(self, x: int, y: int, radius: int, color: Color) -> None:
        """Draw a filled circle centered on (x, y)."""
        pygame.draw.circle(self._target, color, (x, y), max(1, radius))

    def outline_circle(self, x: int, y: int, radius: int, color: Color,
                       thickness: int = 2) -> None:
        """Draw the border of a circle centered on (x, y)."""
        pygame.draw.circle(self._target, color, (x, y), max(1, radius),
                           thickness)

    def line(self, x1: int, y1: int, x2: int, y2: int, color: Color,
             thickness: int = 1) -> None:
        """Draw a straight line."""
        pygame.draw.line(self._target, color, (x1, y1), (x2, y2), thickness)

    def text(self, message: str, x: int, y: int, color: Color = WHITE,
             size: int = 28, align: Align = "left") -> None:
        """Draw one line of text. (x, y) is its top-left, top-center or
        top-right corner, depending on `align`.

        Text that cannot be drawn is skipped: a drawing problem must never
        stop the game.
        """
        clean = message.replace("\n", " ").replace("\0", "")
        try:
            picture = self._font(size).render(clean, True, color)
        except (pygame.error, ValueError):
            return
        if align == "center":
            x -= picture.get_width() // 2
        elif align == "right":
            x -= picture.get_width()
        self._target.blit(picture, (x, y))

    # -----------------------------------------------------------------
    # Off-screen images (for things that do not change every frame)
    # -----------------------------------------------------------------

    def record(self, draw: Callable[[], None]) -> Layer:
        """Run `draw` on a new black off-screen image and return it."""
        surface = pygame.Surface((self.width, self.height))
        previous, self._target = self._target, surface
        try:
            draw()
        finally:
            self._target = previous
        return Layer(surface)

    def draw_layer(self, layer: Layer) -> None:
        """Draw a recorded image over the whole target."""
        self._target.blit(layer.surface, (0, 0))

    # -----------------------------------------------------------------
    # Frame loop
    # -----------------------------------------------------------------

    def present(self) -> None:
        """Show what was drawn in this frame."""
        pygame.display.flip()

    def tick(self, fps: int) -> float:
        """Wait for the next frame and return the seconds since the last.

        The time is measured with a precise clock (not in whole
        milliseconds), so the movement does not stutter. With vsync the
        screen sets the pace and `fps` is only a safety limit.
        """
        self._clock.tick(VSYNC_FPS_LIMIT if self._vsync else fps)
        now = time.perf_counter()
        elapsed = now - self._last_frame
        self._last_frame = now
        return max(0.0, elapsed)

    def ticks(self) -> int:
        """Milliseconds since the window was opened."""
        return int(pygame.time.get_ticks())

    def save(self, path: str) -> None:
        """Save the screen as an image file (useful for tests)."""
        pygame.image.save(self._screen, path)

    def close(self) -> None:
        """Close the window."""
        pygame.font.quit()
        pygame.display.quit()

    def _font(self, size: int) -> pygame.font.Font:
        """Return the (cached) built-in font in the given size."""
        if size not in self._fonts:
            self._fonts[size] = pygame.font.Font(None, size)
        return self._fonts[size]
