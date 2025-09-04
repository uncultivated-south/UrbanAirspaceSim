import random
from pprint import pprint

# Import functions from your main script
from main_script import cbs_search, multi_round_auction


def build_grid(rows=4, cols=4, obstacles=4, agents=None):
    """Builds a rows x cols grid filled with '.' and places obstacles '#'.
       Obstacles will not overwrite agent start/goal positions."""
    grid = [["." for _ in range(cols)] for _ in range(rows)]

    forbidden = set()
    if agents:
        for s, g in agents.values():
            forbidden.add(s)
            forbidden.add(g)

    free_cells = [(r, c) for r in range(rows) for c in range(cols) if (r, c) not in forbidden]
    chosen = random.sample(free_cells, min(obstacles, len(free_cells)))
    for r, c in chosen:
        grid[r][c] = "#"

    return grid


def print_grid(grid):
    """Pretty-print the grid."""
    for row in grid:
        print(" ".join(row))
    print()


def main():
    # Define 4 agents (start, goal)
    agents = {
        "A1": ((0, 0), (3, 3)),
        "A2": ((0, 1), (3, 2)),
        "A3": ((0, 2), (3, 1)),
        "A4": ((0, 3), (3, 0)),
    }

    grid_map = build_grid(4, 4, obstacles=4, agents=agents)

    print("=== Grid with Obstacles ===")
    print_grid(grid_map)

    print("=== Test CBS Search ===")
    solution_cbs = cbs_search(agents, grid_map)
    if solution_cbs:
        for aid, path in solution_cbs.items():
            print(f"{aid}: {path}")
    else:
        print("No solution found with CBS.")

    print("\n=== Test Multi-Round Auction ===")
    result_auction = multi_round_auction(agents, grid_map, max_rounds=3)
    pprint(result_auction)


if __name__ == "__main__":
    main()
