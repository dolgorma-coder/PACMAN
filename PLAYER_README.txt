PAC-MAN (42 EDITION)
====================

HOW TO RUN
----------
  Linux:   ./pacman

Optional: pass a configuration file as the first argument.
  ./pacman my_config.json
If you pass none, the config.json shipped next to the game is used.

CONTROLS
--------
  Main menu        Up / Down: select      Enter: confirm
  In game          Arrow keys: move Pac-Man                       [CHECK]
  Pause            P or Esc: pause / resume      M: back to the menu
  Highscores       Enter or Esc: back
  Game over        Type your name (max 10 characters, letters, digits and
                   spaces), then Enter to save and go back to the menu

GOAL
----
Eat every pacgum in the maze without being caught by the ghosts. Super
pacgums make the ghosts edible for a few seconds; an eaten ghost returns
home as a pair of eyes. You have a limited number of lives and a time limit.

CHEAT MODE (for reviewers)
--------------------------
  F1 or 1    cheat mode on / off
  F2 or 2    invincible          F3 or 3    freeze ghosts
  F4 or 4    fast player         F5 or 5    skip level
  F6 or 6    extra life
  (F2 to F6 only work while the cheat mode is on)

CONFIGURATION (config.json)
---------------------------
Edit config.json with any text editor, then restart the game.

  [FILL IN: one line per field of config.json, with its meaning and
   its allowed values]

FILES
-----
  highscores.json    created in the folder you launch the game from
  assets/            images and fonts (do not move or delete)
