"""Maze data and movement queries.

Wall encoding (the same as the A-Maze-ing generator): every cell is an int
whose bits tell which sides of the cell have a wall.

    1 = north    2 = east    4 = south    8 = west

A cell with the four walls (15) is solid: it belongs to no corridor. The
generator uses such cells to draw the "42" in the middle of the maze.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.models.entity_models import Direction, Position

SOLID_CELL = 15
MOVE_DIRECTIONS = (Direction.UP, Direction.RIGHT,
                   Direction.DOWN, Direction.LEFT)
WALL_BIT = {
    Direction.UP: 1,
    Direction.RIGHT: 2,
    Direction.DOWN: 4,
    Direction.LEFT: 8,
}


class MazeError(Exception):
    """Raised when a maze cannot be generated or is not usable."""


class DistanceField:
    """Walking distances, in steps, from one cell to every cell of a maze.

    It is stored in a flat list (one number per cell), which makes it much
    faster to build than a dictionary of positions. Cells that cannot be
    reached have no distance.
    """

    def __init__(self, width: int, height: int, steps: list[int]) -> None:
        """Wrap the flat list of steps (-1 means "cannot be reached")."""
        self._width = width
        self._height = height
        self._steps = steps

    def get(self, position: Position, default: int) -> int:
        """Return the distance to `position`, or `default` if there is none.

        `default` is also returned for cells outside the maze.
        """
        if not (0 <= position.x < self._width
                and 0 <= position.y < self._height):
            return default
        steps = self._steps[position.y * self._width + position.x]
        return steps if steps >= 0 else default


@dataclass(frozen=True)
class Maze:
    """A grid of cells with walls between them.

    The open passages are worked out once, when the maze is created, so the
    movement queries (which the ghosts use all the time) are fast.

    Attributes:
        width: Number of columns.
        height: Number of rows.
        cells: Wall bits of each cell, indexed as `cells[y][x]`.
        walkable_cells: Every cell that is not solid, row by row.

    Raises:
        MazeError: On creation, if `cells` does not have the given size.
    """

    width: int
    height: int
    cells: tuple[tuple[int, ...], ...]
    walkable_cells: tuple[Position, ...] = field(
        init=False, repr=False, compare=False)
    _links: dict[Position, tuple[Direction, ...]] = field(
        init=False, repr=False, compare=False)
    _neighbours: tuple[tuple[int, ...], ...] = field(
        init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Check the grid size and work out the open passages."""
        if (len(self.cells) != self.height
                or any(len(row) != self.width for row in self.cells)):
            raise MazeError("The cells do not match the maze size.")
        links: dict[Position, tuple[Direction, ...]] = {}
        for y in range(self.height):
            for x in range(self.width):
                position = Position(x, y)
                if self.is_walkable(position):
                    links[position] = tuple(
                        direction for direction in MOVE_DIRECTIONS
                        if self._is_open(position, direction))
        # Same information as `links`, but as cell numbers (y * width + x),
        # which is what the fast distance search uses.
        neighbours: list[tuple[int, ...]] = [()] * (self.width * self.height)
        for position, directions in links.items():
            neighbours[self._index(position)] = tuple(
                self._index(position.moved(direction))
                for direction in directions)
        # The class is frozen: this is the way to set the computed fields.
        object.__setattr__(self, "_links", links)
        object.__setattr__(self, "walkable_cells", tuple(links))
        object.__setattr__(self, "_neighbours", tuple(neighbours))

    def _index(self, position: Position) -> int:
        """Return the number of a cell (row by row, from 0)."""
        return position.y * self.width + position.x

    def in_bounds(self, position: Position) -> bool:
        """True if `position` is inside the grid."""
        return 0 <= position.x < self.width and 0 <= position.y < self.height

    def is_walkable(self, position: Position) -> bool:
        """True if `position` is inside the grid and not a solid cell."""
        return (self.in_bounds(position)
                and self.cells[position.y][position.x] != SOLID_CELL)

    def has_wall(self, position: Position, direction: Direction) -> bool:
        """True if the cell has a wall on that side.

        Anything outside the grid counts as a wall.
        """
        if not self.in_bounds(position):
            return True
        bits = self.cells[position.y][position.x]
        return bool(bits & WALL_BIT.get(direction, 0))

    def _is_open(self, position: Position, direction: Direction) -> bool:
        """Work out if one step from `position` in `direction` is possible.

        Both cells must be walkable and the wall between them must be open
        seen from both sides, so an inconsistent maze can never let anybody
        walk through a wall.
        """
        target = position.moved(direction)
        if not (self.is_walkable(position) and self.is_walkable(target)):
            return False
        return not (self.has_wall(position, direction)
                    or self.has_wall(target, direction.opposite))

    def can_move(self, position: Position, direction: Direction) -> bool:
        """True if one step from `position` in `direction` is possible."""
        return direction in self._links.get(position, ())

    def open_directions(self, position: Position) -> list[Direction]:
        """Return the directions in which one can leave `position`."""
        return list(self._links.get(position, ()))

    def nearest_walkable(self, position: Position) -> Position:
        """Return the corridor cell closest (in a straight line) to a cell.

        Used to aim at cells that may be a wall or outside the maze. Ties
        are broken by row, then column, so the result is always the same.

        Raises:
            MazeError: If the maze has no corridor at all.
        """
        if position in self._links:
            return position
        if not self.walkable_cells:
            raise MazeError("The maze has no corridor.")
        return min(self.walkable_cells,
                   key=lambda cell: ((cell.x - position.x) ** 2
                                     + (cell.y - position.y) ** 2,
                                     cell.y, cell.x))

    def distance_field(self, start: Position) -> DistanceField:
        """Return the walking distance from `start` to every cell.

        It is a breadth-first search, done one "ring" of cells at a time.
        An unwalkable `start` gives a field where nothing can be reached.
        """
        steps = [-1] * (self.width * self.height)
        if start in self._links:
            first = self._index(start)
            steps[first] = 0
            ring = [first]
            distance = 0
            while ring:
                distance += 1
                next_ring = []
                for cell in ring:
                    for neighbour in self._neighbours[cell]:
                        if steps[neighbour] < 0:
                            steps[neighbour] = distance
                            next_ring.append(neighbour)
                ring = next_ring
        return DistanceField(self.width, self.height, steps)

    def distances_from(self, start: Position) -> dict[Position, int]:
        """Return the walking distance from `start` to each reachable cell.

        Same as `distance_field`, but as a dictionary (slower to build, so
        the ghosts use `distance_field`). Cells that cannot be reached are
        not in the result.
        """
        field = self.distance_field(start)
        return {cell: field.get(cell, -1) for cell in self.walkable_cells
                if field.get(cell, -1) >= 0}

    def reachable_from(self, start: Position) -> set[Position]:
        """Return every cell that can be reached from `start`."""
        return set(self.distances_from(start))
