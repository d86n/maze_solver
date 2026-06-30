"""
algorithms.py - Cài đặt các thuật toán giải mê cung:
BFS, DFS, Dijkstra, A*, Flood Fill, Bám tường (Wall Following).

Mỗi thuật toán chạy ĐỘC LẬP, MỘT LẦN (không kết hợp). Mỗi hàm nhận vào
một đối tượng Maze (đã biết trước toàn bộ bản đồ) và trả về một
SearchResult chứa: đường đi tìm được, danh sách các ô đã duyệt, tổng chi
phí, kết quả thành/bại, và thời gian chạy - phục vụ việc đánh giá theo
các tiêu chí: độ hoàn chỉnh, tính tối ưu, số node đã duyệt, chiều dài
đường đi.
"""

import heapq
import time
from collections import deque
from dataclasses import dataclass, field
from typing import List, Tuple

Cell = Tuple[int, int]


@dataclass
class SearchResult:
    algorithm: str
    success: bool
    path: List[Cell] = field(default_factory=list)
    visited_order: List[Cell] = field(default_factory=list)  # thứ tự ô đã duyệt
    expanded_count: int = 0      # số node đã duyệt
    path_length: int = 0         # tổng số ô trên đường đi (bao gồm start & goal)
    total_cost: float = 0.0      # tổng chi phí di chuyển dọc đường đi
    elapsed_ms: float = 0.0


def _reconstruct_path(parent, start, goal):
    if goal != start and goal not in parent:
        return []
    path = [goal]
    cur = goal
    while cur != start:
        cur = parent[cur]
        path.append(cur)
    path.reverse()
    return path


def _path_cost(maze, path):
    if not path:
        return 0.0
    cost = 0.0
    for cell in path[1:]:
        cost += maze.cost(cell)
    return cost


# ---------------------------------------------------------------------------
# 1. BFS - Breadth-First Search (tối ưu theo SỐ BƯỚC trên đồ thị không trọng số)
# ---------------------------------------------------------------------------
def bfs(maze):
    t0 = time.perf_counter()
    start, goal = maze.start, maze.goal
    frontier = deque([start])
    visited = {start}
    visited_order = []
    parent = {}
    found = False

    while frontier:
        cur = frontier.popleft()
        visited_order.append(cur)
        if cur == goal:
            found = True
            break
        for nb in maze.neighbors(cur):
            if nb not in visited:
                visited.add(nb)
                parent[nb] = cur
                frontier.append(nb)

    path = _reconstruct_path(parent, start, goal) if found else []
    elapsed = (time.perf_counter() - t0) * 1000
    return SearchResult("BFS", found, path, visited_order, len(visited_order),
                         len(path), _path_cost(maze, path), elapsed)


# ---------------------------------------------------------------------------
# 2. DFS - Depth-First Search (chỉ tìm MỘT đường đi, không đảm bảo tối ưu)
# ---------------------------------------------------------------------------
def dfs(maze):
    t0 = time.perf_counter()
    start, goal = maze.start, maze.goal
    stack = [start]
    visited = {start}
    visited_order = []
    parent = {}
    found = False

    while stack:
        cur = stack.pop()
        visited_order.append(cur)
        if cur == goal:
            found = True
            break
        for nb in maze.neighbors(cur):
            if nb not in visited:
                visited.add(nb)
                parent[nb] = cur
                stack.append(nb)

    path = _reconstruct_path(parent, start, goal) if found else []
    elapsed = (time.perf_counter() - t0) * 1000
    return SearchResult("DFS", found, path, visited_order, len(visited_order),
                         len(path), _path_cost(maze, path), elapsed)


# ---------------------------------------------------------------------------
# 3. Dijkstra (tối ưu theo TỔNG CHI PHÍ, dùng tốt cho bản đồ có trọng số)
# ---------------------------------------------------------------------------
def dijkstra(maze):
    t0 = time.perf_counter()
    start, goal = maze.start, maze.goal
    dist = {start: 0.0}
    parent = {}
    visited_order = []
    closed = set()
    pq = [(0.0, start)]
    found = False

    while pq:
        d, cur = heapq.heappop(pq)
        if cur in closed:
            continue
        closed.add(cur)
        visited_order.append(cur)
        if cur == goal:
            found = True
            break
        for nb in maze.neighbors(cur):
            nd = d + maze.cost(nb)
            if nd < dist.get(nb, float('inf')):
                dist[nb] = nd
                parent[nb] = cur
                heapq.heappush(pq, (nd, nb))

    path = _reconstruct_path(parent, start, goal) if found else []
    elapsed = (time.perf_counter() - t0) * 1000
    total_cost = dist.get(goal, 0.0) if found else 0.0
    return SearchResult("Dijkstra", found, path, visited_order, len(visited_order),
                         len(path), total_cost, elapsed)


# ---------------------------------------------------------------------------
# 4. A* (A-Star) - dùng heuristic Manhattan, đảm bảo admissible
# ---------------------------------------------------------------------------
def _manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(maze, min_cost=1):
    """min_cost: chi phí nhỏ nhất có thể của một ô, dùng để heuristic
    Manhattan luôn 'admissible' (không vượt quá chi phí thực tế còn lại)."""
    t0 = time.perf_counter()
    start, goal = maze.start, maze.goal
    g_score = {start: 0.0}
    parent = {}
    visited_order = []
    closed = set()
    pq = [(_manhattan(start, goal) * min_cost, start)]
    found = False

    while pq:
        f, cur = heapq.heappop(pq)
        if cur in closed:
            continue
        closed.add(cur)
        visited_order.append(cur)
        if cur == goal:
            found = True
            break
        for nb in maze.neighbors(cur):
            ng = g_score[cur] + maze.cost(nb)
            if ng < g_score.get(nb, float('inf')):
                g_score[nb] = ng
                parent[nb] = cur
                f_score = ng + _manhattan(nb, goal) * min_cost
                heapq.heappush(pq, (f_score, nb))

    path = _reconstruct_path(parent, start, goal) if found else []
    elapsed = (time.perf_counter() - t0) * 1000
    total_cost = g_score.get(goal, 0.0) if found else 0.0
    return SearchResult("A*", found, path, visited_order, len(visited_order),
                         len(path), total_cost, elapsed)


# ---------------------------------------------------------------------------
# 5. Flood Fill (nguyên lý giải mê cung kiểu robot Micromouse)
# ---------------------------------------------------------------------------
def flood_fill(maze):
    """
    Giai đoạn 1 (Flood/"ngập lụt"): tính khoảng cách (số bước) từ GOAL tới
    mọi ô có thể tới được, bằng BFS ngược xuất phát từ goal -> gán
    "flood value" cho từng ô.
    Giai đoạn 2: robot xuất phát từ start, tại mỗi bước di chuyển sang ô
    lân cận có flood value nhỏ hơn (gần goal hơn) cho tới khi tới đích.
    """
    t0 = time.perf_counter()
    start, goal = maze.start, maze.goal

    flood = {goal: 0}
    visited_order = [goal]
    q = deque([goal])
    while q:
        cur = q.popleft()
        for nb in maze.neighbors(cur):
            if nb not in flood:
                flood[nb] = flood[cur] + 1
                visited_order.append(nb)
                q.append(nb)

    if start not in flood:
        elapsed = (time.perf_counter() - t0) * 1000
        return SearchResult("Flood Fill", False, [], visited_order,
                             len(visited_order), 0, 0.0, elapsed)

    path = [start]
    cur = start
    seen_path = {start}
    while cur != goal:
        candidates = [nb for nb in maze.neighbors(cur) if nb in flood]
        nxt = min(candidates, key=lambda c: flood[c])
        if flood[nxt] >= flood[cur] or nxt in seen_path:
            break  # phòng vệ, tránh lặp vô hạn nếu có lỗi logic
        cur = nxt
        path.append(cur)
        seen_path.add(cur)

    found = (path[-1] == goal)
    elapsed = (time.perf_counter() - t0) * 1000
    return SearchResult("Flood Fill", found, path if found else [], visited_order,
                         len(visited_order), len(path) if found else 0,
                         _path_cost(maze, path) if found else 0.0, elapsed)


# ---------------------------------------------------------------------------
# 6. Bám tường - Wall Following (quy tắc tay phải / tay trái)
# ---------------------------------------------------------------------------
def wall_follower(maze, hand='right', max_steps=None):
    """
    Robot bám theo tường, áp dụng quy tắc "tay phải" (mặc định) hoặc
    "tay trái": tại mỗi bước, robot ưu tiên rẽ về phía tay đang bám tường
    trước, sau đó mới đi thẳng, rồi rẽ phía đối diện, cuối cùng mới quay đầu.

    LƯU Ý QUAN TRỌNG (độ hoàn chỉnh): thuật toán này CHỈ đảm bảo tìm ra
    đường đi khi mê cung "đơn liên thông" (simply-connected - không có
    vòng lặp/đảo tường ở giữa, ví dụ mê cung sinh bởi generate_perfect_maze).
    Với bản đồ có vòng lặp (ví dụ generate_random_grid), robot có thể đi
    lặp vô hạn quanh một "đảo" và KHÔNG bao giờ tới đích -> được phát hiện
    và báo THẤT BẠI thay vì treo chương trình.
    """
    t0 = time.perf_counter()
    start, goal = maze.start, maze.goal
    if max_steps is None:
        max_steps = maze.rows * maze.cols * 8

    dirs = maze.directions  # [N, E, S, W]
    heading = 1  # robot xuất phát mặc định hướng Đông

    # độ lệch hướng theo thứ tự ưu tiên: phải, thẳng, trái, quay đầu
    if hand == 'right':
        turn_order = [1, 0, -1, 2]
    else:
        turn_order = [-1, 0, 1, 2]

    pos = start
    path = [pos]
    visited_order = [pos]
    state_seen = set()

    steps = 0
    while pos != goal and steps < max_steps:
        moved = False
        for turn in turn_order:
            new_heading = (heading + turn) % 4
            dr, dc = dirs[new_heading]
            np_ = (pos[0] + dr, pos[1] + dc)
            if maze.is_free(np_):
                heading = new_heading
                pos = np_
                path.append(pos)
                visited_order.append(pos)
                moved = True
                break
        if not moved:
            break  # bị kẹt hoàn toàn, không còn lối nào kể cả quay đầu
        steps += 1
        # Phát hiện vòng lặp: nếu (vị trí, hướng) lặp lại -> đang đi vòng
        # quanh một "đảo" tường, sẽ không bao giờ tới đích trên bản đồ này
        state = (pos, heading)
        if state in state_seen:
            break
        state_seen.add(state)

    found = (pos == goal)
    label = f"Wall Follower ({'tay phải' if hand == 'right' else 'tay trái'})"
    elapsed = (time.perf_counter() - t0) * 1000
    return SearchResult(label, found, path if found else [], visited_order,
                         len(visited_order), len(path) if found else 0,
                         _path_cost(maze, path) if found else 0.0, elapsed)


ALGORITHMS = {
    'bfs': bfs,
    'dfs': dfs,
    'dijkstra': dijkstra,
    'astar': astar,
    'floodfill': flood_fill,
    'wallfollow': wall_follower,
}
