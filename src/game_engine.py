"""Game engine: the rules of the game, with no graphics at all.

The UI calls `update(delta_time)` every frame and draws `engine.state`.

Movement is continuous along the corridors. Every entity has a cell
(`position`), a heading (`direction`) and a `move_progress` between 0 and 1
towards the next cell. When the progress reaches 1 the entity arrives at the
next cell and decides where to go next. Its real place is
`exact_position(entity)`: that is what the UI draws and what is used for
collisions. A frame is cut into small sub-steps, so two entities can never
cross each other without touching, even on a slow frame.

Rules chosen where the subject leaves freedom:
    * Time out: the player loses a life and the timer restarts (the board
      is kept as it is).
    * Losing a life: the player goes back to the spawn cell, all the ghosts
      go back home and the scatter / chase rhythm starts again.
    * Ghosts turn around when the scatter / chase phase changes and when a
      super-pacgum is eaten, as in the original game.
    * Blinky gets angry when few pacgums are left (see ANGRY_PELLET_RATIO).
    * If a later level cannot be generated, the game ends with a victory
      instead of crashing.
"""

from __future__ import annotations

import logging
import math
import random
from dataclasses import replace

from src.ghost_ai import GhostContext, choose_direction
from src.ghost_modes import ModeSchedule
from src.level_builder import build_level, create_ghosts
from src.maze_loader import load_maze
from src.models.config_models import GameConfig
from src.models.entity_models import (Direction, Ghost, Moving, Player,
                                      Position, current_tile, exact_position)
from src.models.game_state import GameState, GameStatus
from src.models.level_models import Level
from src.models.maze_models import MazeError

logger = logging.getLogger(__name__)

MAX_FRAME_TIME = 0.1          # Longer frames are cut, so nobody jumps ahead.
MAX_STEP_DISTANCE = 0.25      # Most cells two entities can approach per step.
COLLISION_DISTANCE = 0.6      # Closer than this (in cells) = they touch.
ARRIVAL_MARGIN = 1e-9         # Tolerance when an entity reaches a cell.
EDIBLE_SPEED_FACTOR = 0.6     # Edible ghosts are slower.
ANGRY_SPEED_FACTOR = 1.15     # Angry Blinky is faster.
ANGRY_PELLET_RATIO = 0.10     # Blinky is angry with this part of them left.
CHEAT_SPEED_FACTOR = 2.0      # Speed multiplier of the "fast player" cheat.
MAX_LIVES = 99
RETRIES = 3                   # Random mazes tried when a level fails.
ANGRY_GHOST = "blinky"
EATEN_SPEED_FACTOR = 1      # Eyes rush back home.


class GameEngine:
    """Runs one game, from the first level to victory or game over."""

    def __init__(self, config: GameConfig,
                 rng: random.Random | None = None) -> None:
        """Start a new game on the first level.

        Args:
            config: Game settings.
            rng: Random generator for the ghosts. A private one is used by
                default, because the maze generator reseeds the global one.

        Raises:
            MazeError: If the first level cannot be built.
        """
        self.config = config
        self.rng = rng if rng is not None else random.Random()
        self.modes = ModeSchedule()
        self._initial_pacgums = 0

        level = self._make_level(0)
        player = Player(spawn=level.spawn, lives=config.lives,
                        speed=config.player_speed)
        self.state = GameState(
            player=player,
            ghosts=create_ghosts(level, config.ghost_speed),
            level=level,
            level_index=0,
            level_count=len(config.levels),
            time_left=float(config.level_max_time),
        )
        self._start_level_bookkeeping()

    # -----------------------------------------------------------------
    # Controls (called by the UI)
    # -----------------------------------------------------------------

    def set_direction(self, direction: Direction) -> None:
        """Ask the player to turn. It is applied when the way is free."""
        if self._playing():
            self.state.player.next_direction = direction

    def toggle_pause(self) -> None:
        """Pause a running game, or resume a paused one."""
        status = self.state.status
        if status == GameStatus.PLAYING:
            self.state.status = GameStatus.PAUSED
        elif status == GameStatus.PAUSED:
            self.state.status = GameStatus.PLAYING

    def toggle_cheat_mode(self) -> None:
        """Turn the cheat mode on or off."""
        self.state.cheats.toggle_enabled()

    def toggle_invincible(self) -> None:
        """Cheat: ghosts and the timer cannot take lives."""
        self.state.cheats.toggle_invincible()

    def toggle_freeze_ghosts(self) -> None:
        """Cheat: ghosts stop moving."""
        self.state.cheats.toggle_freeze_ghosts()

    def toggle_fast_player(self) -> None:
        """Cheat: the player moves twice as fast."""
        self.state.cheats.toggle_fast_player()

    def skip_level(self) -> None:
        """Cheat: win the current level immediately."""
        if self.state.cheats.enabled and self._playing():
            self._complete_level()

    def add_life(self) -> None:
        """Cheat: give the player one extra life."""
        if self.state.cheats.enabled and self._playing():
            player = self.state.player
            player.lives = min(MAX_LIVES, player.lives + 1)

    # -----------------------------------------------------------------
    # Main update
    # -----------------------------------------------------------------

    def update(self, delta_time: float) -> None:
        """Advance the game.

        Args:
            delta_time: Seconds since the last update. Zero, negative or
                NaN values are ignored; huge values are cut.
        """
        if not self._playing() or not delta_time > 0:
            return
        dt = min(delta_time, MAX_FRAME_TIME)

        self.state.time_left -= dt
        if self.state.time_left <= 0:
            self._on_timeout()
            if not self._playing():
                return

        steps = max(1, math.ceil(self._closing_speed() * dt
                                 / MAX_STEP_DISTANCE))
        for _ in range(steps):
            self._advance(dt / steps)
            if not self._playing():
                return

    def _advance(self, dt: float) -> None:
        """Advance everything by a very short time."""
        for ghost in self.state.ghosts:
            ghost.update_timer(dt)
        self._update_modes(dt)
        self._move_player(dt)
        if self._playing():
            self._move_ghosts(dt)
        self._check_collisions()

    def _closing_speed(self) -> float:
        """Most cells per second two entities can approach each other."""
        ghost_speeds = [self._ghost_speed(ghost)
                        for ghost in self.state.ghosts
                        if not ghost.is_eaten]
        return self._player_speed() + max(ghost_speeds, default=0.0)

    # -----------------------------------------------------------------
    # Player
    # -----------------------------------------------------------------

    def _player_speed(self) -> float:
        """Player speed in cells per second, cheats included."""
        speed = self.state.player.speed
        if self.state.cheats.fast_player:
            speed *= CHEAT_SPEED_FACTOR
        return speed

    def _move_player(self, dt: float) -> None:
        """Move the player along its corridor for `dt` seconds."""
        player = self.state.player
        self._apply_turn_request()
        distance = self._player_speed() * dt
        while distance > 0 and player.direction != Direction.NONE:
            step = min(distance, 1.0 - player.move_progress)
            player.move_progress += step
            distance -= step
            if player.move_progress >= 1.0 - ARRIVAL_MARGIN:
                self._player_arrives()
                if not self._playing():
                    return

    def _apply_turn_request(self) -> None:
        """Start moving, or turn around, as soon as the player asks.

        Turning at a junction is done when arriving at it (see
        `_player_arrives`), using the requested direction as a buffer.
        """
        player = self.state.player
        wanted = player.next_direction
        if wanted in (Direction.NONE, player.direction):
            return
        if player.direction == Direction.NONE:
            if self.state.level.maze.can_move(player.position, wanted):
                player.direction = wanted
                player.facing = wanted
        elif wanted == player.direction.opposite:
            _reverse(player)
            player.facing = wanted

    def _player_arrives(self) -> None:
        """The player reached the next cell: eat, then choose the heading."""
        player = self.state.player
        player.position = player.position.moved(player.direction)
        player.move_progress = 0.0
        self._collect(player.position)
        if not self._playing():
            return
        maze = self.state.level.maze
        if maze.can_move(player.position, player.next_direction):
            player.direction = player.next_direction
        elif not maze.can_move(player.position, player.direction):
            player.direction = Direction.NONE        # A wall: stop.
        if player.direction != Direction.NONE:
            player.facing = player.direction

    def _collect(self, position: Position) -> None:
        """Eat what is in the cell: a pacgum or a super-pacgum."""
        state = self.state
        if state.level.eat_pacgum(position):
            state.player.add_score(self.config.points_per_pacgum)
            self._refresh_angry()
            if state.level.is_complete:
                self._complete_level()
        elif state.level.eat_super_pacgum(position):
            state.player.add_score(self.config.points_per_super_pacgum)
            for ghost in state.ghosts:
                ghost.make_edible(self.config.super_pacgum_duration)
                if not ghost.is_eaten:
                    _reverse(ghost)

    # -----------------------------------------------------------------
    # Ghosts
    # -----------------------------------------------------------------

    def _ghost_speed(self, ghost: Ghost) -> float:
        """Speed of a ghost in cells per second, in its current state."""
        if ghost.is_eaten:
            return ghost.speed * EATEN_SPEED_FACTOR
        if ghost.is_edible:
            return ghost.speed * EDIBLE_SPEED_FACTOR
        if ghost.angry:
            return ghost.speed * ANGRY_SPEED_FACTOR
        return ghost.speed

    def _update_modes(self, dt: float) -> None:
        """Advance the scatter / chase rhythm; ghosts turn around on change.

        The rhythm waits while the ghosts are edible.
        """
        if any(ghost.is_edible for ghost in self.state.ghosts):
            return
        if self.modes.update(dt):
            for ghost in self.state.ghosts:
                if not ghost.is_eaten:
                    _reverse(ghost)

    def _move_ghosts(self, dt: float) -> None:
        """Move every ghost along its corridor for `dt` seconds."""
        if self.state.cheats.freeze_ghosts:
            return
        for ghost in self.state.ghosts:
            if ghost.direction == Direction.NONE:
                ghost.direction = self._choose_direction(ghost)
            distance = self._ghost_speed(ghost) * dt
            while distance > 0 and ghost.direction != Direction.NONE:
                step = min(distance, 1.0 - ghost.move_progress)
                ghost.move_progress += step
                distance -= step
                if ghost.move_progress >= 1.0 - ARRIVAL_MARGIN:
                    ghost.position = ghost.position.moved(ghost.direction)
                    ghost.move_progress = 0.0
                    ghost.direction = self._choose_direction(ghost)

    def _choose_direction(self, ghost: Ghost) -> Direction:
        """Ask the ghost's personality where to go from its current cell."""
        state = self.state
        player_tile = current_tile(state.player)
        blinky = next((other for other in state.ghosts
                       if other.name == ANGRY_GHOST), None)
        context = GhostContext(
            maze=state.level.maze,
            player_tile=player_tile,
            player_facing=state.player.facing,
            blinky_tile=current_tile(blinky) if blinky else player_tile,
            mode=self.modes.mode,
        )
        return choose_direction(ghost, context, self.rng)

    def _refresh_angry(self) -> None:
        """Blinky is angry while few pacgums are left."""
        remaining = len(self.state.level.pacgums)
        angry = remaining <= self._initial_pacgums * ANGRY_PELLET_RATIO
        for ghost in self.state.ghosts:
            ghost.angry = angry and ghost.name == ANGRY_GHOST

    # -----------------------------------------------------------------
    # Collisions, lives and levels
    # -----------------------------------------------------------------

    def _check_collisions(self) -> bool:
        """Resolve the ghosts that touch the player.

        Returns:
            True if the player lost a life.
        """
        state = self.state
        if not self._playing():
            return False
        player_x, player_y = exact_position(state.player)
        for ghost in state.ghosts:
            if ghost.is_eaten:
                continue
            ghost_x, ghost_y = exact_position(ghost)
            if math.hypot(player_x - ghost_x,
                          player_y - ghost_y) >= COLLISION_DISTANCE:
                continue
            if ghost.is_edible:
                state.player.add_score(self.config.points_per_ghost)
                ghost.get_eaten(self.config.ghost_respawn_delay)
            elif not state.cheats.invincible:
                self._lose_life()
                return True
        return False

    def _lose_life(self) -> None:
        """Take a life: game over, or everybody goes back to the start."""
        player = self.state.player
        player.lose_life()
        if not player.is_alive:
            self.state.status = GameStatus.GAME_OVER
            return
        player.respawn()
        for ghost in self.state.ghosts:
            ghost.reset()
        self.modes.reset()

    def _on_timeout(self) -> None:
        """The level time is over: lose a life and restart the timer."""
        self.state.time_left = float(self.config.level_max_time)
        if not self.state.cheats.invincible:
            self._lose_life()

    def _complete_level(self) -> None:
        """Go to the next level, or win the game after the last one."""
        state = self.state
        next_index = state.level_index + 1
        if next_index >= state.level_count:
            state.status = GameStatus.VICTORY
            return
        try:
            level = self._make_level(next_index)
        except MazeError as error:
            logger.warning("Cannot build level %d (%s). Ending the game.",
                           next_index + 1, error)
            state.status = GameStatus.VICTORY
            return
        state.level = level
        state.level_index = next_index
        state.ghosts = create_ghosts(level, self.config.ghost_speed)
        state.player.start_level(level.spawn)
        state.time_left = float(self.config.level_max_time)
        self._start_level_bookkeeping()

    def _start_level_bookkeeping(self) -> None:
        """Reset what depends on the level: rhythm and angry mode."""
        self._initial_pacgums = len(self.state.level.pacgums)
        self.modes.reset()
        self._refresh_angry()

    def _make_level(self, index: int) -> Level:
        """Build level `index`.

        If its maze fails, random mazes of the same size are tried before
        giving up.

        Raises:
            MazeError: If every attempt fails.
        """
        if not 0 <= index < len(self.config.levels):
            raise MazeError("The configuration has no such level.")
        level_config = self.config.levels[index]
        attempts = [level_config] + [replace(level_config, seed=0)] * RETRIES
        error = MazeError("The level could not be built.")
        for attempt in attempts:
            try:
                return build_level(load_maze(attempt))
            except MazeError as caught:
                logger.debug("Level %d: %s", index + 1, caught)
                error = caught
        raise error

    def _playing(self) -> bool:
        """True while the game is running (not paused or finished)."""
        return self.state.status == GameStatus.PLAYING


def _reverse(mover: Moving) -> None:
    """Turn around on the spot, without moving.

    The mover keeps its exact place: it is now heading to the cell it was
    coming from, with the rest of the way to do.
    """
    if mover.direction == Direction.NONE:
        return
    mover.position = mover.position.moved(mover.direction)
    mover.direction = mover.direction.opposite
    mover.move_progress = 1.0 - mover.move_progress
