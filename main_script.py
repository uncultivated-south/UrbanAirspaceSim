import heapq
import math
import random
from itertools import combinations
from collections import defaultdict

# ---------- A* part ----------
class AstarNode:
    def __init__(self, position, g_cost, h_cost, parent=None, time=0):
        self.position = position
        self.g_cost = g_cost
        self.h_cost = h_cost
        self.parent = parent
        self.time = time

    @property
    def f_cost(self):
        return self.g_cost + self.h_cost

    def __lt__(self, other):
        # Tie-breaker: if f is equal, prefer node with smaller heuristic (larger g)
        if self.f_cost == other.f_cost:
            return self.h_cost < other.h_cost
        return self.f_cost < other.f_cost


def astar_search(start, goal, constraints, grid_map, agent_id, max_time=200):
    """
    A* search with time-extended constraints.

    constraints: list of dict
        Vertex constraint: {'agent': agent_id, 'time': t, 'pos': (r,c)}
        Edge constraint: {'agent': agent_id, 'time': t, 'type':'edge', 'from':(r1,c1), 'to':(r2,c2)}
        If agent=None, constraint is global.

    Notes:
      - Returns a path as a list of positions (indexed by timestep).
      - detect_conflict() applies landing_hold to extend stay at goal.
      - When reaching goal, checks if later timesteps forbid occupying the goal.
    """
    if not grid_map or not grid_map[0]:
        return None

    rows, cols = len(grid_map), len(grid_map[0])
    if not isinstance(max_time, int) or max_time <= 0:
        max_time = rows * cols * 2

    def heuristic(p1, p2):
        return abs(p1[0]-p2[0]) + abs(p1[1]-p2[1])

    # --- preprocess constraints (ignore malformed entries) ---
    vertex_constraints = defaultdict(set)  # (agent,time) -> set of positions
    edge_constraints = defaultdict(set)    # (agent,time) -> set of (u,v)
    for c in constraints:
        if not isinstance(c, dict):
            continue
        t = c.get('time')
        if t is None:
            continue
        a = c.get('agent')
        ctype = c.get('type', None)
        if ctype in (None, 'vertex'):
            pos = c.get('pos')
            if pos is not None:
                vertex_constraints[(a, t)].add(pos)
        elif ctype == 'edge':
            fr = c.get('from')
            to = c.get('to')
            if fr is not None and to is not None:
                edge_constraints[(a, t)].add((fr, to))

    start_node = AstarNode(start, 0, heuristic(start, goal), None, 0)
    open_heap = [start_node]
    closed = {}  # (pos,time) -> best g_cost

    while open_heap:
        curr = heapq.heappop(open_heap)

        if (curr.position, curr.time) in closed and closed[(curr.position, curr.time)] <= curr.g_cost:
            continue
        closed[(curr.position, curr.time)] = curr.g_cost

        # Goal check: ensure no future vertex constraint forbids staying at goal
        if curr.position == goal:
            forbidden_later = False
            for future_t in range(curr.time, max_time + 1):
                if goal in vertex_constraints.get((agent_id, future_t), set()) \
                   or goal in vertex_constraints.get((None, future_t), set()):
                    forbidden_later = True
                    break
            if not forbidden_later:
                path = []
                node = curr
                while node:
                    path.append(node.position)
                    node = node.parent
                return path[::-1]
            # else: continue expanding (allow waiting or alternative route)

        # expand neighbors: 4 directions + wait
        for dx, dy in [(0,1),(0,-1),(1,0),(-1,0),(0,0)]:
            nx, ny = curr.position[0]+dx, curr.position[1]+dy
            if not (0 <= nx < rows and 0 <= ny < cols):
                continue
            if grid_map[nx][ny] == '#':
                continue
            nt = curr.time + 1
            next_pos = (nx, ny)

            # vertex constraints (per-agent or global)
            if next_pos in vertex_constraints.get((agent_id, nt), set()) \
               or next_pos in vertex_constraints.get((None, nt), set()):
                continue
            # edge constraints (forbid transition at time nt)
            if (curr.position, next_pos) in edge_constraints.get((agent_id, nt), set()) \
               or (curr.position, next_pos) in edge_constraints.get((None, nt), set()):
                continue

            if nt > max_time:
                continue

            new_node = AstarNode(next_pos, curr.g_cost+1, heuristic(next_pos, goal), curr, nt)
            heapq.heappush(open_heap, new_node)

    return None


# ---------- conflict detection ----------
def detect_conflict(paths, landing_hold=2):
    """
    paths: dict agent_id -> list of positions (path indexed by time)
    landing_hold: number of steps agents are considered staying at goal

    Returns a list of conflicts (dicts).
    """
    conflicts = []
    if not paths:
        return conflicts

    max_time = max(len(p) for p in paths.values()) + landing_hold

    def pos_at(path, t):
        plen = len(path)
        if t < plen:
            return path[t]
        elif t < plen + landing_hold:
            return path[-1]
        else:
            return None

    # vertex conflicts
    for t in range(max_time):
        occ = defaultdict(list)
        for aid, path in paths.items():
            pos = pos_at(path, t)
            if pos is not None:
                occ[pos].append(aid)
        for pos, agents_here in occ.items():
            if len(agents_here) > 1:
                for i in range(len(agents_here)):
                    for j in range(i+1, len(agents_here)):
                        conflicts.append({
                            'type':'vertex','time':t,
                            'agent1':agents_here[i],'agent2':agents_here[j],
                            'pos':pos
                        })

    # edge conflicts (swap)
    for t in range(1, max_time):
        for (a1, p1), (a2, p2) in combinations(paths.items(), 2):
            a1_t, a1_t1 = pos_at(p1, t), pos_at(p1, t-1)
            a2_t, a2_t1 = pos_at(p2, t), pos_at(p2, t-1)
            if None in (a1_t, a1_t1, a2_t, a2_t1):
                continue
            if a1_t == a2_t1 and a2_t == a1_t1 and a1_t1 != a1_t:
                conflicts.append({
                    'type':'edge','time':t,
                    'agent1':a1,'agent2':a2,
                    'a1_from':a1_t1,'a1_to':a1_t,
                    'a2_from':a2_t1,'a2_to':a2_t
                })
    return conflicts


# ---------- CBS ----------
def cbs_search(agents, grid_map, extra_constraints=None, max_astar_time=200):
    """
    agents: dict agent_id -> (start, goal)
    extra_constraints: initial constraints (global or per-agent)
    Returns: dict of paths or None if infeasible
    """
    if extra_constraints is None:
        extra_constraints = []

    class CBSNode:
        def __init__(self, constraints, paths, cost):
            self.constraints = constraints
            self.paths = paths
            self.cost = cost
        def __lt__(self, other):
            return self.cost < other.cost

    # root: initial paths
    root_paths = {}
    for aid, (s, g) in agents.items():
        p = astar_search(s, g, extra_constraints, grid_map, aid, max_time=max_astar_time)
        if p is None:
            return None
        root_paths[aid] = p
    root = CBSNode(list(extra_constraints), root_paths, sum(len(p) for p in root_paths.values()))
    open_heap = [root]

    while open_heap:
        node = heapq.heappop(open_heap)
        conflicts = detect_conflict(node.paths)
        if not conflicts:
            return node.paths
        # pick earliest conflict
        conflict = min(conflicts, key=lambda c: c['time'])

        children = []
        if conflict['type'] == 'vertex':
            for agent in [conflict['agent1'], conflict['agent2']]:
                new_constraints = list(node.constraints)
                new_constraints.append({'agent': agent, 'time': conflict['time'], 'type': 'vertex', 'pos': conflict['pos']})
                new_paths = dict(node.paths)
                s, g = agents[agent]
                new_p = astar_search(s, g, new_constraints, grid_map, agent, max_time=max_astar_time)
                if new_p:
                    new_paths[agent] = new_p
                    children.append(CBSNode(new_constraints, new_paths, sum(len(p) for p in new_paths.values())))
        else:  # edge conflict
            for agent, (f, to) in [(conflict['agent1'], (conflict['a1_from'], conflict['a1_to'])),
                                   (conflict['agent2'], (conflict['a2_from'], conflict['a2_to']))]:
                new_constraints = list(node.constraints)
                new_constraints.append({'agent': agent, 'time': conflict['time'], 'type': 'edge', 'from': f, 'to': to})
                new_paths = dict(node.paths)
                s, g = agents[agent]
                new_p = astar_search(s, g, new_constraints, grid_map, agent, max_time=max_astar_time)
                if new_p:
                    new_paths[agent] = new_p
                    children.append(CBSNode(new_constraints, new_paths, sum(len(p) for p in new_paths.values())))
        for c in children:
            heapq.heappush(open_heap, c)
    return None


# ---------- auction ----------
def multi_round_auction(agents, grid_map, max_rounds=5, base_price=10.0, strategy='linear'):
    """
    Multi-round auction-based congestion mitigation.

    agents: dict agent_id -> (start, goal)
    grid_map: 2D grid list
    Returns: dict containing solution or auction history.

    Notes:
      - Auction generates global vertex constraints (agent=None) on congested cells.
      - This may make the problem infeasible depending on bids.
    """
    history = []

    # round0: try CBS directly
    solution = cbs_search(agents, grid_map)
    if solution:
        return {'solution': solution}

    for round_id in range(1, max_rounds + 1):
        # generate unconstrained paths
        root_paths = {}
        for aid, (s, g) in agents.items():
            p = astar_search(s, g, [], grid_map, aid)
            if p is None:
                return {'error': f'agent {aid} no path'}
            root_paths[aid] = p

        # analyze congestion
        counter = defaultdict(int)
        conflicts = detect_conflict(root_paths)
        for c in conflicts:
            if c['type'] == 'vertex':
                counter[c['pos']] += 1
            else:
                counter[c['a1_to']] += 1
                counter[c['a2_to']] += 1
        if not counter:
            return {'auctions': history, 'reason': 'No congestion'}

        # compute prices
        prices = {}
        for pos, cnt in counter.items():
            if strategy == 'linear':
                p = base_price * cnt
            else:
                p = base_price * math.log(1 + cnt)
            prices[pos] = {'count': cnt, 'price': round(p, 2)}

        auctions = [{'pos': pos, 'count': info['count'], 'price': info['price']} for pos, info in prices.items()]

        # simulate bids
        bids = {}
        for item in auctions:
            if random.random() < 0.7:
                bids[item['pos']] = round(item['price'] * random.uniform(1, 1.5), 2)

        history.append({'round': round_id, 'auctions': auctions, 'bids': bids})
        if not bids:
            return {'auctions': history, 'reason': 'No bidders'}

        # update base price (smoothed)
        base_price = 0.5 * base_price + 0.5 * max(prices[pos]['price'] for pos in bids.keys())

        # add global vertex constraints for losing cells
        auction_constraints = []
        horizon = 50
        for pos in bids.keys():
            for t in range(horizon):
                auction_constraints.append({'agent': None, 'time': t, 'type': 'vertex', 'pos': pos})

        solution = cbs_search(agents, grid_map, extra_constraints=auction_constraints)
        if solution:
            return {'solution': solution, 'auctions': history}

    return {'auctions': history, 'reason': 'Exceeded max rounds'}
