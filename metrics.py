"""
metrics.py - Tính toán các tiêu chí đánh giá thuật toán giải mê cung:

- Độ hoàn chỉnh (Completeness): thuật toán có CHẮC CHẮN tìm ra đường đi
  nếu nó tồn tại hay không (đặc tính lý thuyết) + kết quả thực tế trên
  bản đồ đang chạy.
- Tính tối ưu (Optimality): đường đi tìm được có phải là đường đi ngắn
  nhất (theo số bước) / chi phí thấp nhất (theo tổng cost) hay không.
- Số node đã duyệt (Expanded nodes).
- Chiều dài đường đi (tổng số ô, bao gồm điểm đầu & điểm cuối).
"""

import csv

# Đặc tính lý thuyết của từng thuật toán (độc lập với bản đồ cụ thể)
THEORETICAL_PROPERTIES = {
    'BFS': {
        'complete': 'Có (không gian trạng thái hữu hạn)',
        'optimal': 'Có, theo SỐ BƯỚC (đồ thị không trọng số)',
    },
    'DFS': {
        'complete': 'Có (trên bản đồ hữu hạn, không lặp trạng thái)',
        'optimal': 'Không đảm bảo',
    },
    'Dijkstra': {
        'complete': 'Có (trọng số không âm)',
        'optimal': 'Có, theo TỔNG CHI PHÍ',
    },
    'A*': {
        'complete': 'Có (heuristic admissible)',
        'optimal': 'Có, theo TỔNG CHI PHÍ (heuristic admissible)',
    },
    'Flood Fill': {
        'complete': 'Có (dùng BFS để tính flood value)',
        'optimal': 'Có, theo SỐ BƯỚC (bản đồ không trọng số)',
    },
}


def _is_wall_follower(name):
    return name.startswith('Wall Follower')


def build_report(results):
    """
    results: dict {key: SearchResult}
    Trả về list[dict] (1 dòng / thuật toán) để in bảng hoặc lưu CSV.
    """
    bfs_res = results.get('bfs')
    dij_res = results.get('dijkstra')
    ref_steps = bfs_res.path_length if (bfs_res and bfs_res.success) else None
    ref_cost = dij_res.total_cost if (dij_res and dij_res.success) else None

    rows = []
    for r in results.values():
        name = r.algorithm
        if _is_wall_follower(name):
            theory_complete = 'Chỉ khi mê cung đơn liên thông (không vòng lặp)'
            theory_optimal = 'Không đảm bảo'
        else:
            theory = THEORETICAL_PROPERTIES.get(name, {})
            theory_complete = theory.get('complete', '-')
            theory_optimal = theory.get('optimal', '-')

        if not r.success:
            steps_label = '-'
            cost_label = '-'
        elif ref_steps is None:
            steps_label = 'Khong xac dinh (chua chay BFS de doi chieu)'
        else:
            steps_label = 'Co' if r.path_length == ref_steps else 'Khong'
        if not r.success:
            pass  # cost_label already '-'
        elif ref_cost is None:
            cost_label = 'Khong xac dinh (chua chay Dijkstra de doi chieu)'
        else:
            cost_label = 'Co' if abs(r.total_cost - ref_cost) < 1e-6 else 'Khong'

        rows.append({
            'Thuat_toan': name,
            'Tim_duoc_duong_di': 'Co' if r.success else 'Khong',
            'Do_hoan_chinh_ly_thuyet': theory_complete,
            'Tinh_toi_uu_ly_thuyet': theory_optimal,
            'Toi_uu_so_buoc_thuc_te': steps_label,
            'Toi_uu_chi_phi_thuc_te': cost_label,
            'So_node_da_duyet': r.expanded_count,
            'Chieu_dai_duong_di': r.path_length if r.success else '-',
            'Tong_chi_phi': round(r.total_cost, 2) if r.success else '-',
            'Thoi_gian_ms': round(r.elapsed_ms, 3),
        })
    return rows


def print_report(rows):
    if not rows:
        print("Không có kết quả để hiển thị.")
        return
    headers = list(rows[0].keys())
    col_widths = [max(len(str(h)), max((len(str(row[h])) for row in rows), default=0))
                  for h in headers]
    sep = '-+-'.join('-' * w for w in col_widths)

    def fmt_row(values):
        return ' | '.join(str(v).ljust(w) for v, w in zip(values, col_widths))

    print(fmt_row(headers))
    print(sep)
    for row in rows:
        print(fmt_row(row.values()))


def save_report_csv(rows, path):
    if not rows:
        return
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
