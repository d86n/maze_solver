"""
visualize.py - Trực quan hóa bản đồ mê cung, quá trình duyệt và đường đi
của robot bằng matplotlib. Không cần GUI (dùng backend 'Agg'), tất cả
kết quả được lưu ra file ảnh PNG / animation GIF.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation, PillowWriter
import numpy as np

COLOR_WALL = '#222222'
COLOR_FREE = '#ffffff'
COLOR_TERRAIN2 = '#fff2cc'
COLOR_TERRAIN3 = '#ffd28a'
COLOR_VISITED = '#a8d8ff'
COLOR_PATH = '#ff9900'
COLOR_START = '#2ecc71'
COLOR_GOAL = '#e74c3c'
COLOR_ROBOT = '#8e44ad'


def _draw_base(ax, maze):
    ax.set_xlim(0, maze.cols)
    ax.set_ylim(0, maze.rows)
    ax.set_aspect('equal')
    ax.invert_yaxis()
    ax.set_xticks([])
    ax.set_yticks([])
    for r in range(maze.rows):
        for c in range(maze.cols):
            val = maze.grid[r][c]
            if val == -1:
                color = COLOR_WALL
            elif val <= 1:
                color = COLOR_FREE
            elif val == 2:
                color = COLOR_TERRAIN2
            else:
                color = COLOR_TERRAIN3
            ax.add_patch(patches.Rectangle((c, r), 1, 1, facecolor=color,
                                            edgecolor='#dddddd', linewidth=0.3))


def _draw_start_goal(ax, maze):
    sr, sc = maze.start
    gr, gc = maze.goal
    ax.add_patch(patches.Rectangle((sc, sr), 1, 1, facecolor=COLOR_START))
    ax.add_patch(patches.Rectangle((gc, gr), 1, 1, facecolor=COLOR_GOAL))


def plot_result(maze, result, save_path):
    fig, ax = plt.subplots(figsize=(maze.cols / 2.2 + 1, maze.rows / 2.2 + 1))
    _draw_base(ax, maze)
    for (r, c) in result.visited_order:
        ax.add_patch(patches.Rectangle((c, r), 1, 1, facecolor=COLOR_VISITED,
                                        edgecolor='#dddddd', linewidth=0.3, alpha=0.6))
    if result.success:
        for (r, c) in result.path:
            ax.add_patch(patches.Rectangle((c, r), 1, 1, facecolor=COLOR_PATH,
                                            edgecolor='#dddddd', linewidth=0.3, alpha=0.85))
    _draw_start_goal(ax, maze)

    status = "Thành công" if result.success else "Thất bại"
    title = (f"{result.algorithm} | {status} | "
             f"Node đã duyệt: {result.expanded_count} | "
             f"Độ dài đường đi: {result.path_length if result.success else '-'}")
    ax.set_title(title, fontsize=10)
    plt.tight_layout()
    plt.savefig(save_path, dpi=140)
    plt.close(fig)


def plot_comparison(maze, results, save_path):
    n = len(results)
    cols = 3
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 4, rows * 4))
    axes = np.array(axes).reshape(-1)
    for ax, result in zip(axes, results):
        _draw_base(ax, maze)
        for (r, c) in result.visited_order:
            ax.add_patch(patches.Rectangle((c, r), 1, 1, facecolor=COLOR_VISITED,
                                            edgecolor='#dddddd', linewidth=0.2, alpha=0.55))
        if result.success:
            for (r, c) in result.path:
                ax.add_patch(patches.Rectangle((c, r), 1, 1, facecolor=COLOR_PATH,
                                                edgecolor='#dddddd', linewidth=0.2, alpha=0.9))
        _draw_start_goal(ax, maze)
        status = "OK" if result.success else "That bai"
        ax.set_title(f"{result.algorithm}\n{status} | duyet={result.expanded_count} | "
                     f"dai={result.path_length if result.success else '-'}", fontsize=9)
    for ax in axes[len(results):]:
        ax.axis('off')
    plt.tight_layout()
    plt.savefig(save_path, dpi=140)
    plt.close(fig)


def animate_robot(maze, result, save_path, fps=10, show_exploration=True):
    """
    Tạo file GIF mô phỏng robot:
    - show_exploration=True: hiển thị dần các ô được thuật toán "duyệt
      qua" trước (màu xanh nhạt), sau đó hoạt ảnh robot đi dọc đường đi
      cuối cùng tìm được (màu cam, có chấm robot màu tím).
    - show_exploration=False: chỉ hoạt ảnh robot đi theo đường đi cuối.
    """
    fig, ax = plt.subplots(figsize=(maze.cols / 2.2 + 1, maze.rows / 2.2 + 1))

    explore_frames = result.visited_order if show_exploration else []
    path_frames = result.path if result.success else []
    # bước nhảy để giới hạn số khung hình cho mê cung lớn (animation không quá dài)
    step = max(1, len(explore_frames) // 150)
    explore_frames = explore_frames[::step]
    total_frames = len(explore_frames) + len(path_frames) + 5

    def render(frame_idx):
        ax.clear()
        _draw_base(ax, maze)
        n_explore = min(frame_idx, len(explore_frames))
        for (r, c) in explore_frames[:n_explore]:
            ax.add_patch(patches.Rectangle((c, r), 1, 1, facecolor=COLOR_VISITED,
                                            edgecolor='#dddddd', linewidth=0.3, alpha=0.6))
        n_path = max(0, frame_idx - len(explore_frames))
        n_path = min(n_path, len(path_frames))
        for (r, c) in path_frames[:n_path]:
            ax.add_patch(patches.Rectangle((c, r), 1, 1, facecolor=COLOR_PATH,
                                            edgecolor='#dddddd', linewidth=0.3, alpha=0.85))
        _draw_start_goal(ax, maze)
        if n_path > 0:
            rr, rc = path_frames[n_path - 1]
            ax.plot(rc + 0.5, rr + 0.5, 'o', color=COLOR_ROBOT, markersize=12)
        elif n_explore > 0:
            rr, rc = explore_frames[n_explore - 1]
            ax.plot(rc + 0.5, rr + 0.5, 'o', color=COLOR_ROBOT, markersize=8, alpha=0.6)
        ax.set_title(f"{result.algorithm} - khung {frame_idx}/{total_frames}", fontsize=10)

    anim = FuncAnimation(fig, render, frames=total_frames, interval=1000 / fps)
    anim.save(save_path, writer=PillowWriter(fps=fps))
    plt.close(fig)
