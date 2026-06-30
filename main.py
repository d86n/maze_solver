"""
main.py - CHƯƠNG TRÌNH MÔ PHỎNG GIẢI MÊ CUNG cho MỘT robot duy nhất.

Hỗ trợ 6 thuật toán chạy ĐỘC LẬP (không kết hợp), mỗi thuật toán 1 lần:
    BFS, DFS, Dijkstra, A*, Flood Fill, Bám tường (tay phải / tay trái)

Giả thiết: bản đồ TĨNH và ĐÃ BIẾT TRƯỚC toàn bộ (mọi thuật toán đều có
quyền truy cập đầy đủ bản đồ trước khi giải).

Đánh giá theo 4 tiêu chí: độ hoàn chỉnh, tính tối ưu, số node đã duyệt,
chiều dài đường đi (tổng số ô) - xem chi tiết trong metrics.py.

VÍ DỤ SỬ DỤNG:
    python main.py
        -> dùng bản đồ mẫu mặc định, chạy cả 6 thuật toán, xuất ảnh + CSV

    python main.py --maze perfect --rows 25 --cols 25 --seed 1
        -> sinh mê cung "hoàn hảo" 25x25 (không vòng lặp)

    python main.py --maze random --rows 20 --cols 20 --wall-prob 0.25
        -> sinh bản đồ lưới ngẫu nhiên (có thể có vòng lặp)

    python main.py --maze file --maze-file mymaze.txt
        -> đọc bản đồ từ file txt do người dùng tự vẽ

    python main.py --weighted
        -> bật chế độ địa hình có trọng số để so sánh rõ BFS vs Dijkstra/A*

    python main.py --algo bfs astar wallfollow
        -> chỉ chạy một số thuật toán được chọn

    python main.py --animate astar
        -> xuất thêm file GIF mô phỏng robot chạy theo thuật toán A*
"""

import argparse
import os
import sys

from maze import Maze
from algorithms import ALGORITHMS
from metrics import build_report, print_report, save_report_csv
from visualize import plot_result, plot_comparison, animate_robot


DEFAULT_MAZE_TEXT = """\
#####################
#S..#...............#
#.#.#.###.#########.#
#.#...#.....#.......#
#.#.###.###.#.#####.#
#.#.#...#...#.#.....#
#.#.#.###.###.#.###.#
#...#.#.....#.#.#...#
###.#.#.###.#.#.#.###
#...#.#.#...#.#.#...#
#.###.#.#.###.#.###.#
#.#...#.#.#...#.....#
#.#.#####.#.#######.#
#.#.......#.........#
#.#######.#########.#
#.................#G#
#####################
"""


def load_maze(args):
    if args.maze == 'perfect':
        return Maze.generate_perfect_maze(args.rows, args.cols, seed=args.seed)
    if args.maze == 'random':
        return Maze.generate_random_grid(args.rows, args.cols,
                                          wall_prob=args.wall_prob, seed=args.seed)
    if args.maze == 'file':
        if not args.maze_file:
            sys.exit("Vui lòng cung cấp --maze-file khi dùng --maze file")
        return Maze.from_file(args.maze_file)
    # mặc định: dùng bản đồ mẫu có sẵn
    tmp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_default_maze.txt')
    with open(tmp_path, 'w', encoding='utf-8') as f:
        f.write(DEFAULT_MAZE_TEXT)
    return Maze.from_file(tmp_path)


def parse_args():
    p = argparse.ArgumentParser(description="Mô phỏng giải mê cung cho 1 robot duy nhất")
    p.add_argument('--maze', choices=['default', 'perfect', 'random', 'file'],
                    default='default', help="Loại bản đồ")
    p.add_argument('--maze-file', type=str, default=None, help="Đường dẫn file bản đồ (.txt)")
    p.add_argument('--rows', type=int, default=21)
    p.add_argument('--cols', type=int, default=21)
    p.add_argument('--wall-prob', type=float, default=0.25)
    p.add_argument('--seed', type=int, default=None)
    p.add_argument('--weighted', action='store_true',
                    help="Thêm địa hình có chi phí khác nhau để so sánh BFS với Dijkstra/A*")
    p.add_argument('--algo', nargs='+',
                    choices=list(ALGORITHMS.keys()) + ['all'], default=['all'])
    p.add_argument('--hand', choices=['right', 'left'], default='right',
                    help="Quy tắc bám tường: tay phải hoặc tay trái")
    p.add_argument('--outdir', type=str, default='output')
    p.add_argument('--no-visualize', action='store_true', help="Không xuất ảnh PNG")
    p.add_argument('--animate', type=str, default=None,
                    help="Tên thuật toán muốn tạo GIF mô phỏng robot, ví dụ: astar")
    return p.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    maze = load_maze(args)
    if args.weighted:
        maze.add_random_terrain_cost(max_cost=3, prob=0.2, seed=args.seed)

    print("=" * 60)
    print("BẢN ĐỒ MÊ CUNG ('#'=tường, '.'=ô trống, 'S'=start, 'G'=goal,")
    print("                 số 2-9 = ô có chi phí di chuyển cao hơn)")
    print("=" * 60)
    print(maze.to_text())
    print(f"\nKích thước: {maze.rows} x {maze.cols} | Start: {maze.start} | Goal: {maze.goal}")
    print(f"Chế độ trọng số địa hình: {'BẬT' if args.weighted else 'TẮT (mọi ô cost=1)'}\n")

    algos = list(ALGORITHMS.keys()) if 'all' in args.algo else args.algo

    results = {}
    for key in algos:
        func = ALGORITHMS[key]
        result = func(maze, hand=args.hand) if key == 'wallfollow' else func(maze)
        results[key] = result
        status = "THÀNH CÔNG" if result.success else "THẤT BẠI"
        print(f"[{result.algorithm}] {status} - duyệt {result.expanded_count} node, "
              f"đường đi dài {result.path_length if result.success else '-'} ô, "
              f"chi phí {round(result.total_cost, 2) if result.success else '-'}, "
              f"thời gian {result.elapsed_ms:.3f} ms")

    print("\n" + "=" * 60)
    print("BẢNG ĐÁNH GIÁ TỔNG HỢP")
    print("=" * 60)
    rows = build_report(results)
    print_report(rows)
    csv_path = os.path.join(args.outdir, 'bao_cao_danh_gia.csv')
    save_report_csv(rows, csv_path)
    print(f"\nĐã lưu bảng đánh giá: {csv_path}")

    if not args.no_visualize:
        for key, result in results.items():
            img_path = os.path.join(args.outdir, f"{key}.png")
            plot_result(maze, result, img_path)
        cmp_path = os.path.join(args.outdir, 'so_sanh_tat_ca.png')
        plot_comparison(maze, list(results.values()), cmp_path)
        print(f"Đã lưu hình ảnh từng thuật toán và ảnh so sánh: {cmp_path}")

    if args.animate:
        if args.animate not in results:
            print(f"Không tìm thấy kết quả cho thuật toán '{args.animate}' để tạo animation.")
        else:
            gif_path = os.path.join(args.outdir, f"{args.animate}_animation.gif")
            animate_robot(maze, results[args.animate], gif_path)
            print(f"Đã lưu animation: {gif_path}")


if __name__ == '__main__':
    main()
