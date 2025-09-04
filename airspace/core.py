from typing import Set, Tuple, Dict

class Airspace:
    def __init__(self, width: int, height: int, time_horizon: int):
        """
        Initialize the airspace grid.

        :param width: number of columns (x-axis)
        :param height: number of rows (y-axis)
        :param time_horizon: maximum time steps to consider
        """
        self.width = width
        self.height = height
        self.time_horizon = time_horizon

        # Static obstacles: positions permanently blocked (x, y)
        self.static_obstacles: Set[Tuple[int, int]] = set()

        # Dynamic occupancy: mapping from time -> set of (x, y) occupied
        self.dynamic_occupancy: Dict[int, Set[Tuple[int, int]]] = {
            t: set() for t in range(time_horizon)
        }

    # ----------------- Validation helpers -----------------
    def _validate_position(self, x: int, y: int) -> None:
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise ValueError(f"Invalid position ({x}, {y}): out of bounds.")

    def _validate_time(self, t: int) -> None:
        if not (0 <= t < self.time_horizon):
            raise ValueError(f"Invalid time {t}: must be within 0-{self.time_horizon-1}.")

    # ----------------- Static obstacles -----------------
    def add_static_obstacle(self, x: int, y: int) -> None:
        self._validate_position(x, y)
        if (x, y) in self.static_obstacles:
            raise ValueError(f"Static obstacle already exists at ({x}, {y}).")
        self.static_obstacles.add((x, y))

    def remove_static_obstacle(self, x: int, y: int) -> None:
        self._validate_position(x, y)
        if (x, y) not in self.static_obstacles:
            raise ValueError(f"No static obstacle at ({x}, {y}) to remove.")
        self.static_obstacles.remove((x, y))

    # ----------------- Dynamic occupancy -----------------
    def add_dynamic_occupancy(self, x: int, y: int, t: int) -> None:
        self._validate_position(x, y)
        self._validate_time(t)
        if (x, y) in self.static_obstacles:
            raise ValueError(f"Cannot occupy ({x}, {y}, {t}): it is a static obstacle.")
        if (x, y) in self.dynamic_occupancy[t]:
            raise ValueError(f"Dynamic occupancy already exists at ({x}, {y}, {t}).")
        self.dynamic_occupancy[t].add((x, y))

    def remove_dynamic_occupancy(self, x: int, y: int, t: int) -> None:
        self._validate_position(x, y)
        self._validate_time(t)
        if (x, y) not in self.dynamic_occupancy[t]:
            raise ValueError(f"No dynamic occupancy at ({x}, {y}, {t}) to remove.")
        self.dynamic_occupancy[t].remove((x, y))

    # ----------------- Queries -----------------
    def is_occupied(self, x: int, y: int, t: int) -> bool:
        """Check if a position is occupied (static or dynamic) at time t."""
        self._validate_position(x, y)
        self._validate_time(t)
        return (x, y) in self.static_obstacles or (x, y) in self.dynamic_occupancy[t]

    def __repr__(self):
        return (f"Airspace(width={self.width}, height={self.height}, time_horizon={self.time_horizon}, "
                f"static_obstacles={len(self.static_obstacles)}, dynamic_occupancy={{...}})")
