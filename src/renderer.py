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
    master cycle.Replacing the underlying graphics library involves rewriting
    only this component alongside the Canvas layer.
"""

from __future__ import annotations

import os
from typing import Any

import pygame

from src.models.entity_models import Direction, exact_position


class GameRenderer:
    """Handles low-level sprite rendering and autotiling logic using Pygame."""

    def __init__(self, screen: pygame.Surface, tile_size: int = 32) -> None:
        """Initialize the renderer and load graphic assets from disk.

        Args:
            screen: The master Pygame window surface where the gameplay
                buffer will be projected.
            tile_size: The base pixel dimensions of a single logical grid cell.
                Defaults to 32 to match the standard asset resolution.

        Raises:
            FileNotFoundError: If any of the required sprite sheets (.png file)
                are missing from the project assets directory.
        """
        self.screen = screen
        self.tile_size = tile_size
        self.death_frame = -1
        self.death_timer = 0
        self.last_lives = None
        self.death_x_pos = 0
        self.death_y_pos = 0

        # Load graphic sheets from the project assets directory
        assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        self.pacman_sheet = pygame.image.load(
            os.path.join(assets_dir, "pacman_sprites.png"))
        self.walls_sheet = pygame.image.load(
            os.path.join(assets_dir, "wall_sprites.png"))
        self.ghost_sheet = pygame.image.load(
            os.path.join(assets_dir, "ghosts_sprites.png"))
        self.food_sheet = pygame.image.load(
            os.path.join(assets_dir, "pacgum_sprites.png"))

        # Eyes of an eaten ghost: one small image per direction
        self.eyes_sprites: dict[Direction, pygame.Surface] = {}
        for direction, file_name in (
                (Direction.UP, "eyesup.png"),
                (Direction.DOWN, "eyesdown.png"),
                (Direction.LEFT, "eyesleft.png"),
                (Direction.RIGHT, "eyesright.png")):
            try:
                self.eyes_sprites[direction] = pygame.image.load(
                    os.path.join(assets_dir, file_name)).convert_alpha()
            except (pygame.error, FileNotFoundError):
                pass          # Missing file: circles are drawn instead.

        # Autotile layout map to match Figma grid parameters
        self.autotile_map: dict[int, tuple[int, int]] = {
            1:  (0, 0), 4:  (1, 0), 8:  (2, 0), 2:  (3, 0),  # Straight lines
            9:  (0, 1), 3:  (1, 1), 12: (2, 1), 6:  (3, 1),  # Corners
            5:  (0, 2), 10: (1, 2),                          # Rails
            7:  (0, 3), 13: (1, 3), 14: (2, 3), 11: (2, 3),  # Junctions
            15: (3, 3)                                       # Solid block
        }

    # -----------------------------------------------------------------
    # Sprite slicers
    # -----------------------------------------------------------------

    def _slice_sprite(self, col_index: int, row_index: int,
                      sheet: pygame.Surface) -> pygame.Surface:
        """Helper to slice a 32x32 asset from a given sheet with Figma padding.

        Args:
            col_index: The column index of the asset in the sprite grid.
            row_index: The row index of the asset in the sprite grid.
            sheet: The source Pygame surface to slice the texture from.

        Returns:
            A new isolated 32x32 transparent Pygame surface containing the
            sprite.
        """
        start_x = 16
        start_y = 16
        step = 32 + 20  # 32px element + 20px spacer gap

        exact_x = start_x + (col_index * step)
        exact_y = start_y + (row_index * step)

        sprite = pygame.Surface((32, 32), pygame.SRCALPHA)
        sprite.blit(sheet, (0, 0), (exact_x, exact_y, 32, 32))
        return sprite

    def get_wall_tile(self, col_index: int, row_index: int) -> pygame.Surface:
        """Slice a single 32x32 wall tile from the wall sheet."""
        return self._slice_sprite(col_index, row_index, self.walls_sheet)

    def get_food_tile(self, col_index: int, row_index: int) -> pygame.Surface:
        """Slice a single 32x32 food item tile from the pacgum sheet."""
        return self._slice_sprite(col_index, row_index, self.food_sheet)

    def get_pacman_tile(self, col_index: int,
                        row_index: int) -> pygame.Surface:
        """Slice a single 32x32 Pac-Man sprite using the Figma layout."""
        return self._slice_sprite(col_index, row_index, self.pacman_sheet)

    def get_ghosts_tile(self, col_index: int,
                        row_index: int) -> pygame.Surface:
        """Slice a single 32x32 ghost sprite using the Figma layout."""
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
    # Maze, player, ghosts
    # -----------------------------------------------------------------

    def draw_maze(self, grid: list[list[int]], pacgums: set[Any],
                  super_pacgums: set[Any]) -> None:
        """Process the dual-pass autotiling pipeline for walls and food items.

        Args:
            grid: Two-dimensional matrix represents the structural maze layout.
            pacgums: A set of positions containing standard edible dots.
            super_pacgums: A set of positions containing energizers.
        """
        height_tiles = len(grid)
        width_tiles = len(grid[0]) if height_tiles > 0 else 0

        # Calculate time-based frame swapping for the pulsing super-pacgums
        energizer_phase = (pygame.time.get_ticks() // 200) % 2

        # Slice items from Row 0 of the independent food asset sheet
        super_full_sprite = self.get_food_tile(0, 0)
        super_blank_sprite = self.get_food_tile(1, 0)
        dot_sprite = self.get_food_tile(2, 0)

        # Unpack backend position sets into native coordinate tuples for safety
        active_dots = set()
        if pacgums:
            for p in pacgums:
                if hasattr(p, 'x') and hasattr(p, 'y'):
                    active_dots.add((p.x, p.y))
                elif isinstance(p, tuple) and len(p) == 2:
                    active_dots.add(p)

        active_super_dots = set()
        if super_pacgums:
            for p in super_pacgums:
                if hasattr(p, 'x') and hasattr(p, 'y'):
                    active_super_dots.add((p.x, p.y))
                elif isinstance(p, tuple) and len(p) == 2:
                    active_super_dots.add(p)

        # Iterate through the grid matrix coordinates
        for y in range(height_tiles):
            for x in range(width_tiles):
                val = grid[y][x]
                screen_x = x * self.tile_size
                screen_y = y * self.tile_size

                # Render standard small dots
                if (x, y) in active_dots:
                    self.screen.blit(dot_sprite, (screen_x, screen_y))

                # Render animated pulsing energizers
                if (x, y) in active_super_dots:
                    if energizer_phase == 0:
                        self.screen.blit(super_full_sprite,
                                         (screen_x, screen_y))
                    else:
                        self.screen.blit(super_blank_sprite,
                                         (screen_x, screen_y))

                next_x, prev_x = x + 1, x - 1
                next_y, prev_y = y + 1, y - 1

                # PASS 1: Generate base wall structure
                if val in self.autotile_map:
                    c, r = self.autotile_map[val]
                    tile = self.get_wall_tile(c, r)
                    if tile:
                        self.screen.blit(tile, (screen_x, screen_y))

                # PASS 2: Inject edge connection caps
                if (val & 4):
                    if prev_x < 0 or not (grid[y][prev_x] & 4):
                        if not (val & 8):
                            cap = self.get_wall_tile(0, 4)
                            if cap:
                                self.screen.blit(cap, (screen_x, screen_y))
                    if next_x >= width_tiles or not (grid[y][next_x] & 4):
                        if not (val & 2):
                            cap = self.get_wall_tile(1, 4)
                            if cap:
                                self.screen.blit(cap, (screen_x, screen_y))

                if (val & 1):
                    if prev_x < 0 or not (grid[y][prev_x] & 1):
                        if not (val & 8):
                            cap = self.get_wall_tile(0, 5)
                            if cap:
                                self.screen.blit(cap, (screen_x, screen_y))
                    if next_x >= width_tiles or not (grid[y][next_x] & 1):
                        if not (val & 2):
                            cap = self.get_wall_tile(1, 5)
                            if cap:
                                self.screen.blit(cap, (screen_x, screen_y))

                if (val & 8):
                    if prev_y < 0 or not (grid[prev_y][x] & 8):
                        if not (val & 1):
                            cap = self.get_wall_tile(2, 6)
                            if cap:
                                self.screen.blit(cap, (screen_x, screen_y))
                    if next_y >= height_tiles or not (grid[next_y][x] & 8):
                        if not (val & 4):
                            cap = self.get_wall_tile(3, 6)
                            if cap:
                                self.screen.blit(cap, (screen_x, screen_y))

                if (val & 2):
                    if prev_y < 0 or not (grid[prev_y][x] & 2):
                        if not (val & 1):
                            cap = self.get_wall_tile(0, 6)
                            if cap:
                                self.screen.blit(cap, (screen_x, screen_y))
                    if next_y >= height_tiles or not (grid[next_y][x] & 2):
                        if not (val & 4):
                            cap = self.get_wall_tile(1, 6)
                            if cap:
                                self.screen.blit(cap, (screen_x, screen_y))

                # Render solid perimeter borders around the gameplay window
                if y == 0:
                    border = self.get_wall_tile(2, 4)
                    if border:
                        self.screen.blit(border, (screen_x, screen_y))
                if y == height_tiles - 1:
                    border = self.get_wall_tile(2, 5)
                    if border:
                        self.screen.blit(border, (screen_x, screen_y))
                if x == 0:
                    border = self.get_wall_tile(2, 2)
                    if border:
                        self.screen.blit(border, (screen_x, screen_y))
                if x == width_tiles - 1:
                    border = self.get_wall_tile(3, 2)
                    if border:
                        self.screen.blit(border, (screen_x, screen_y))

    def draw_entities(self, player_model: Any, ghosts_list: list[Any]) -> None:
        """Render continuous pixel movement and state changes for all entities.

        Args:
            player_model: The master backend Player data model instance.
            ghosts_list: List containing active backend Ghost entity models.
        """
        # --- A. PAC-MAN ---
        p_x, p_y = exact_position(player_model)
        current_px = int(p_x * self.tile_size)
        current_py = int(p_y * self.tile_size)

        spawn_x = int(player_model.spawn.x * self.tile_size)
        spawn_y = int(player_model.spawn.y * self.tile_size)

        if self.last_lives is None:
            self.last_lives = player_model.lives
            self.prev_alive_x = current_px
            self.prev_alive_y = current_py

        # Trigger death sequence when a life counter drops
        if player_model.lives < self.last_lives and self.death_frame == -1:
            self.death_frame = 0
            self.death_timer = pygame.time.get_ticks()
            self.death_x_pos = self.prev_alive_x
            self.death_y_pos = self.prev_alive_y

        if self.death_frame == -1:
            if (current_px != 0 and current_py != 0 and
                    current_px != spawn_x and current_py != spawn_y):
                self.prev_alive_x = current_px
                self.prev_alive_y = current_py

        # PAC-MAN DEATH ANIMATION SEQUENCE
        if self.death_frame != -1:
            now = pygame.time.get_ticks()
            if now - self.death_timer > 130:
                self.death_frame += 1
                self.death_timer = now

            if self.death_frame < 12:
                death_sprite = self.get_pacman_tile(self.death_frame, 4)
                self.screen.blit(death_sprite,
                                 (self.death_x_pos, self.death_y_pos))
                return
            else:
                self.death_frame = -1
                self.last_lives = player_model.lives

        # STANDARD GAMEPLAY STATE REFRESH
        ticks = pygame.time.get_ticks() // 70
        anim_sequence = [0, 1, 2, 1]
        mouth_phase = anim_sequence[ticks % 4]

        current_dir = player_model.direction
        if current_dir == Direction.NONE:
            pacman_sprite = self.get_pacman_tile(2, 0)
        else:
            col_idx = mouth_phase
            if current_dir == Direction.RIGHT:
                row_idx = 0
            elif current_dir == Direction.LEFT:
                row_idx = 1
            elif current_dir == Direction.UP:
                row_idx = 2
            elif current_dir == Direction.DOWN:
                row_idx = 3
            else:
                row_idx = 0

            pacman_sprite = self.get_pacman_tile(col_idx, row_idx)
        self.screen.blit(pacman_sprite, (current_px, current_py))

        # --- B. GHOSTS RENDERING ---
        ghost_anim_phase = (pygame.time.get_ticks() // 120) % 2
        is_blinking = (pygame.time.get_ticks() // 200) % 2

        for ghost in ghosts_list:
            g_x, g_y = exact_position(ghost)
            gx = int(g_x * self.tile_size)
            gy = int(g_y * self.tile_size)

            if ghost.is_eaten:                    # Only eyes going home.
                self._draw_ghost_eyes(gx, gy, ghost.direction)
                continue

            g_col_idx, g_row_idx = 0, 0

            # Process edible running behavior state
            if ghost.is_edible:
                g_row_idx = 4
                if ghost.timer < 3.0 and is_blinking:
                    g_col_idx = 3 if ghost_anim_phase == 0 else 4
                else:
                    g_col_idx = 0 if ghost_anim_phase == 0 else 1
            else:
                # Assign default row mapping based on ghost entities
                name = ghost.name.lower()
                if 'blinky' in name:
                    g_row_idx = 0
                elif 'pinky' in name:
                    g_row_idx = 1
                elif 'inky' in name:
                    g_row_idx = 2
                elif 'clyde' in name:
                    g_row_idx = 3

                # Map eye look direction to asset sheet columns
                if ghost.direction == Direction.LEFT:
                    g_col_idx = 0 if ghost_anim_phase == 0 else 1
                elif ghost.direction == Direction.RIGHT:
                    g_col_idx = 2 if ghost_anim_phase == 0 else 3
                elif ghost.direction == Direction.UP:
                    g_col_idx = 4 if ghost_anim_phase == 0 else 5
                elif ghost.direction == Direction.DOWN:
                    g_col_idx = 6 if ghost_anim_phase == 0 else 7
                else:
                    g_col_idx = 0 if ghost.direction == Direction.LEFT else 2

            ghost_sprite = self.get_ghosts_tile(g_col_idx, g_row_idx)
            self.screen.blit(ghost_sprite, (gx, gy))
