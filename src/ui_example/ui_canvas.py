"""Drawing layer: the only module that draws on the screen.

Everything else in the interface draws through `Canvas`, using a few
primitives that every simple graphics library (MLX included) has: a window,
filled rectangles and circles, lines, text, off-screen images, rounded buttons,
and a master frame loop.

Responsibilities & Structural Features:
    1. Graphic Primitives: Provides high-level abstract methods for neon button
       outlines, rounded panels, text cache handling, and screen wipes.
    2. Asset Management: Automatically pre-caches and scales the master Figma
       background image, game logo, and re-routes standard size parameters into
       the correct custom retro fonts (`PressStart2P` and `DotGothic16`).
    3. Hardware Projections: Hosts a centralized aspect-ratio compression
       engine (`draw_game_field`). It automatically intercepts oversized
       backend matrix arrays, smoothly compresses the game surface on the fly,
       and centers the viewport to shield layout views from out-of-bounds
       exceptions.

To change the graphics library, only this module, `ui_input.py`, and the
low-level inside `GameRenderer` have to be rewritten. The master game views
and menu components remain completely untouched.
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from typing import Any, Literal

import pygame  # type: ignore

from src.ui_example.ui_theme import WHITE, Color
from src.renderer import GameRenderer


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

        self._fonts: dict[tuple[str, int], pygame.font.Font] = {}
        assets_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "assets"
            )
        bg_path = os.path.join(assets_dir, "background.jpg")
        try:
            raw_bg = pygame.image.load(bg_path).convert()
            self.menu_bg = pygame.transform.scale(raw_bg, (width, height))
        except pygame.error:
            self.menu_bg = None

        logo_path = os.path.join(assets_dir, "logo.png")
        try:
            self.menu_logo_img = pygame.image.load(logo_path)
        except pygame.error:
            self.menu_logo_img = None
        self.game_renderer = GameRenderer(self._target, tile_size=32)

        ui_sprites_path = os.path.join(assets_dir, "ui_sprites.png")
        try:
            self.ui_sheet = pygame.image.load(ui_sprites_path).convert_alpha()
        except pygame.error:
            self.ui_sheet = None

        # --- ТВОЕ НОВОЕ ДИАЛОГОВОЕ ОКНО ПАУЗЫ ИЗ FIGMA ---
        try:
            self.dialog_img = pygame.image.load(os.path.join(assets_dir, "dialog.png")).convert_alpha()
        except pygame.error:
            self.dialog_img = None

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

    def get_ui_sprite(self, x_src: int, y_coord: int, width: int,
                      height: int) -> pygame.Surface | None:
        """Slice a specific UI frame from the master UI sheet.
        In MLX, this translates to reading a pixel block from an image buffer.
        """
        if not self.ui_sheet:
            return None
        sprite = pygame.Surface((width, height), pygame.SRCALPHA)
        sprite.blit(self.ui_sheet, (0, 0), (x_src, y_coord, width, height))
        return sprite

    def draw_image(
            self, surface: pygame.Surface | None, x: int, y: int
            ) -> None:
        """Draw a prepared off-screen image (sprite/bkgd) onto the target."""
        if surface:
            self._target.blit(surface, (x, y))

    def fill_circle(self, x: int, y: int, radius: int, color: Color) -> None:
        """Draw a filled circle centered on (x, y)."""
        pygame.draw.circle(self._target, color, (x, y), max(1, radius))

    def outline_circle(
            self, x: int, y: int, radius: int, color: Color, thickness: int = 2
            ) -> None:
        """Draw the border of a circle centered on (x, y)."""
        pygame.draw.circle(self._target, color, (x, y), max(1, radius),
                           thickness)

    def line(self, x1: int, y1: int, x2: int, y2: int, color: Color,
             thickness: int = 1) -> None:
        """Draw a straight line."""
        pygame.draw.line(self._target, color, (x1, y1), (x2, y2), thickness)

    def text(
            self, message: str, x: int, y: int, color: Color = WHITE,
            size: int = 28, align: Align = "left"
            ) -> None:
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
        """Return the (cached) custom pixel font in the given size."""
        if size == 20:
            font_name = "DotGothic16-Regular.ttf"
        else:
            font_name = "PressStart2P-Regular.ttf"
        cache_key = (font_name, size)

        if cache_key not in self._fonts:
            assets_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "assets"
                )
            font_path = os.path.join(assets_dir, font_name)

            try:
                self._fonts[cache_key] = pygame.font.Font(font_path, size)
            except pygame.error:
                self._fonts[cache_key] = pygame.font.Font(None, size)

        return self._fonts[cache_key]

    def draw_game_field(self, hud_top: int, hud_bottom: int,
                        grid: list[list[int]], pacgums: set[Any],
                        super_pacgums: set[Any], player: Any,
                        ghosts: list[Any]) -> tuple[int, int, int]:
        """Draw the scaled and centered game board along with all active
        entities.

        Args:
            hud_top: Upper vertical offset zone allocated for score tallies.
            hud_bottom: Lower vertical offset zone allocated for remain lives.
            grid: Structural matrix list from the backend map generator.
            pacgums: Active positions containing remaining small food items.
            super_pacgums: Active positions containing remaining energizers.
            player: Backend Player model data container.
            ghosts: List containing active tracking backend ghost entities.

        Returns:
            A tuple containing calculated offset_x, offset_y, and the final
            scaled matrix width.
        """
        # Synchronize the renderer target screen with current canvas buffer
        self.game_renderer.screen = self._target

        # Calculate base pixel dimensions of the raw maze layout
        maze_w = len(grid) * 32 if (grid and len(grid) > 0) else 0
        maze_h = len(grid) * 32 if grid else 0

        # Calculate bounding boxes for the permitted gameplay zone
        max_w = self.width - 80
        max_h = self.height - hud_top - hud_bottom

        # Compute aspect-ratio scale scaling factor
        scale_w = max_w / maze_w if maze_w > 0 else 1.0
        scale_h = max_h / maze_h if maze_h > 0 else 1.0
        scale_ratio = min(scale_w, scale_h, 1.0)

        final_w = int(maze_w * scale_ratio)
        final_h = int(maze_h * scale_ratio)

        # Center the fields dynamically
        offset_x = (self.width - final_w) // 2
        offset_y = hud_top + (max_h - final_h) // 2

        # Draw the maze graphics onto a clean isolated Pygame surface
        maze_surface = pygame.Surface((maze_w, maze_h), pygame.SRCALPHA)
        orig_screen = self.game_renderer.screen
        self.game_renderer.screen = maze_surface

        self.game_renderer.draw_maze(grid, pacgums, super_pacgums)
        self.game_renderer.draw_entities(player, ghosts)

        # Project and compress the finalized frame onto the main screen target
        self.game_renderer.screen = orig_screen
        if scale_ratio < 1.0:
            scaled = pygame.transform.smoothscale(maze_surface,
                                                  (final_w, final_h))
            self._target.blit(scaled, (offset_x, offset_y))
        else:
            self._target.blit(maze_surface, (offset_x, offset_y))

        return offset_x, offset_y, final_w
