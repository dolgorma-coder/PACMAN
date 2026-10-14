"""Drawing of the game screen: maze, items, entities, HUD and pause menu."""

from __future__ import annotations

from dataclasses import dataclass

from src.app import App
from src.ghost_modes import GhostMode
from src.models.app_models import PauseItem
from src.models.entity_models import Direction, Ghost, Position, exact_position
from src.models.game_state import GameState, GameStatus
from src.models.maze_models import MOVE_DIRECTIONS, Maze
from src.ui_example.ui_canvas import Canvas, Layer
from src.ui_example.ui_theme import (FOOTER_HEIGHT, GHOST_COLORS, GRAY, GREEN,
                                     HIGHLIGHT, HUD_HEIGHT, MAX_CELL_SIZE,
                                     MIN_CELL_SIZE, PANEL, PELLET,
                                     RED, SCARED_BLUE, SOLID_CELL,
                                     WALL_BLUE, WHITE, YELLOW,
                                     Color)

FLASH_SECONDS = 2.0       # Edible ghosts flash when this close to the end.


@dataclass(frozen=True)
class Geometry:
    """Where the maze is drawn on the screen.

    Attributes:
        cell: Size of a maze cell, in pixels.
        left: X of the maze's left edge.
        top: Y of the maze's top edge.
    """

    cell: int
    left: int
    top: int

    def center(self, column: float, row: float) -> tuple[int, int]:
        """Pixel at the center of a (possibly fractional) cell position."""
        return (round(self.left + (column + 0.5) * self.cell),
                round(self.top + (row + 0.5) * self.cell))


def make_geometry(maze: Maze, width: int, height: int) -> Geometry:
    """Fit the maze in the free area of a `width` x `height` window."""
    free_height = height - HUD_HEIGHT - FOOTER_HEIGHT
    cell = min(MAX_CELL_SIZE, width // maze.width, free_height // maze.height)
    cell = max(MIN_CELL_SIZE, cell)
    left = (width - cell * maze.width) // 2
    top = HUD_HEIGHT + (free_height - cell * maze.height) // 2
    return Geometry(cell, left, top)


class GameView:
    """Draws a game in progress. The maze picture is made once per level."""

    def __init__(self, canvas: Canvas) -> None:
        """Create the view for a canvas."""
        self.canvas = canvas
        self._cache: tuple[Maze, Geometry, Layer] | None = None

    def draw(self, app: App, now_ms: int) -> None:
        """Draw the whole game screen."""
        engine = app.engine
        if engine is None:
            return
        state = engine.state
        maze = state.level.maze
        if self._cache is None or self._cache[0] is not maze:
            self._cache = self._build_cache(maze)
        _, geometry, layer = self._cache

        self.canvas.draw_layer(layer)
        self._draw_items(state, geometry)
        self._draw_ghosts(state, geometry, now_ms)
        self._draw_player(state, geometry)
        self._draw_hud(state)
        self._draw_footer(state, engine.modes.mode)
        if state.status == GameStatus.PAUSED:
            self._draw_pause_menu(app.pause_index)

    # -----------------------------------------------------------------
    # Maze (drawn once per level)
    # -----------------------------------------------------------------

    def _build_cache(self, maze: Maze) -> tuple[Maze, Geometry, Layer]:
        """Draw the maze on an off-screen image."""
        geometry = make_geometry(maze, self.canvas.width,
                                 self.canvas.height)
        layer = self.canvas.record(lambda: self._draw_maze(maze, geometry))
        return maze, geometry, layer

    def _draw_maze(self, maze: Maze, geometry: Geometry) -> None:
        """Draw the solid cells and the walls."""
        size = geometry.cell
        for y in range(maze.height):
            for x in range(maze.width):
                position = Position(x, y)
                left = geometry.left + x * size
                top = geometry.top + y * size
                if not maze.is_walkable(position):
                    self.canvas.fill_rect(left, top, size, size, SOLID_CELL)
                    continue
                for direction in MOVE_DIRECTIONS:
                    if maze.has_wall(position, direction):
                        self._draw_wall(left, top, size, direction)

    def _draw_wall(self, left: int, top: int, size: int,
                   direction: Direction) -> None:
        """Draw one side of a cell."""
        right, bottom = left + size, top + size
        edges = {
            Direction.UP: (left, top, right, top),
            Direction.RIGHT: (right, top, right, bottom),
            Direction.DOWN: (left, bottom, right, bottom),
            Direction.LEFT: (left, top, left, bottom),
        }
        x1, y1, x2, y2 = edges[direction]
        self.canvas.line(x1, y1, x2, y2, WALL_BLUE, 2)

    # -----------------------------------------------------------------
    # Items and entities
    # -----------------------------------------------------------------

    def _draw_items(self, state: GameState, geometry: Geometry) -> None:
        """Draw pacgums (small) and super-pacgums (big)."""
        for position in state.level.pacgums:
            x, y = geometry.center(position.x, position.y)
            self.canvas.fill_circle(x, y, geometry.cell // 8, PELLET)
        for position in state.level.super_pacgums:
            x, y = geometry.center(position.x, position.y)
            self.canvas.fill_circle(x, y, geometry.cell // 3, PELLET)

    def _draw_ghosts(self, state: GameState, geometry: Geometry,
                     now_ms: int) -> None:
        """Draw the ghosts at their real place.

        An eaten ghost shows only two eyes while it waits at home; an angry
        one has a white ring.
        """
        radius = int(geometry.cell * 0.4)
        for ghost in state.ghosts:
            x, y = geometry.center(*exact_position(ghost))
            if ghost.is_eaten:
                eye = max(1, radius // 3)
                self.canvas.fill_circle(x - eye * 2, y, eye, WHITE)
                self.canvas.fill_circle(x + eye * 2, y, eye, WHITE)
                continue
            self.canvas.fill_circle(x, y, radius,
                                    self._ghost_color(ghost, now_ms))
            if ghost.angry:
                self.canvas.outline_circle(x, y, radius + 3, WHITE, 2)

    @staticmethod
    def _ghost_color(ghost: Ghost, now_ms: int) -> Color:
        """Own color, blue when edible, white flashes before it ends."""
        if not ghost.is_edible:
            return GHOST_COLORS.get(ghost.name, RED)
        if ghost.timer < FLASH_SECONDS and (now_ms // 200) % 2 == 0:
            return WHITE
        return SCARED_BLUE

    def _draw_player(self, state: GameState, geometry: Geometry) -> None:
        """Draw the player at its real place."""
        x, y = geometry.center(*exact_position(state.player))
        self.canvas.fill_circle(x, y, int(geometry.cell * 0.42), YELLOW)

    # -----------------------------------------------------------------
    # HUD, footer and pause menu
    # -----------------------------------------------------------------

    def _draw_hud(self, state: GameState) -> None:
        """Top bar: score, lives, level and remaining time."""
        canvas = self.canvas
        seconds = max(0, int(state.time_left))
        canvas.text(f"SCORE {state.player.score}", 20, 16, WHITE, 34)
        canvas.text(f"LIVES {state.player.lives}", 300, 16, WHITE, 34)
        canvas.text(f"LEVEL {state.level_number}/{state.level_count}", 480,
                    16, WHITE, 34)
        canvas.text(f"TIME {seconds}", canvas.width - 20, 16,
                    RED if seconds <= 10 else WHITE, 34, "right")
        canvas.line(0, HUD_HEIGHT - 2, canvas.width, HUD_HEIGHT - 2,
                    WALL_BLUE, 1)

    def _draw_footer(self, state: GameState, mode: GhostMode) -> None:
        """Bottom bar: key hints, state of the cheats and ghost phase."""
        cheats = state.cheats
        canvas = self.canvas
        y = canvas.height - FOOTER_HEIGHT + 8
        if cheats.enabled:
            def flag(active: bool) -> str:
                return "ON" if active else "off"

            canvas.text(
                f"CHEATS ON  F2 invincible {flag(cheats.invincible)}  "
                f"F3 freeze {flag(cheats.freeze_ghosts)}  "
                f"F4 fast {flag(cheats.fast_player)}  F5 skip  "
                f"F6 +1 life  F1 off", 20, y, GREEN, 18)
        else:
            canvas.text("P / Esc: pause     F1 (or 1): cheat mode "
                        "(for reviewers)", 20, y, GRAY, 20)

        label = f"Ghosts: {mode.name}"
        if any(ghost.angry for ghost in state.ghosts):
            label += "  (Blinky ANGRY)"
        canvas.text(label, canvas.width - 20, y,
                    RED if mode == GhostMode.CHASE else WHITE, 20, "right")

    def _draw_pause_menu(self, selected: int) -> None:
        """A panel over the game with the pause menu."""
        canvas = self.canvas
        center = canvas.width // 2
        canvas.fill_rect(center - 260, 230, 520, 250, PANEL)
        canvas.outline_rect(center - 260, 230, 520, 250, YELLOW)
        canvas.text("PAUSED", center, 255, YELLOW, 64, "center")
        for index, item in enumerate(PauseItem):
            y = 340 + index * 56
            if index == selected:
                canvas.fill_rect(center - 230, y - 8, 460, 46, HIGHLIGHT)
            canvas.text(item.value, center, y,
                        YELLOW if index == selected else WHITE, 36,
                        "center")
        canvas.text("Up / Down + Enter    P or Esc: resume", center, 440,
                    GRAY, 22, "center")
