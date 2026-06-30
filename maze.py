"""
maze.py - Định nghĩa lớp Maze (bản đồ lưới 2D) cho bài toán giải mê cung.

Quy ước biểu diễn bản đồ:
- Mỗi ô (cell) được xác định bởi tọa độ (hàng, cột) = (row, col).
- Giá trị trong lưới:
    -1  : Tường (wall) - không thể đi qua.
    >=1 : Ô trống (free cell) với "chi phí di chuyển" (cost) tương ứng.
          Mặc định cost = 1 cho mọi ô trống (bản đồ "đồng nhất").
          Nếu bật chế độ "có trọng số" (weighted), một số ô có thể có
          cost = 2, 3,... mô phỏng địa hình gồ ghề/khó đi, giúp minh họa
          rõ sự khác biệt giữa BFS (tối ưu theo SỐ BƯỚC) và
          Dijkstra/A* (tối ưu theo TỔNG CHI PHÍ).

Giả thiết của bài toán: bản đồ TĨNH và ĐÃ BIẾT TRƯỚC toàn bộ (robot có
quyền truy cập đầy đủ bản đồ trước khi giải, đúng yêu cầu đề bài).
"""

import random
from collections import deque


class Maze:
    def __init__(self, grid, start, goal):
        self.grid = grid
        self.rows = len(grid)
        self.cols = len(grid[0]) if self.rows > 0 else 0
        self.start = start
        self.goal = goal
        # 4 hướng di chuyển: Bắc, Đông, Nam, Tây (thứ tự dùng cho bám tường)
        self.directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        self.direction_names = ['N', 'E', 'S', 'W']

    # ---------- Truy vấn cơ bản ----------
    def in_bounds(self, pos):
        r, c = pos
        return 0 <= r < self.rows and 0 <= c < self.cols

    def is_wall(self, pos):
        r, c = pos
        return self.grid[r][c] == -1

    def is_free(self, pos):
        return self.in_bounds(pos) and not self.is_wall(pos)

    def cost(self, pos):
        r, c = pos
        return max(1, self.grid[r][c])

    def neighbors(self, pos):
        r, c = pos
        result = []
        for dr, dc in self.directions:
            np_ = (r + dr, c + dc)
            if self.is_free(np_):
                result.append(np_)
        return result

    # ---------- Sinh bản đồ ----------
    @staticmethod
    def generate_perfect_maze(rows, cols, seed=None):
        """
        Sinh mê cung "hoàn hảo" (perfect maze) bằng thuật toán Randomized
        DFS / Recursive Backtracker (cài đặt LẶP, không đệ quy, để tránh
        giới hạn recursion với bản đồ lớn): giữa 2 ô bất kỳ luôn có đúng
        MỘT đường đi duy nhất (không có vòng lặp / đảo tường).
        rows, cols nên là số lẻ để mê cung đẹp (tường xen kẽ lối đi).
        """
        rng = random.Random(seed)
        if rows % 2 == 0:
            rows += 1
        if cols % 2 == 0:
            cols += 1
        grid = [[-1 for _ in range(cols)] for _ in range(rows)]

        grid[1][1] = 1
        stack = [(1, 1)]
        while stack:
            r, c = stack[-1]
            dirs = [(-2, 0), (2, 0), (0, -2), (0, 2)]
            rng.shuffle(dirs)
            carved = False
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == -1:
                    grid[r + dr // 2][c + dc // 2] = 1
                    grid[nr][nc] = 1
                    stack.append((nr, nc))
                    carved = True
                    break
            if not carved:
                stack.pop()

        start = (1, 1)
        goal = (rows - 2, cols - 2)
        grid[goal[0]][goal[1]] = 1
        return Maze(grid, start, goal)

    @staticmethod
    def generate_random_grid(rows, cols, wall_prob=0.25, seed=None):
        """
        Sinh bản đồ lưới ngẫu nhiên: mỗi ô có xác suất `wall_prob` là tường.
        Bản đồ này có thể có vòng lặp / nhiều đường đi (KHÔNG phải mê cung
        "hoàn hảo") - dùng để minh họa trường hợp thuật toán bám tường
        có thể THẤT BẠI (không đảm bảo độ hoàn chỉnh trên bản đồ có đảo).
        """
        rng = random.Random(seed)
        start = (0, 0)
        goal = (rows - 1, cols - 1)
        for _ in range(300):
            grid = [[1 if rng.random() > wall_prob else -1
                     for _ in range(cols)] for _ in range(rows)]
            grid[start[0]][start[1]] = 1
            grid[goal[0]][goal[1]] = 1
            m = Maze(grid, start, goal)
            if m._is_reachable(start, goal):
                return m
        # fallback: nếu quá nhiều lần thất bại, trả về bản đồ trống hoàn toàn
        grid = [[1] * cols for _ in range(rows)]
        return Maze(grid, start, goal)

    def add_random_terrain_cost(self, max_cost=3, prob=0.2, seed=None):
        """Gán ngẫu nhiên chi phí cao hơn (địa hình khó đi) cho một số ô
        trống, dùng để minh họa khác biệt giữa BFS và Dijkstra/A*."""
        rng = random.Random(seed)
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] != -1 and (r, c) not in (self.start, self.goal):
                    if rng.random() < prob:
                        self.grid[r][c] = rng.randint(2, max_cost)

    def _is_reachable(self, start, goal):
        q = deque([start])
        seen = {start}
        while q:
            cur = q.popleft()
            if cur == goal:
                return True
            for nb in self.neighbors(cur):
                if nb not in seen:
                    seen.add(nb)
                    q.append(nb)
        return False

    @staticmethod
    def from_file(path):
        """
        Đọc bản đồ từ file text. Quy ước ký tự:
            '#'      : tường
            '.'      : ô trống, cost = 1
            'S'      : điểm xuất phát (ô trống)
            'G'      : điểm đích (ô trống)
            '2'-'9'  : ô trống có cost tương ứng (địa hình khó đi)
        """
        with open(path, 'r', encoding='utf-8') as f:
            lines = [line.rstrip('\n') for line in f if line.strip('\n') != '']
        cols = max(len(line) for line in lines)
        grid = []
        start = goal = None
        for r, line in enumerate(lines):
            row = []
            for c in range(cols):
                ch = line[c] if c < len(line) else '#'
                if ch == '#':
                    row.append(-1)
                elif ch == 'S':
                    row.append(1)
                    start = (r, c)
                elif ch == 'G':
                    row.append(1)
                    goal = (r, c)
                elif ch.isdigit() and ch != '0':
                    row.append(int(ch))
                else:
                    row.append(1)
            grid.append(row)
        if start is None or goal is None:
            raise ValueError("File bản đồ phải có ký tự 'S' (start) và 'G' (goal).")
        return Maze(grid, start, goal)

    def to_text(self):
        lines = []
        for r in range(self.rows):
            line = []
            for c in range(self.cols):
                pos = (r, c)
                if pos == self.start:
                    line.append('S')
                elif pos == self.goal:
                    line.append('G')
                elif self.grid[r][c] == -1:
                    line.append('#')
                elif self.grid[r][c] == 1:
                    line.append('.')
                else:
                    line.append(str(self.grid[r][c]))
            lines.append(''.join(line))
        return '\n'.join(lines)
