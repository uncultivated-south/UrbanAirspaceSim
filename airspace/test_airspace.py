# test_airspace.py

import json
from airspace import Airspace, Position, CellState, AirspaceValidationError


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
