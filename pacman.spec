# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Pac-Man (42 Edition) package.

Build with ``make package``. The result is the ``dist/pacman`` folder.
"""

from PyInstaller.utils.hooks import collect_submodules

a = Analysis(
    ["pac-man.py"],
    pathex=["."],
    # config.json and PLAYER_README.txt are copied next to the executable
    # by `make package`, so the player can see and edit them.
    datas=[("assets", "assets")],
    hiddenimports=collect_submodules("mazegenerator"),
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="pacman",
    console=False,  # set to True to see errors while testing the build
)
coll = COLLECT(exe, a.binaries, a.datas, name="pacman")
