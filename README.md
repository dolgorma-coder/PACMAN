# Pac-Man

A complete Pac-Man game in Python 3.10+, built with a modular architecture.
Mazes come from the assigned **A-Maze-ing** package (used as-is, with
`perfect=False`).

> **Status:** the game logic and a basic, working graphical interface
> (pygame-ce) are done, so every feature can be tried. The final
> polished interface and the platform packaging are still to do.

## Usage

The project is managed with [uv](https://docs.astral.sh/uv/) and
`pyproject.toml` (Python 3.10 or later).

```
make install                      # uv sync: creates .venv and installs everything
make run                          # uv run python pac-man.py config.json
uv run python pac-man.py my_config.json
```

The program takes exactly one argument: a JSON configuration file. Any error
is reported with a one-line message, never with a traceback.

Other rules: `make debug` (pdb), `make lint`, `make lint-strict`,
`make clean`. Add dependencies with `uv add <package>` (it updates
`pyproject.toml` and `uv.lock`; commit both).

## Configuration file

JSON with comments: lines starting with `#` or `//` are ignored. Unknown keys
are ignored. A missing or invalid value is replaced by its default (or clamped
to its range) and a warning is printed. Only a missing, unreadable or
syntactically broken file stops the program.

| Key | Default | Range | Meaning |
|---|---|---|---|
| `highscore_filename` | `highscores.json` | any path | Where the top 10 is saved |
| `lives` | 3 | 1 - 99 | Lives at the start |
| `points_per_pacgum` | 10 | 0 - 1 000 000 | Score of a pacgum |
| `points_per_super_pacgum` | 50 | 0 - 1 000 000 | Score of a super-pacgum |
| `points_per_ghost` | 200 | 0 - 1 000 000 | Score of an edible ghost |
| `seed` | 42 | 0 - 2^31-1 | Seed of the first maze (0 = random) |
| `level_max_time` | 90 | 10 - 3600 | Seconds per level |
| `super_pacgum_duration` | 8 | 1 - 60 | Seconds the ghosts stay edible |
| `ghost_respawn_delay` | 5 | 1 - 60 | Seconds an eaten ghost waits at home |
| `player_speed` | 8 | 1 - 20 | Cells per second |
| `ghost_speed` | 6 | 1 - 20 | Cells per second |
| `levels` | 10 levels | 1 - 100 | List of `{"width", "height", "seed"?}` |

Level sizes go from 10 to 60 cells. A level may define its own `seed`; the
global `seed` is given to the first level that has none, all the others are
random (0). With no valid `levels`, 10 default levels are used (15x15 growing
one cell every two levels). The `pacgum` key of the subject is not used:
pacgums fill every reachable corridor.

## Gameplay rules

* The player starts in the middle of the maze (the closest corridor cell, as
  the generator draws a "42" there), the 4 ghosts and the 4 super-pacgums are
  in the 4 corners, pacgums fill the other corridors.
* Movement is continuous: the player and the ghosts glide along the corridors
  at `player_speed` / `ghost_speed` cells per second, whatever the frame rate
  (the frame time is measured precisely and the window is synchronised with
  the screen refresh when possible). A direction pressed before a junction is
  kept and applied when the player gets there; the opposite direction turns
  around at once.
* A level is won when all the pacgums are eaten. Score and lives are kept
  between levels. The game is won after the last level.
* Touching a chasing ghost costs a life: the player and the ghosts go back to
  their start cells. Game over at 0 lives.
* A super-pacgum makes every ghost edible for `super_pacgum_duration`
  seconds: they turn around, run away, move slower and can be eaten
  (+`points_per_ghost`). An eaten ghost waits at its corner for
  `ghost_respawn_delay` seconds.
* **Time out:** the player loses a life and the timer restarts (the board is
  kept).

### Ghosts

As in the original game, the ghosts alternate between two phases (the
footer shows the current one): **scatter**, where each one heads to its own
corner, and **chase**, where each one hunts Pac-Man in its own way. The
rhythm is the one of the original first level: scatter 7 s, chase 20 s,
scatter 7 s, chase 20 s, scatter 5 s, chase 20 s, scatter 5 s, then chase
forever. It waits while the ghosts are edible and starts again after a lost
life. The ghosts turn around when the phase changes.

| Ghost | Chase target | Scatter corner |
|---|---|---|
| Blinky (red) | Pac-Man himself. "Angry" when 10 % of the pacgums or fewer are left: faster, and he chases even in scatter mode (white ring) | upper-right |
| Pinky (pink) | 4 cells ahead of Pac-Man. Original bug kept: facing up, also 4 cells to the left | upper-left |
| Inky (cyan) | The cell 2 ahead of Pac-Man (same bug), mirrored through Blinky: the vector Blinky to that cell, doubled | lower-right |
| Clyde (orange) | Pac-Man, but when closer than 8 cells he heads to his corner instead | lower-left |

At every cell a ghost picks the way with the shortest walk to its target. It
never turns back (except when the phase changes, when it is the only way, or
when a scatter ghost strays more than 4 steps from its corner), and ties are
broken in the original order: up, left, down, right. An edible ghost takes the
way that leads farthest from Pac-Man. The original game measures distances in
a straight line; our mazes are random, so the real walking distance is used
instead. The targets, and so the personalities, are the original ones. A
target that is a wall (or outside the maze) is replaced by the closest corridor
cell.

## Highscores

Stored in `highscore_filename` as `{"highscores": [{"name": "...", "score": N}]}`.

* Top 10, best first. With equal scores the older entry stays first.
* Names: 1 to 10 characters, ASCII letters, digits and spaces. An empty name
  becomes `PLAYER`. Scores: integers from 0 to 999 999 999.
* Loaded at start, saved when the player confirms the name after a game over
  or a victory. Leaving through the pause menu saves nothing.
* A missing, corrupted, oversized or unreadable file gives an empty table;
  invalid entries are skipped. Saving is atomic (temporary file, then
  rename), so a failed save never destroys the previous table.

## Controls

| Action | Keys |
|---|---|
| Move | Arrow keys or WASD |
| Pause / resume | P or Escape |
| Menus | Up / Down, Enter, Escape |
| Name entry | Letters, digits, space; Backspace; Enter |

### Cheat mode (for the peer review)

Press `F1` (or `1`) to turn the cheat mode on; the bottom bar then shows the
state of every cheat. `F2` to `F6` (or `2` to `6`) only work while it is on.
Turning the mode off clears all the switches. The number keys work only
during the game, because on the name screen digits are typed text.

| Keys | Effect |
|---|---|
| `F1` / `1` | Cheat mode on / off |
| `F2` / `2` | Invincible: ghosts and the timer cannot take lives |
| `F3` / `3` | Ghosts stop moving |
| `F4` / `4` | Player moves twice as fast |
| `F5` / `5` | Wins the current level |
| `F6` / `6` | +1 life |

## Architecture

```
pac-man.py           entry point: arguments, config, error handling
config.py            config file loading and validation
highscore_manager.py load / add / save the top 10
maze_loader.py       adapter to the A-Maze-ing package
level_builder.py     builds a level from a maze, creates the ghosts
ghost_modes.py       scatter / chase rhythm
ghost_ai.py          each ghost's target and next direction
game_engine.py       the rules (movement, collisions, lives, levels, timer)
app.py               screens, menus, name entry, highscore flow

ui_example/
  ui.py                window, main loop, screen choice
  ui_canvas.py         the only drawing code (pygame-ce)
  ui_input.py          keyboard -> Command / text (pygame-ce)
  ui_game_view.py      maze, items, entities, HUD, pause menu
  ui_menu_views.py     menu, highscores, instructions, end screen
  ui_theme.py          colors and sizes

models/
    config_models.py     configuration data classes and defaults
    entity_models.py     Direction, Position, Player, Ghost, exact_position
    highscore_models.py  name rules and HighscoreEntry
    maze_models.py       Maze (walls, movement, distance maps)
    level_models.py      Level: maze, spawn, ghost homes, pacgums
    game_state.py        GameState, GameStatus, Cheats
    app_models.py        Screen, Command, menu items, instruction text
```

### Interface

`ui.py` only connects the keyboard to `app.handle_command` / `app.handle_text`,
calls `app.update(dt)` every frame and draws `app.screen`. It has no game
rules. All the drawing goes through `ui_canvas.py` and all the keyboard
reading through `ui_input.py`, and they only use basic primitives (window,
rectangles, circles, lines, text, off-screen images, frame loop, key events).
Replacing the graphics library (for example by MLX) means rewriting only those
two modules.
