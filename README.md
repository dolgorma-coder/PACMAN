*This project has been created as part of the 42 curriculum by dzhambal, jaatif-a.*

![Project Banner](cover.jpg)

<div align="center">

# 🟡 Pac-Man — Ghosts! More ghosts!

**A Pac-Man game with random mazes, ghost personalities and a neon retro look.**

![Python](https://img.shields.io/badge/python-3.12%2B-blue?logo=python&logoColor=white)
![Pygame](https://img.shields.io/badge/graphics-pygame-green)
![Typing](https://img.shields.io/badge/typing-mypy-informational)
![Package](https://img.shields.io/badge/package-PyInstaller-orange)
![Status](https://img.shields.io/badge/42-curriculum-black)

</div>

---

## 📑 Table of contents

- [Description](#-description)
- [Instructions](#-instructions)
- [Configuration](#-configuration)
- [Highscore](#-highscore)
- [Maze Generation](#-maze-generation)
- [Implementation](#-implementation)
- [General Software Architecture](#-general-software-architecture)
- [Packaging and Distribution](#-packaging-and-distribution)
- [Project Management](#-project-management)
- [Resources](#-resources)

---

## 📖 Description

This project is a complete **Pac-Man** game written in Python. The player
moves through a maze, eats every pacgum to complete the level and avoids the
ghosts. The mazes are **randomly generated** by the A-Maze-ing package, so no
two games are the same.

The goal of the project is to build a full game with a clean separation
between **game rules**, **application logic** and **graphics**. The rules
know nothing about the screen, so the graphics library can be replaced
(for example by MiniLibX) by rewriting only a few modules. The game can also
be **packaged as a stand-alone build** and distributed from a public platform
(see [Packaging and Distribution](#-packaging-and-distribution)).

### ✨ Features

- 🧩 **Random mazes**, one per level, with an optional fixed seed.
- 👻 **Four ghosts with their own personality**, based on the original game:
  Blinky, Pinky, Inky and Clyde.
- 🔁 **Scatter / chase rhythm**: ghosts alternate between going to their
  corner and hunting the player.
- 🔵 **Super-pacgums**: ghosts turn blue and edible. A ghost that is eaten
  becomes a pair of **eyes**, runs home, and comes back still blue if the
  effect has not ended.
- 😡 **Angry Blinky**: when few pacgums are left he becomes faster and never
  stops chasing.
- 💀 **Death animation** that freezes the game while it plays.
- ⏱️ **Time limit per level**: running out of time costs a life.
- 🏆 **Persistent highscores** with name entry.
- ⏸️ **Pause screen** with resume and return to the main menu.
- 🕹️ **Cheat mode** for testing and demonstrations.
- 🎬 **Smooth continuous movement** along the corridors, not cell by cell.
- 📦 **Ready-to-install package** with its own short player guide.

---

## 🚀 Instructions

### Requirements

- Python **3.12**
- [`uv`](https://docs.astral.sh/uv/) (it creates the virtual environment and
  installs the dependencies)
- `pygame` (installed by `uv`) and the A-Maze-ing wheel
  (`mazegenerator-2.1.0-py3-none-any.whl`, included in the repository)
- A graphical environment (a display is needed to open the window)
- `zip`, only to build the distribution package

### Installation

#### To download the game and launch from a public platform (Itch.io)
https://pacmangame42.itch.io/pacman

```bash
git clone https://github.com/dolgorma-coder/PACMAN/tree/main
cd PACMAN
make install        # installs the wheel and syncs the dependencies with uv
```

### Run

```bash
make run                          # uses config.json
make run CONFIG=my_config.json    # uses another configuration file

# or, without make:
python3 pac-man.py [config.json]
```

The configuration file is optional: if none is given, the default
`config.json` is used.

### Other useful commands

| Command | What it does |
|---|---|
| `make debug` | Runs the game under `pdb` |
| `make lint` | `flake8` + `mypy` (standard options) |
| `make lint-strict` | `flake8` + `mypy --strict` |
| `make package` | Builds the distribution package in `dist/` |
| `make publish` | Builds the package and uploads it with `butler` (itch.io) |
| `make clean` | Removes caches, `build/`, `dist/` and the highscore file |

### 🎮 Controls

| Key | Action |
|---|---|
| `↑` `↓` `←` `→` / `W` `A` `S` `D` | Move (and navigate menus) |
| `Enter` | Confirm |
| `P` or `Esc` | Pause / resume |
| `M` *(while paused)* | Return to the main menu |
| `Backspace` | Erase a letter (name entry) |

### 🧪 Cheat mode

Press `F1` (or `1`) to enable the cheat mode, then:

| Key | Cheat |
|---|---|
| `F2` / `2` | Invincibility (ghosts and timer cannot take lives) |
| `F3` / `3` | Freeze the ghosts |
| `F4` / `4` | Double player speed |
| `F5` / `5` | Skip the current level |
| `F6` / `6` | Add one extra life |

The number keys exist for keyboards where the function keys need `Fn`. They
only work during a game, because on the name screen digits are text.

### 📜 Rules

- Eat **all the pacgums** to complete a level. Finish all the levels to win.
- **Super-pacgums** make the ghosts edible for a short time.
- Touching a normal ghost costs a **life**. Eating a blue ghost gives points.
- Each level has a **time limit**. When it ends you lose a life.
- The game is over when you have no lives left.

---

## ⚙️ Configuration

The game reads a configuration file at start-up. Every value that changes
the gameplay lives there, so the game can be tuned without touching the code.

- The file is the first (optional) argument: `python3 pac-man.py my.json`.
- Without an argument, the `config.json` of the repository is used. In the
  distribution package it is the `config.json` placed **next to the
  executable**, so players can edit it with any text editor.
- Relative paths inside the file (such as `highscore_filename`) are
  resolved from the folder of the game.
- An invalid file is reported with a clear error message and the game exits
  with code 1; it never shows a traceback.

> 📝 Fill in the real file format and default values of your project.

### General settings

| Key | Description | Default |
|---|---|---|
| `lives` | Lives at the start of the game | `<default>` |
| `player_speed` | Player speed, in cells per second | `<default>` |
| `ghost_speed` | Base ghost speed, in cells per second | `<default>` |
| `level_max_time` | Seconds available per level | `<default>` |
| `points_per_pacgum` | Score for a pacgum | `<default>` |
| `points_per_super_pacgum` | Score for a super-pacgum | `<default>` |
| `points_per_ghost` | Score for eating a ghost | `<default>` |
| `super_pacgum_duration` | Seconds the ghosts stay edible | `<default>` |
| `ghost_respawn_delay` | Seconds an eaten ghost waits at home | `<default>` |
| `highscore_filename` | File where the highscores are stored | `<default>` |
| `levels` | List of levels (see below) | `<default>` |

### Level settings

Every entry of `levels` describes the maze of one level:

| Key | Description |
|---|---|
| `seed` | Maze seed. `0` means a random maze every time |
| `<width / height>` | Size of the maze |

### Example

```json
{
  "lives": 3,
  "player_speed": 6.0,
  "ghost_speed": 5.0,
  "level_max_time": 120,
  "points_per_pacgum": 10,
  "points_per_super_pacgum": 50,
  "points_per_ghost": 200,
  "super_pacgum_duration": 8,
  "ghost_respawn_delay": 2,
  "highscore_filename": "highscores.json",
  "levels": [
    { "width": 15, "height": 15, "seed": 0 }
  ]
}
```

### Internal constants

Some values are not in the file because they are tuning of the rules and not
user settings. They are named constants at the top of `game_engine.py` and
`ghost_ai.py`:

| Constant | Meaning |
|---|---|
| `EDIBLE_SPEED_FACTOR` | Edible ghosts are slower |
| `EATEN_SPEED_FACTOR` | Eyes rush back home |
| `ANGRY_SPEED_FACTOR` | Angry Blinky is faster |
| `ANGRY_PELLET_RATIO` | Part of pacgums left that makes Blinky angry |
| `COLLISION_DISTANCE` | Distance (in cells) at which two entities touch |
| `DEATH_DURATION` | Length of the death animation in seconds |

---

## 🏆 Highscore

### How it works

1. The table is **loaded when the application starts** from the file set in
   `highscore_filename`. It is a plain JSON file:
   `{"highscores": [{"name": "Ana", "score": 1200}, ...]}`.
2. When a game ends (game over or victory) the **name entry screen** appears.
   The player types a name. Only allowed characters are accepted and the name
   has a maximum length (10 characters).
3. On `Enter` the score is added to the table, which keeps only the **top 10**,
   **sorted with the best score first**. With equal scores the older entry
   stays first. An empty name becomes a default one (`PLAYER`), and the score
   is kept inside the valid range.
4. The table is **saved to disk**. If saving fails, the game shows a message
   and keeps running.
5. The best score is shown in the HUD during the game and the whole table in
   the main menu and in the highscores screen.

### Why this design

- **Persistence in a plain file**, so scores survive between sessions without
  needing any other tool, and the file can be read or reset by hand.
- **Input is filtered** (allowed characters and maximum length) so a name can
  never break the file or the screen layout.
- **Loading and saving never crash the game**: a missing, damaged, wrongly
  structured or absurdly big file gives an empty (or partial) table, invalid
  entries are skipped one by one, and a failed save only shows a notice.
- **Safe saving**: the table is written to a temporary file and then moved
  over the real one, so a crash while saving cannot corrupt the existing
  scores.
- **No graphics in the logic**: `highscore_manager.py` only works with data.
  The UI just draws the table the `App` gives it.
- **Works in the package too**: the file is created in the folder of the game,
  never inside the read-only bundle.

---

## 🧱 Maze Generation

The mazes come from the **A-Maze-ing** package assigned to the project
(`mazegenerator`, shipped as the wheel `mazegenerator-2.1.0-py3-none-any.whl`
in the repository and installed by `make install`). The game does not build
mazes itself: it asks the package for one and turns the result into a
playable level.

```text
LevelConfig ──► load_maze() ──► Maze ──► build_level() ──► Level
 (size, seed)   (A-Maze-ing)   (walls)   (items, spawn)   (ready to play)
```

1. **`maze_loader.load_maze`** passes the level settings (size and seed) to
   the A-Maze-ing package and wraps the result in the project's `Maze` model.
   A `seed` of `0` gives a different maze every time. Any other value always
   gives the same maze.
2. **`Maze`** stores the walls in a grid. Each cell is a bit mask that says
   which sides have a wall, and it answers questions such as
   `can_move(position, direction)`, `open_directions(position)` or
   `distance_field(position)` (walking distance to every cell).
3. **`level_builder.build_level`** places the pacgums, the super-pacgums, the
   player spawn and the ghost homes on top of the maze.
4. **If a maze cannot be generated**, the engine tries random mazes of the same
   size a few times (`RETRIES`). If a later level still fails, the game ends
   with a victory instead of crashing. If the first level fails, the menu
   shows an error message.

> 📝 Add here how the package is imported and the options you pass to it.

---

## 🔧 Implementation

### Continuous movement

Entities do not jump from cell to cell. Each one has a cell (`position`), a
heading (`direction`) and a `move_progress` from 0 to 1 towards the next cell.
When the progress reaches 1 the entity arrives and decides where to go next.
Its real place is `exact_position(entity)`, which is what is drawn and what is
used for collisions.

To avoid two entities crossing each other without touching on a slow frame,
every frame is **cut into small sub-steps** (`MAX_STEP_DISTANCE`), and long
frames are capped (`MAX_FRAME_TIME`).

### Ghost AI

Each ghost has a *target cell* that depends on its personality, as in the
original game. All targets are in cells, and "ahead of Pac-Man" means ahead
in the direction he is facing.

| Ghost | Target while chasing | Scatter corner |
|---|---|---|
| 🔴 **Blinky** | Pac-Man directly. Angry when few pacgums are left | Upper-right |
| 🌸 **Pinky** | 4 cells ahead of Pac-Man (with the original *up* bug) | Upper-left |
| 🩵 **Inky** | Doubles the vector from Blinky to 2 cells ahead of Pac-Man | Lower-right |
| 🟠 **Clyde** | Pac-Man, but runs to his corner when closer than 8 cells | Lower-left |

Every time a ghost reaches a cell it picks a direction:

- It **never turns back**, unless there is no other way. The only exception is
  a scatter ghost that strays too far from its corner.
- An **edible** ghost takes the way that leads farthest from the player.
- **Eyes** (eaten ghosts) take the shortest way home.
- Any other ghost takes the way with the **shortest walking distance** to its
  target. Ties are broken in the order up, left, down, right.

**Adaptation:** the original game compares straight-line distances, which only
works in its hand-made maze. Because our mazes are random, the ghosts use the
real **walking distance** instead. The targets, and so the personalities, are
the original ones.

### Ghost states

```mermaid
stateDiagram-v2
    [*] --> CHASING
    CHASING --> EDIBLE: super-pacgum eaten
    EDIBLE --> CHASING: effect ends
    EDIBLE --> EATEN: eaten by the player
    EATEN --> EDIBLE: back home, effect still active
    EATEN --> CHASING: back home, effect over
```

An eaten ghost keeps walking from where it was eaten, now as eyes, at higher
speed. Its respawn delay only starts counting once it is back home, and the
super-pacgum effect keeps running meanwhile.

### Scatter / chase rhythm

`ModeSchedule` alternates the `SCATTER` and `CHASE` phases. Ghosts turn around
when the phase changes and when a super-pacgum is eaten. The rhythm waits
while any ghost is edible, and starts again after a life is lost.

### Lives and death

When the player is touched by a ghost (or the level time ends), the engine
starts a **death animation** and freezes everything else. The renderer draws
the animation frame from the engine's progress, so logic and graphics always
stay in sync. When it ends, the game is over (no lives left) or everybody goes
back to the start.

### Rendering

- The sprites are cut from sprite sheets and **cached**, so nothing is sliced
  twice.
- The tile size is the **biggest whole number (up to 32 px)** that makes the
  maze fit the window. Sprites (and the eyes of eaten ghosts) are scaled once
  with a nearest-neighbour function that only reads and writes single pixels,
  so it does not depend on any library-specific scaling.
- Walls use an **autotiling** pipeline that picks the right tile (straight,
  corner, junction...) from the bit mask of each cell, in two passes: the base
  wall, then the connection caps and the outer border.
- The drawing code is split into small functions (maze, wall caps, borders,
  player, one ghost, HUD, lives, pause), each one with a single job.

### Quality

- Complete **type hints** and PEP 257 docstrings (Google style, with `Args`,
  `Returns` and `Raises`) in every module.
- The code is checked with `flake8` and `mypy` (`make lint`, and the stricter
  `make lint-strict`). Return values coming from untyped libraries are
  converted explicitly (for example `int(image.get_height())`), so no
  `# type: ignore` is needed.
- No input can crash the application: invalid keys are ignored, every file
  or generation error is handled, and the entry point has a last safety net so
  the player never sees a traceback.

---

## 🏗️ General Software Architecture

The project is split in layers. Each one only knows the layers below it.

```mermaid
flowchart TD
    ENTRY["pac-man.py<br/>entry point"]
    PATHS["paths.py<br/>default config · game folder"]
    UI["UI layer<br/>ui.py · ui_canvas · ui_game_view<br/>ui_menu_views · ui_input · renderer"]
    APP["Application logic<br/>app.py"]
    ENGINE["Game engine<br/>game_engine.py"]
    AI["Ghost behaviour<br/>ghost_ai.py · ghost_modes.py"]
    BUILD["Level creation<br/>maze_loader.py · level_builder.py"]
    SCORE["highscore_manager.py"]
    MODELS["Models<br/>entity · maze · level · game_state<br/>config · highscore · app"]

    ENTRY --> PATHS
    ENTRY --> UI
    UI --> APP
    APP --> ENGINE
    APP --> SCORE
    ENGINE --> AI
    ENGINE --> BUILD
    AI --> MODELS
    ENGINE --> MODELS
    BUILD --> MODELS
    SCORE --> MODELS
```

### Project structure

```text
.
├── README.md
├── PLAYER_README.txt        # Short guide shipped inside the package
├── Makefile                 # install, run, lint, package, publish
├── pyproject.toml           # Metadata, dependencies, tool settings
├── uv.lock
├── pac-man.py               # Entry point
├── pacman.spec              # PyInstaller packaging spec
├── config.json              # Default configuration
├── mazegenerator-2.1.0-py3-none-any.whl   # A-Maze-ing package
├── assets/                  # Sprites, fonts and images
└── src/
    ├── app.py               # Screens and commands (no graphics)
    ├── config.py            # Loads and validates the config file
    ├── game_engine.py       # Game rules (no graphics)
    ├── ghost_ai.py          # Ghost personalities and pathing
    ├── ghost_modes.py       # Scatter / chase schedule
    ├── level_builder.py     # Builds levels and ghosts
    ├── maze_loader.py       # Connects to the A-Maze-ing package
    ├── highscore_manager.py # Load, add and save highscores
    ├── paths.py             # Default config and game folder (source / build)
    ├── renderer.py          # Sprites, autotiling, entity drawing
    ├── models/
    │   ├── app_models.py        # Screen, Command, MenuItem
    │   ├── config_models.py     # GameConfig, level settings
    │   ├── entity_models.py     # Direction, Position, Player, Ghost
    │   ├── game_state.py        # GameState, GameStatus, cheats
    │   ├── level_models.py      # Level (items on the maze)
    │   ├── maze_models.py       # Maze, distance fields, MazeError
    │   └── highscore_models.py  # Highscore entry, name rules
    └── UI/
        ├── ui.py            # Window and main loop
        ├── ui_canvas.py     # The only drawing layer
        ├── ui_game_view.py  # HUD, maze and pause screen
        ├── ui_menu_views.py # Menu, highscores, instructions, game end
        ├── ui_input.py      # Keyboard to commands
        └── ui_theme.py      # Colors, sizes, constants
```

### Main classes

| Class | Module | Role |
|---|---|---|
| `App` | `app.py` | Which screen is shown and what each command does |
| `GameEngine` | `game_engine.py` | Runs one game: movement, collisions, lives, levels |
| `GameState` | `models/game_state.py` | Everything the UI needs to draw a game |
| `Player` | `models/entity_models.py` | Position, lives, score, death animation |
| `Ghost` | `models/entity_models.py` | Position, state (`CHASING` / `EDIBLE` / `EATEN`), timers |
| `GhostContext` | `ghost_ai.py` | What a ghost knows when it chooses a direction |
| `ModeSchedule` | `ghost_modes.py` | Scatter / chase timing |
| `Maze` | `models/maze_models.py` | Walls, open directions, walking distances |
| `Level` | `models/level_models.py` | Maze plus pacgums, super-pacgums and spawn |
| `GameRenderer` | `renderer.py` | Draws the maze, the player and the ghosts |
| `Canvas` | `ui_canvas.py` | Window and drawing primitives |
| `GameView` | `ui_game_view.py` | HUD, lives row and pause overlay |
| `Ui` | `ui.py` | Connects keyboard, `App` and drawing |

### Design rules

- 🧠 **The game logic has no graphics.** `GameEngine` and `App` can be tested
  without opening a window. The UI calls `update(delta_time)` every frame and
  draws what it finds in the state.
- 🎨 **All drawing goes through `Canvas`.** To change the graphics library
  only `ui_canvas.py`, `ui_input.py` and the low-level part of `renderer.py`
  have to be rewritten. The game view and the menu views contain no graphics
  library imports.
- 💉 **Dependencies are injected.** The random generator of the ghosts can be
  passed to the engine, so tests can make it predictable.
- 🧊 **Small immutable types** (`Position`, `GhostContext`) are frozen
  dataclasses, so they are safe to share and to use as dictionary keys.
- 📦 **Packaging concerns live in one place.** Everything that depends on
  whether the game runs from the sources or from a build (default config
  file, working folder) is in `src/paths.py`.

---

## 📦 Packaging and Distribution

The game is delivered as a stand-alone, free and unlisted build, so it can be
installed and launched without Python or `uv` on the player's machine.

### Build

```bash
make package        # runs PyInstaller with pacman.spec and zips the result
```

The packaging script is `pacman.spec` (a PyInstaller spec) driven by the
`Makefile`. It produces `dist/pacman-linux.zip`. The spec bundles the
`assets/` folder (with the same layout as in the source tree) and the
`mazegenerator` package. `make package` then copies `config.json` and
`PLAYER_README.txt` next to the executable, so the player can read and edit
them.

```text
pacman/
├── pacman              # the executable
├── config.json         # editable configuration
├── PLAYER_README.txt   # controls, options and configuration
└── _internal/          # Python runtime, libraries and assets
```

The build is **per operating system**: PyInstaller does not cross-compile, so
the Linux package is built on Linux, a Windows one would be built on Windows.

### What changes when the game is packaged

- `pac-man.py` accepts **no argument**: it then loads the `config.json` next
  to the executable.
- The folder of the executable becomes the **working directory**, so
  `highscores.json` and any relative path of the configuration end up next to
  the game, wherever it was launched from.
- Both rules are implemented in `src/paths.py` and do nothing when the game is
  run from the sources.

### Publishing (itch.io)

1. Create the project with **Kind: Downloadable**, **Pricing: No payments**
   and **Visibility: Restricted** (or Draft), so it is free but unlisted.
2. Upload `dist/pacman-linux.zip` from the web page of the project and tick
   the **Linux** platform, **or** push it with
   [`butler`](https://itch.io/docs/butler/):
   `make publish ITCH_TARGET=<user>/<project>`.
3. Share the password or access keys of the restricted page with the
   reviewers.

### Regenerating the package

From a clean clone:

```bash
git clone https://github.com/dolgorma-coder/PACMAN/tree/main && cd PACMAN
make install
make package        # → dist/pacman-linux.zip
```

To check the result, unzip it in another folder and run `./pacman/pacman`.

---

## 📋 Project Management

> 📝 Adapt this section to how the team really worked.

- **Team:** `dzhambal`, `jaatif-a`
- **Organisation:** the work was split by layer (game rules and ghost AI,
  application logic and highscores, graphics and assets).
- **Tools:** Git with feature branches and code reviews, a shared task board,
  and regular meetings to agree on interfaces between modules.
- **Workflow:** the models and the interfaces between layers were defined
  first, so every part could be developed and tested independently. At the end,
  a clean-up pass added type hints and docstrings everywhere, and the
  packaging was set up and checked from a clean clone.

📂 **Project management directory:** [`./project-management`](./project-management)

---

## 📚 Resources

### References

- [The Pac-Man Dossier](https://pacman.holenet.info/) — the reference on the
  original ghost behaviour (targets, scatter and chase, bugs).
- [Pygame documentation](https://www.pygame.org/docs/)
- [MiniLibX documentation (42 Docs)](https://harm-smits.github.io/42docs/libs/minilibx)
- [Python documentation](https://docs.python.org/3/) — `dataclasses`, `enum`,
  `typing`, `pathlib`
- [PEP 8](https://peps.python.org/pep-0008/),
  [PEP 257](https://peps.python.org/pep-0257/) and
  [PEP 484](https://peps.python.org/pep-0484/) — style, docstrings and type
  hints
- [mypy documentation](https://mypy.readthedocs.io/) and
  [flake8 documentation](https://flake8.pycqa.org/)
- [uv documentation](https://docs.astral.sh/uv/) — environments and
  dependencies
- [PyInstaller documentation](https://pyinstaller.org/) — spec files, data
  files and the frozen application
- [itch.io creator docs](https://itch.io/docs/creators/) and
  [butler](https://itch.io/docs/butler/) — publishing a build
- [Game Programming Patterns](https://gameprogrammingpatterns.com/) — game
  loop and state patterns
- [Pac-Man on Wikipedia](https://en.wikipedia.org/wiki/Pac-Man)

### 🤖 Use of AI

AI (Claude) was used as a programming assistant. Every suggestion was read,
tested and adapted by the team, who understand and can explain all of the code.

| Task | How AI helped |
|---|---|
| Ghost respawn | Designed the edible state that survives being eaten, and the *eyes* that return home before respawning |
| Death animation | Moved the animation timing into the engine so the logic and the graphics stay in sync |
| Pause screen | Integrated the pause image and the `P` / `Esc` / `M` controls |
| Graphics portability | Replaced `smoothscale` with a cached nearest-neighbour scaler that does not depend on pygame |
| Code review | Found drawing bugs such as leftover sprites drawn twice, eye sprites that were never loaded (so they were not rescaled), and an undefined variable in the menu button fallback |
| Code quality | Added type hints and PEP 257 docstrings, split long drawing functions into small ones, and fixed `flake8` / `mypy` errors in the renderer, the game view and the menu views |
| Packaging | Helped write the PyInstaller spec, the `package` / `publish` targets of the `Makefile`, the `paths.py` helper and the in-package player guide, and explained how to publish on itch.io |
| Documentation | Helped write and format this README |

AI was **not** used to take design decisions about the project requirements,
which were made by the team.

> 📝 Edit the table so it matches exactly what your team used AI for.

---

<div align="center">

Made with 💛 and too many ghosts.

</div>
