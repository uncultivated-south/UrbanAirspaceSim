"""
UrbanAirspaceSim - Airspace Module

This module provides the core airspace representation and management functionality
for the urban airspace simulation system. It handles grid-based airspace with
time-dependent cell states and provides standardized interfaces for other modules.
"""

from typing import Dict, List, Tuple, Optional, Set, Any
from enum import Enum
from dataclasses import dataclass, field
from copy import deepcopy
import json


class CellState(Enum):
    """Enumeration for airspace cell states."""
    OPEN = '.'           # Open airspace
    STATIC_OBSTACLE = '#'  # Static obstacles (buildings)
    DYNAMIC_OBSTACLE = '*' # Dynamic obstacles (assigned paths)


@dataclass(frozen=True)
class Position:
    """Immutable position representation with validation."""
    x: int
    y: int
    
    def __post_init__(self):
        if not isinstance(self.x, int) or not isinstance(self.y, int):
            raise TypeError("Position coordinates must be integers")
        if self.x < 0 or self.y < 0:
            raise ValueError("Position coordinates must be non-negative")
    
    def __str__(self) -> str:
        return f"({self.x}, {self.y})"
    
    def manhattan_distance(self, other: 'Position') -> int:
        """Calculate Manhattan distance to another position."""
        if not isinstance(other, Position):
            raise TypeError("Can only calculate distance to another Position")
        return abs(self.x - other.x) + abs(self.y - other.y)


@dataclass
class CellInfo:
    """Information about a specific cell at a specific time."""
    position: Position
    state: CellState
    timestamp: int
    agent_id: Optional[str] = None  # ID of agent occupying this cell (if dynamic obstacle)
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional cell information
    
    def __post_init__(self):
        if not isinstance(self.timestamp, int) or self.timestamp < 0:
            raise ValueError("Timestamp must be a non-negative integer")
        if not isinstance(self.state, CellState):
            raise TypeError("State must be a CellState enum value")
        if not isinstance(self.position, Position):
            raise TypeError("Position must be a Position instance")


class AirspaceValidationError(Exception):
    """Custom exception for airspace validation errors."""
    pass


class Airspace:
    """
    Time-dependent grid-based airspace representation.
    
    This class manages the airspace grid with time-dependent cell states,
    providing methods for querying, updating, and validating airspace
    configurations.
    """
    
    def __init__(self, width: int, height: int, max_time: int = 1000):
        """
        Initialize airspace grid.
        
        Args:
            width: Grid width (number of columns)
            height: Grid height (number of rows) 
            max_time: Maximum simulation time steps
            
        Raises:
            ValueError: If dimensions are invalid
        """
        if not isinstance(width, int) or not isinstance(height, int):
            raise TypeError("Width and height must be integers")
        if width <= 0 or height <= 0:
            raise ValueError("Width and height must be positive")
        if not isinstance(max_time, int) or max_time <= 0:
            raise ValueError("Max time must be a positive integer")
            
        self._width = width
        self._height = height
        self._max_time = max_time
        
        # Time-dependent grid: {timestamp: {position: CellInfo}}
        self._grid: Dict[int, Dict[Position, CellInfo]] = {}
        
        # Initialize all cells as open at time 0
        self._grid[0] = {}
        for x in range(width):
            for y in range(height):
                pos = Position(x, y)
                self._grid[0][pos] = CellInfo(
                    position=pos,
                    state=CellState.OPEN,
                    timestamp=0
                )
        
        # Track which cells are static obstacles (immutable across time)
        self._static_obstacles: Set[Position] = set()
    
    @property
    def width(self) -> int:
        """Get airspace width."""
        return self._width
    
    @property
    def height(self) -> int:
        """Get airspace height."""
        return self._height
    
    @property
    def max_time(self) -> int:
        """Get maximum simulation time."""
        return self._max_time
    
    def _validate_position(self, position: Position) -> None:
        """Validate that position is within grid bounds."""
        if position.x >= self._width or position.y >= self._height:
            raise AirspaceValidationError(
                f"Position {position} is outside grid bounds ({self._width}x{self._height})"
            )
    
    def _validate_timestamp(self, timestamp: int) -> None:
        """Validate timestamp is within simulation bounds."""
        if not isinstance(timestamp, int) or timestamp < 0:
            raise ValueError("Timestamp must be a non-negative integer")
        if timestamp > self._max_time:
            raise ValueError(f"Timestamp {timestamp} exceeds maximum time {self._max_time}")
    
    def _ensure_time_exists(self, timestamp: int) -> None:
        """Ensure grid state exists for given timestamp."""
        if timestamp not in self._grid:
            # Copy state from previous timestamp
            prev_time = max(t for t in self._grid.keys() if t < timestamp)
            self._grid[timestamp] = deepcopy(self._grid[prev_time])
            # Update timestamps in copied cells
            for cell_info in self._grid[timestamp].values():
                object.__setattr__(cell_info, 'timestamp', timestamp)
    
    def get_cell_state(self, position: Position, timestamp: int = 0) -> CellState:
        """
        Get the state of a cell at a specific time.
        
        Args:
            position: Grid position
            timestamp: Time step
            
        Returns:
            CellState of the specified cell
            
        Raises:
            AirspaceValidationError: If position is invalid
            ValueError: If timestamp is invalid
        """
        self._validate_position(position)
        self._validate_timestamp(timestamp)
        
        if timestamp not in self._grid:
            # Find the latest available state
            available_times = [t for t in self._grid.keys() if t <= timestamp]
            if not available_times:
                raise ValueError(f"No grid state available for timestamp {timestamp}")
            timestamp = max(available_times)
        
        return self._grid[timestamp][position].state
    
    def get_cell_info(self, position: Position, timestamp: int = 0) -> CellInfo:
        """
        Get complete information about a cell at a specific time.
        
        Args:
            position: Grid position
            timestamp: Time step
            
        Returns:
            CellInfo object with complete cell information
        """
        self._validate_position(position)
        self._validate_timestamp(timestamp)
        
        if timestamp not in self._grid:
            available_times = [t for t in self._grid.keys() if t <= timestamp]
            if not available_times:
                raise ValueError(f"No grid state available for timestamp {timestamp}")
            timestamp = max(available_times)
        
        return deepcopy(self._grid[timestamp][position])
    
    def set_cell_state(self, position: Position, state: CellState, 
                      timestamp: int = 0, agent_id: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Set the state of a cell at a specific time.
        
        Args:
            position: Grid position
            state: New cell state
            timestamp: Time step
            agent_id: ID of agent (if dynamic obstacle)
            metadata: Additional cell metadata
            
        Raises:
            AirspaceValidationError: If modification violates constraints
        """
        self._validate_position(position)
        self._validate_timestamp(timestamp)
        
        if not isinstance(state, CellState):
            raise TypeError("State must be a CellState enum value")
        
        # Check if trying to modify a static obstacle
        if position in self._static_obstacles and state != CellState.STATIC_OBSTACLE:
            raise AirspaceValidationError(
                f"Cannot change static obstacle at {position}"
            )
        
        # Ensure timestamp exists in grid
        self._ensure_time_exists(timestamp)
        
        # Update cell information
        self._grid[timestamp][position] = CellInfo(
            position=position,
            state=state,
            timestamp=timestamp,
            agent_id=agent_id,
            metadata=metadata or {}
        )
        
        # Track static obstacles
        if state == CellState.STATIC_OBSTACLE:
            self._static_obstacles.add(position)
    
    def add_static_obstacle(self, position: Position) -> None:
        """
        Add a permanent static obstacle (e.g., building).
        
        Args:
            position: Grid position for obstacle
        """
        self._validate_position(position)
        
        # Set as static obstacle across all time steps
        for timestamp in self._grid.keys():
            self._grid[timestamp][position] = CellInfo(
                position=position,
                state=CellState.STATIC_OBSTACLE,
                timestamp=timestamp
            )
        
        self._static_obstacles.add(position)
    
    def add_dynamic_path(self, path: List[Tuple[Position, int]], agent_id: str) -> None:
        """
        Add a dynamic path as obstacles (e.g., assigned aircraft path).
        
        Args:
            path: List of (position, timestamp) tuples defining the path
            agent_id: ID of the agent using this path
            
        Raises:
            AirspaceValidationError: If path conflicts with static obstacles
        """
        if not isinstance(agent_id, str) or not agent_id:
            raise ValueError("Agent ID must be a non-empty string")
        
        if not isinstance(path, list) or not path:
            raise ValueError("Path must be a non-empty list")
        
        # Validate entire path first
        for pos, timestamp in path:
            if not isinstance(pos, Position):
                raise TypeError("Path positions must be Position instances")
            self._validate_position(pos)
            self._validate_timestamp(timestamp)
            
            if pos in self._static_obstacles:
                raise AirspaceValidationError(
                    f"Path conflicts with static obstacle at {pos}"
                )
        
        # Apply path to grid
        for pos, timestamp in path:
            self._ensure_time_exists(timestamp)
            
            # Check for conflicts with existing dynamic obstacles
            current_cell = self._grid[timestamp][pos]
            if (current_cell.state == CellState.DYNAMIC_OBSTACLE and 
                current_cell.agent_id != agent_id):
                raise AirspaceValidationError(
                    f"Path conflict at {pos} at time {timestamp} with agent {current_cell.agent_id}"
                )
            
            self.set_cell_state(pos, CellState.DYNAMIC_OBSTACLE, timestamp, agent_id)
    
    def remove_dynamic_path(self, agent_id: str) -> None:
        """
        Remove all dynamic obstacles created by a specific agent.
        
        Args:
            agent_id: ID of the agent whose path to remove
        """
        if not isinstance(agent_id, str) or not agent_id:
            raise ValueError("Agent ID must be a non-empty string")
        
        for timestamp in self._grid.keys():
            for pos, cell_info in self._grid[timestamp].items():
                if (cell_info.state == CellState.DYNAMIC_OBSTACLE and 
                    cell_info.agent_id == agent_id):
                    self.set_cell_state(pos, CellState.OPEN, timestamp)
    
    def get_neighbors(self, position: Position) -> List[Position]:
        """
        Get valid neighboring positions (4-connected grid).
        
        Args:
            position: Center position
            
        Returns:
            List of valid neighboring positions
        """
        self._validate_position(position)
        
        neighbors = []
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # N, E, S, W
        
        for dx, dy in directions:
            new_x, new_y = position.x + dx, position.y + dy
            if 0 <= new_x < self._width and 0 <= new_y < self._height:
                neighbors.append(Position(new_x, new_y))
        
        return neighbors
    
    def is_free(self, position: Position, timestamp: int = 0) -> bool:
        """
        Check if a cell is free (open) at a specific time.
        
        Args:
            position: Grid position
            timestamp: Time step
            
        Returns:
            True if cell is open, False otherwise
        """
        return self.get_cell_state(position, timestamp) == CellState.OPEN
    
    def get_grid_snapshot(self, timestamp: int = 0) -> Dict[Position, CellState]:
        """
        Get a snapshot of the entire grid at a specific time.
        
        Args:
            timestamp: Time step
            
        Returns:
            Dictionary mapping positions to cell states
        """
        self._validate_timestamp(timestamp)
        
        if timestamp not in self._grid:
            available_times = [t for t in self._grid.keys() if t <= timestamp]
            if not available_times:
                raise ValueError(f"No grid state available for timestamp {timestamp}")
            timestamp = max(available_times)
        
        return {pos: cell_info.state for pos, cell_info in self._grid[timestamp].items()}
    
    def to_string(self, timestamp: int = 0) -> str:
        """
        Generate a string representation of the grid at a specific time.
        
        Args:
            timestamp: Time step
            
        Returns:
            String representation of the grid
        """
        snapshot = self.get_grid_snapshot(timestamp)
        
        lines = []
        lines.append(f"Airspace Grid at t={timestamp} ({self._width}x{self._height})")
        lines.append("+" + "-" * self._width + "+")
        
        for y in range(self._height - 1, -1, -1):  # Top to bottom
            line = "|"
            for x in range(self._width):
                pos = Position(x, y)
                line += snapshot[pos].value
            line += "|"
            lines.append(line)
        
        lines.append("+" + "-" * self._width + "+")
        return "\n".join(lines)
    
    def export_config(self) -> Dict[str, Any]:
        """
        Export airspace configuration for serialization.
        
        Returns:
            Dictionary containing airspace configuration
        """
        config = {
            "width": self._width,
            "height": self._height,
            "max_time": self._max_time,
            "static_obstacles": [(pos.x, pos.y) for pos in self._static_obstacles],
            "timestamps": list(self._grid.keys())
        }
        return config
    
    def import_config(self, config: Dict[str, Any]) -> None:
        """
        Import airspace configuration (for loading saved states).
        
        Args:
            config: Configuration dictionary
            
        Raises:
            ValueError: If configuration is invalid
        """
        required_keys = ["width", "height", "max_time", "static_obstacles"]
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required configuration key: {key}")
        
        # Validate and set basic parameters
        if config["width"] != self._width or config["height"] != self._height:
            raise ValueError("Grid dimensions don't match current airspace")
        
        # Import static obstacles
        for x, y in config["static_obstacles"]:
            self.add_static_obstacle(Position(x, y))


# Test Example and Demonstration
def run_airspace_tests():
    """Comprehensive test suite for the Airspace module."""
    
    print("=" * 50)
    print("URBANAIRSPACESIM - AIRSPACE MODULE TESTS")
    print("=" * 50)
    
    # Test 1: Basic Airspace Creation
    print("\n1. Testing Basic Airspace Creation...")
    try:
        airspace = Airspace(5, 5, 100)
        print(f"✓ Created {airspace.width}x{airspace.height} airspace")
        print(f"✓ Max simulation time: {airspace.max_time}")
    except Exception as e:
        print(f"✗ Failed to create airspace: {e}")
        return
    
    # Test 2: Position Validation
    print("\n2. Testing Position Validation...")
    try:
        valid_pos = Position(2, 3)
        print(f"✓ Valid position created: {valid_pos}")
        
        # Test invalid positions
        try:
            Position(-1, 0)
            print("✗ Should have failed for negative coordinates")
        except ValueError:
            print("✓ Correctly rejected negative coordinates")
        
        try:
            Position(1.5, 2)
            print("✗ Should have failed for float coordinates")
        except TypeError:
            print("✓ Correctly rejected float coordinates")
            
    except Exception as e:
        print(f"✗ Position validation failed: {e}")
    
    # Test 3: Basic Cell Operations
    print("\n3. Testing Basic Cell Operations...")
    try:
        pos = Position(1, 1)
        
        # Check initial state
        initial_state = airspace.get_cell_state(pos, 0)
        print(f"✓ Initial cell state: {initial_state}")
        
        # Set static obstacle
        airspace.add_static_obstacle(pos)
        obstacle_state = airspace.get_cell_state(pos, 0)
        print(f"✓ After adding obstacle: {obstacle_state}")
        
        # Try to modify static obstacle (should fail)
        try:
            airspace.set_cell_state(pos, CellState.OPEN, 0)
            print("✗ Should not be able to modify static obstacle")
        except AirspaceValidationError:
            print("✓ Correctly prevented modification of static obstacle")
            
    except Exception as e:
        print(f"✗ Cell operations failed: {e}")
    
    # Test 4: Dynamic Path Management
    print("\n4. Testing Dynamic Path Management...")
    try:
        # Create a simple path
        path = [
            (Position(0, 0), 1),
            (Position(0, 1), 2),
            (Position(0, 2), 3),
            (Position(1, 2), 4)
        ]
        
        agent_id = "aircraft_001"
        airspace.add_dynamic_path(path, agent_id)
        print(f"✓ Added dynamic path for {agent_id}")
        
        # Check path cells
        for pos, timestamp in path:
            state = airspace.get_cell_state(pos, timestamp)
            cell_info = airspace.get_cell_info(pos, timestamp)
            print(f"  {pos} at t={timestamp}: {state}, agent: {cell_info.agent_id}")
        
        # Remove path
        airspace.remove_dynamic_path(agent_id)
        print(f"✓ Removed dynamic path for {agent_id}")
        
        # Verify removal
        pos, timestamp = path[0]
        state_after_removal = airspace.get_cell_state(pos, timestamp)
        print(f"✓ State after removal: {state_after_removal}")
        
    except Exception as e:
        print(f"✗ Dynamic path management failed: {e}")
    
    # Test 5: Grid Visualization
    print("\n5. Testing Grid Visualization...")
    try:
        # Create a small test scenario
        test_airspace = Airspace(8, 6, 50)
        
        # Add some static obstacles
        test_airspace.add_static_obstacle(Position(2, 2))
        test_airspace.add_static_obstacle(Position(3, 2))
        test_airspace.add_static_obstacle(Position(4, 2))
        test_airspace.add_static_obstacle(Position(5, 4))
        
        # Add a dynamic path
        dynamic_path = [
            (Position(1, 1), 5),
            (Position(2, 1), 6),
            (Position(3, 1), 7),
            (Position(4, 1), 8)
        ]
        test_airspace.add_dynamic_path(dynamic_path, "emergency_01")
        
        print("✓ Grid at t=0 (static obstacles only):")
        print(test_airspace.to_string(0))
        
        print("\n✓ Grid at t=7 (with dynamic path):")
        print(test_airspace.to_string(7))
        
    except Exception as e:
        print(f"✗ Grid visualization failed: {e}")
    
    # Test 6: Neighbor Detection
    print("\n6. Testing Neighbor Detection...")
    try:
        center_pos = Position(2, 2)
        neighbors = airspace.get_neighbors(center_pos)
        print(f"✓ Neighbors of {center_pos}: {[str(n) for n in neighbors]}")
        
        corner_pos = Position(0, 0)
        corner_neighbors = airspace.get_neighbors(corner_pos)
        print(f"✓ Neighbors of corner {corner_pos}: {[str(n) for n in corner_neighbors]}")
        
    except Exception as e:
        print(f"✗ Neighbor detection failed: {e}")
    
    # Test 7: Configuration Export/Import
    print("\n7. Testing Configuration Export/Import...")
    try:
        config = test_airspace.export_config()
        print(f"✓ Exported configuration: {json.dumps(config, indent=2)}")
        
        new_airspace = Airspace(config["width"], config["height"], config["max_time"])
        new_airspace.import_config(config)
        print("✓ Successfully imported configuration")
        
    except Exception as e:
        print(f"✗ Configuration export/import failed: {e}")
    
    print("\n" + "=" * 50)
    print("AIRSPACE MODULE TESTS COMPLETED")
    print("=" * 50)


if __name__ == "__main__":
    run_airspace_tests()