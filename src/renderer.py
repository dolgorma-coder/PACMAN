"""Maze, items and entities graphic renderer for Pac-Man (42 Edition).

This module acts as a dedicated graphic rendering engine, completely isolating
the core layout views from low-level Pygame draw calls and hardware surface
manipulations. It bridges the backend game models with the frontend user
interface by transforming logical matrix structures into continuous
pixel-perfect displays.

Architecture & Responsibilities:
    1. Sprite Sheet Slicing: Efficiently extracts 32x32 tiles for walls,
       entities, and pacgums from standalone asset sheets, strictly following
       the custom Figma grid metrics (padding, cell layouts, and spacing
       configurations).
    2. Autotiling Pipeline: Implements a dual-pass rendering pipeline that
       handles neon wall connections, junction rendering, and contextual
       boundary corner caps.
    3. Dynamic Frame Animation: Controls time-synchronised sprite swapping for
       the pulsing super-pacgums and manages the 12-frame linear decay
       sequence for the Player death animation.

Target Synchronization:
    To maintain the structural rule of separation of concerns required by the
    subject, this module translates game logic frames independently of the
    master cycle. Replacing the underlying graphics library involves
    rewriting only this component alongside the Canvas layer.
"""

from __future__ import annotations

import os
from typing import Any

import pygame

from src.models.entity_models import Direction, exact_position

# Frames of the death row (row 4) in the pacman sheet.
DEATH_FRAMES: int = 12


class GameRenderer:
    """Handle low-level sprite rendering and autotiling logic with Pygame.

    Attributes:
        screen: The master Pygame surface everything is drawn onto.
        tile_size: Pixel size of one logical grid cell.
        eyes_sprites: Eye images of eaten ghosts, one per direction, already
            scaled to the current ``tile_size``.
        autotile_map: Maps a wall bitmask to its (column, row) in the sheet.
    """

    def __init__(self, screen: pygame.Surface, tile_size: int = 32) -> None:
        """Initialize the renderer and load graphic assets from disk.

        Args:
            screen: The master Pygame window surface where the gameplay
                buffer will be projected.
            tile_size: The base pixel dimensions of a single logical grid
                cell. Defaults to 32 to match the standard asset resolution.

        Raises:
            FileNotFoundError: If any of the required sprite sheets (.png
                file) are missing from the project assets directory.
        """
        self.screen: pygame.Surface = screen
        self.tile_size: int = tile_size

        self._sprite_cache: dict[tuple[int, int, int], pygame.Surface] = {}
        self._eyes_originals: dict[Direction, pygame.Surface] = {}
        self.eyes_sprites: dict[Direction, pygame.Surface] = {}

        # Load graphic sheets from the project assets directory
        assets_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "assets"
            )
        self.pacman_sheet: pygame.Surface = pygame.image.load(
            os.path.join(assets_dir, "pacman_sprites.png"))
        self.walls_sheet: pygame.Surface = pygame.image.load(
            os.path.join(assets_dir, "wall_sprites.png"))
        self.ghost_sheet: pygame.Surface = pygame.image.load(
            os.path.join(assets_dir, "ghosts_sprites.png"))
        self.food_sheet: pygame.Surface = pygame.image.load(
            os.path.join(assets_dir, "pacgum_sprites.png"))

        # Eyes of an eaten ghost: one small image per direction
        for direction, file_name in (
                (Direction.UP, "eyesup.png"),
                (Direction.DOWN, "eyesdown.png"),
                (Direction.LEFT, "eyesleft.png"),
                (Direction.RIGHT, "eyesright.png")):
            try:
                self._eyes_originals[direction] = pygame.image.load(
                    os.path.join(assets_dir, file_name)).convert_alpha()
            except (pygame.error, FileNotFoundError):
                pass  # Missing file: circles are drawn instead.
        self._rescale_eyes()

        # Autotile layout map to match Figma grid parameters
        self.autotile_map: dict[int, tuple[int, int]] = {
            1: (0, 0), 4: (1, 0), 8: (2, 0), 2: (3, 0),    # Straight lines
            9: (0, 1), 3: (1, 1), 12: (2, 1), 6: (3, 1),   # Corners
            5: (0, 2), 10: (1, 2),                         # Rails
            7: (0, 3), 13: (1, 3), 14: (2, 3), 11: (2, 3),  # Junctions
            15: (3, 3),                                    # Solid block
        }

    # -----------------------------------------------------------------
    # Sprite slicers
    # -----------------------------------------------------------------

    def _slice_sprite(self, col_index: int, row_index: int,
                      sheet: pygame.Surface) -> pygame.Surface:
        """Slice a sprite from a sheet, scaled to ``tile_size`` (cached).

        Args:
            col_index: Column of the sprite in the sheet grid.
            row_index: Row of the sprite in the sheet grid.
            sheet: The sprite sheet to cut the sprite from.

        Returns:
            The sprite surface, ready to be blitted.
        """
        key = (id(sheet), col_index, row_index)
        cached = self._sprite_cache.get(key)
        if cached is not None:
            return cached

        exact_x = 16 + col_index * 52
        exact_y = 16 + row_index * 52
        sprite = pygame.Surface((32, 32), pygame.SRCALPHA)
        sprite.blit(sheet, (0, 0), (exact_x, exact_y, 32, 32))
        if self.tile_size != 32:
            sprite = scale_nearest(sprite, self.tile_size, self.tile_size)
        self._sprite_cache[key] = sprite
        return sprite

    def _rescale_eyes(self) -> None:
        """Rebuild ``eyes_sprites`` from the originals for ``tile_size``."""
        factor = self.tile_size / 32
        if factor == 1:
            self.eyes_sprites = dict(self._eyes_originals)
            return
        self.eyes_sprites = {
            direction: scale_nearest(
                image,
                max(1, round(image.get_width() * factor)),
                max(1, round(image.get_height() * factor)))
            for direction, image in self._eyes_originals.items()}

    def set_tile_size(self, size: int) -> None:
        """Change the cell size; sprites are rescaled once, lazily.

        Args:
            size: The new pixel size of one grid cell.
        """
        if size == self.tile_size:
            return
        self.tile_size = size
        self._sprite_cache.clear()
        self._rescale_eyes()

    def get_wall_tile(self, col_index: int, row_index: int) -> pygame.Surface:
        """Slice a single wall tile from the wall sheet.

        Args:
            col_index: Column of the tile in the sheet grid.
            row_index: Row of the tile in the sheet grid.

        Returns:
            The wall tile surface.
        """
        return self._slice_sprite(col_index, row_index, self.walls_sheet)

    def get_food_tile(self, col_index: int, row_index: int) -> pygame.Surface:
        """Slice a single food item tile from the pacgum sheet.

        Args:
            col_index: Column of the tile in the sheet grid.
            row_index: Row of the tile in the sheet grid.

        Returns:
            The food tile surface.
        """
        return self._slice_sprite(col_index, row_index, self.food_sheet)

    def get_pacman_tile(self, col_index: int,
                        row_index: int) -> pygame.Surface:
        """Slice a single Pac-Man sprite using the Figma layout.

        Args:
            col_index: Column of the sprite in the sheet grid.
            row_index: Row of the sprite in the sheet grid.

        Returns:
            The Pac-Man sprite surface.
        """
        return self._slice_sprite(col_index, row_index, self.pacman_sheet)

    def get_ghosts_tile(self, col_index: int,
                        row_index: int) -> pygame.Surface:
        """Slice a single ghost sprite using the Figma layout.

        Args:
            col_index: Column of the sprite in the sheet grid.
            row_index: Row of the sprite in the sheet grid.

        Returns:
            The ghost sprite surface.
        """
        return self._slice_sprite(col_index, row_index, self.ghost_sheet)

    def _draw_ghost_eyes(self, left: int, top: int,
                         direction: Direction) -> None:
        """Draw only the eyes of an eaten ghost (no body).

        Args:
            left: Left pixel of the ghost's cell.
            top: Top pixel of the ghost's cell.
            direction: Where the ghost is heading (the eyes look that way).
        """
        size = self.tile_size
        # A ghost standing still (NONE) looks to the left.
        sprite = (self.eyes_sprites.get(direction)
                  or self.eyes_sprites.get(Direction.LEFT))
        if sprite is not None:
            rect = sprite.get_rect(center=(left + size // 2,
                                           top + size // 2))
            self.screen.blit(sprite, rect)
            return

        # Fallback: eyes drawn with circles.
        eye_radius = max(3, size // 5)
        pupil_radius = max(2, eye_radius // 2)
        reach = eye_radius - pupil_radius
        center_y = top + size // 2 - size // 10
        for side in (-1, 1):
            eye_x = left + size // 2 + side * (size // 5)
            pygame.draw.circle(self.screen, (255, 255, 255),
                               (eye_x, center_y), eye_radius)
            pygame.draw.circle(
                self.screen, (33, 33, 255),
                (eye_x + direction.dx * reach,
                 center_y + direction.dy * reach), pupil_radius)

    # -----------------------------------------------------------------
    # Maze
    # -----------------------------------------------------------------

    @staticmethod
    def _to_coords(positions: set[Any] | None) -> set[tuple[int, int]]:
        """Convert backend position objects into plain ``(x, y)`` tuples.

        Args:
            positions: Objects with ``x`` and ``y`` attributes, or already
                ``(x, y)`` tuples. May be ``None`` or empty.

        Returns:
            A set of native coordinate tuples.
        """
        coords: set[tuple[int, int]] = set()
        if not positions:
            return coords
        for pos in positions:
            if hasattr(pos, "x") and hasattr(pos, "y"):
                coords.add((pos.x, pos.y))
            elif isinstance(pos, tuple) and len(pos) == 2:
                coords.add(pos)
        return coords

    def _blit_wall(self, col_index: int, row_index: int,
                   screen_x: int, screen_y: int) -> None:
        """Blit one wall tile at the given pixel position.

        Args:
            col_index: Column of the tile in the wall sheet.
            row_index: Row of the tile in the wall sheet.
            screen_x: Destination left pixel.
            screen_y: Destination top pixel.
        """
        self.screen.blit(self.get_wall_tile(col_index, row_index),
                         (screen_x, screen_y))

    def _draw_wall_caps(self, grid: list[list[int]], x: int, y: int) -> None:
        """Draw the edge connection caps of one cell (autotiling pass 2).

        Args:
            grid: Two-dimensional matrix with the maze layout bitmasks.
            x: Column of the cell in the grid.
            y: Row of the cell in the grid.
        """
        height_tiles = len(grid)
        width_tiles = len(grid[0])
        val = grid[y][x]
        screen_x = x * self.tile_size
        screen_y = y * self.tile_size

        # Horizontal walls: (bit, sheet row of the caps).
        for bit, row in ((4, 4), (1, 5)):
            if not val & bit:
                continue
            if (x == 0 or not grid[y][x - 1] & bit) and not val & 8:
                self._blit_wall(0, row, screen_x, screen_y)
            if (x + 1 >= width_tiles
                    or not grid[y][x + 1] & bit) and not val & 2:
                self._blit_wall(1, row, screen_x, screen_y)

        # Vertical walls: (bit, previous-cap column, next-cap column).
        for bit, prev_col, next_col in ((8, 2, 3), (2, 0, 1)):
            if not val & bit:
                continue
            if (y == 0 or not grid[y - 1][x] & bit) and not val & 1:
                self._blit_wall(prev_col, 6, screen_x, screen_y)
            if (y + 1 >= height_tiles
                    or not grid[y + 1][x] & bit) and not val & 4:
                self._blit_wall(next_col, 6, screen_x, screen_y)

    def _draw_borders(self, x: int, y: int, width_tiles: int,
                      height_tiles: int) -> None:
        """Draw the solid border tiles around the gameplay window.

        Args:
            x: Column of the cell in the grid.
            y: Row of the cell in the grid.
            width_tiles: Grid width in cells.
            height_tiles: Grid height in cells.
        """
        screen_x = x * self.tile_size
        screen_y = y * self.tile_size
        if y == 0:
            self._blit_wall(2, 4, screen_x, screen_y)
        if y == height_tiles - 1:
            self._blit_wall(2, 5, screen_x, screen_y)
        if x == 0:
            self._blit_wall(2, 2, screen_x, screen_y)
        if x == width_tiles - 1:
            self._blit_wall(3, 2, screen_x, screen_y)

    def draw_maze(self, grid: list[list[int]], pacgums: set[Any],
                  super_pacgums: set[Any]) -> None:
        """Process the dual-pass autotiling pipeline for walls and food.

        Args:
            grid: Two-dimensional matrix representing the maze layout.
            pacgums: A set of positions containing standard edible dots.
            super_pacgums: A set of positions containing energizers.
        """
        height_tiles = len(grid)
        width_tiles = len(grid[0]) if height_tiles > 0 else 0

        # Time-based frame swapping for the pulsing super-pacgums
        energizer_phase = (pygame.time.get_ticks() // 200) % 2

        # Row 0 of the independent food asset sheet
        super_full_sprite = self.get_food_tile(0, 0)
        super_blank_sprite = self.get_food_tile(1, 0)
        dot_sprite = self.get_food_tile(2, 0)

        active_dots = self._to_coords(pacgums)
        active_super_dots = self._to_coords(super_pacgums)

        for y in range(height_tiles):
            for x in range(width_tiles):
                val = grid[y][x]
                screen_x = x * self.tile_size
                screen_y = y * self.tile_size

                # Standard small dots
                if (x, y) in active_dots:
                    self.screen.blit(dot_sprite, (screen_x, screen_y))

                # Animated pulsing energizers
                if (x, y) in active_super_dots:
                    energizer = (super_full_sprite if energizer_phase == 0
                                 else super_blank_sprite)
                    self.screen.blit(energizer, (screen_x, screen_y))

                # PASS 1: Generate base wall structure
                if val in self.autotile_map:
                    col, row = self.autotile_map[val]
                    self._blit_wall(col, row, screen_x, screen_y)

                # PASS 2: Inject edge connection caps
                self._draw_wall_caps(grid, x, y)

                # Solid perimeter borders around the gameplay window
                self._draw_borders(x, y, width_tiles, height_tiles)

    # -----------------------------------------------------------------
    # Player and ghosts
    # -----------------------------------------------------------------

    def _draw_player(self, player_model: Any) -> None:
        """Render Pac-Man, either alive (mouth animation) or dying.

        Args:
            player_model: The master backend Player data model instance.
        """
        p_x, p_y = exact_position(player_model)
        current_px = int(p_x * self.tile_size)
        current_py = int(p_y * self.tile_size)

        if player_model.is_dying:
            # Frame chosen from the engine's progress: always in sync.
            frame = min(DEATH_FRAMES - 1,
                        int(player_model.death_progress * DEATH_FRAMES))
            pacman_sprite = self.get_pacman_tile(frame, 4)
        else:
            ticks = pygame.time.get_ticks() // 70
            mouth_phase = [0, 1, 2, 1][ticks % 4]
            current_dir = player_model.direction
            if current_dir == Direction.NONE:
                pacman_sprite = self.get_pacman_tile(2, 0)
            else:
                row_idx = {Direction.RIGHT: 0, Direction.LEFT: 1,
                           Direction.UP: 2, Direction.DOWN: 3}.get(
                               current_dir, 0)
                pacman_sprite = self.get_pacman_tile(mouth_phase, row_idx)
        self.screen.blit(pacman_sprite, (current_px, current_py))

    def _draw_ghost(self, ghost: Any, anim_phase: int,
                    is_blinking: int) -> None:
        """Render a single ghost in its current state.

        Args:
            ghost: A backend Ghost entity model.
            anim_phase: Current body animation frame (0 or 1).
            is_blinking: Non-zero while an edible ghost should flash white.
        """
        g_x, g_y = exact_position(ghost)
        gx = int(g_x * self.tile_size)
        gy = int(g_y * self.tile_size)

        if ghost.is_eaten:  # Only eyes going home.
            self._draw_ghost_eyes(gx, gy, ghost.direction)
            return

        g_col_idx, g_row_idx = 0, 0

        if ghost.is_edible:
            g_row_idx = 4
            if ghost.timer < 3.0 and is_blinking:
                g_col_idx = 3 if anim_phase == 0 else 4
            else:
                g_col_idx = 0 if anim_phase == 0 else 1
        else:
            # Default row mapping based on the ghost's name
            name = ghost.name.lower()
            if "blinky" in name:
                g_row_idx = 0
            elif "pinky" in name:
                g_row_idx = 1
            elif "inky" in name:
                g_row_idx = 2
            elif "clyde" in name:
                g_row_idx = 3

            # Map eye look direction to asset sheet columns
            if ghost.direction == Direction.LEFT:
                g_col_idx = 0 if anim_phase == 0 else 1
            elif ghost.direction == Direction.RIGHT:
                g_col_idx = 2 if anim_phase == 0 else 3
            elif ghost.direction == Direction.UP:
                g_col_idx = 4 if anim_phase == 0 else 5
            elif ghost.direction == Direction.DOWN:
                g_col_idx = 6 if anim_phase == 0 else 7
            else:
                g_col_idx = 2

        ghost_sprite = self.get_ghosts_tile(g_col_idx, g_row_idx)
        self.screen.blit(ghost_sprite, (gx, gy))

    def draw_entities(self, player_model: Any,
                      ghosts_list: list[Any]) -> None:
        """Render continuous pixel movement and state changes of entities.

        Args:
            player_model: The master backend Player data model instance.
            ghosts_list: List containing active backend Ghost entity models.
        """
        self._draw_player(player_model)

        ticks = pygame.time.get_ticks()
        ghost_anim_phase = (ticks // 120) % 2
        is_blinking = (ticks // 200) % 2
        for ghost in ghosts_list:
            self._draw_ghost(ghost, ghost_anim_phase, is_blinking)


def scale_nearest(source: pygame.Surface, width: int,
                  height: int) -> pygame.Surface:
    """Scale an image with nearest-neighbour (no blur, pixel art friendly).

    Only reads and writes single pixels, so it can be rewritten on top of
    an MLX image buffer. It is slow, so call it once per sprite and cache
    the result, never every frame.

    Args:
        source: The surface to scale.
        width: Target width in pixels.
        height: Target height in pixels.

    Returns:
        A new surface of size ``(width, height)``.
    """
    src_w, src_h = source.get_size()
    result = pygame.Surface((width, height), pygame.SRCALPHA)
    for y in range(height):
        src_y = y * src_h // height
        for x in range(width):
            result.set_at((x, y), source.get_at((x * src_w // width, src_y)))
    return result
