# Chương trình mô phỏng GIẢI MÊ CUNG (1 Robot)

Mô phỏng một robot duy nhất di chuyển từ điểm xuất phát (S) đến điểm đích
(G) trên bản đồ lưới 2D, sử dụng 6 thuật toán giải mê cung kinh điển.
Mỗi thuật toán chạy **độc lập, một lần** (không kết hợp nhiều thuật toán
trong cùng một lượt giải).

**Giả thiết:** bản đồ tĩnh và được biết trước toàn bộ (robot có sẵn bản
đồ đầy đủ trước khi giải, không phải "dò đường" theo cảm biến thời gian
thực).

## Các thuật toán

| Thuật toán | File | Ý tưởng chính |
|---|---|---|
| BFS (Breadth-First Search) | `algorithms.py::bfs` | Duyệt theo từng lớp, đảm bảo tìm đường đi ngắn nhất theo **số bước** trên đồ thị không trọng số. |
| DFS (Depth-First Search) | `algorithms.py::dfs` | Đi sâu hết một nhánh trước khi quay lui. Tìm được *một* đường đi nhưng **không đảm bảo tối ưu**. |
| Dijkstra | `algorithms.py::dijkstra` | Mở rộng theo chi phí tích lũy nhỏ nhất, đảm bảo tối ưu **theo tổng chi phí** kể cả khi các ô có chi phí di chuyển khác nhau. |
| A* | `algorithms.py::astar` | Giống Dijkstra nhưng có thêm heuristic Manhattan để ưu tiên hướng về đích, giúp **duyệt ít node hơn** mà vẫn tối ưu (heuristic admissible). |
| Flood Fill | `algorithms.py::flood_fill` | Nguyên lý dùng trong robot Micromouse: "ngập lụt" tính khoảng cách từ đích ra toàn bản đồ, sau đó robot đi theo hướng giảm dần của khoảng cách. |
| Bám tường (Wall Follower) | `algorithms.py::wall_follower` | Robot bám theo tường bằng quy tắc tay phải/tay trái, **không cần biết toàn bộ bản đồ** trong thực tế triển khai vật lý, nhưng **không đảm bảo độ hoàn chỉnh** nếu mê cung có vòng lặp hoặc nếu robot không tiếp xúc tường. |

## Tiêu chí đánh giá (xem `metrics.py`)

1. **Độ hoàn chỉnh (Completeness):** thuật toán có chắc chắn tìm ra đường
   đi nếu nó tồn tại hay không (đặc tính lý thuyết), và có thực sự thành
   công trên bản đồ đang chạy hay không.
2. **Tính tối ưu (Optimality):** đường đi tìm được có phải đường đi ngắn
   nhất (theo số bước, so với BFS làm chuẩn) và/hoặc chi phí thấp nhất
   (theo tổng cost, so với Dijkstra làm chuẩn) hay không.
3. **Số node đã duyệt:** số ô được thuật toán "mở rộng/xét tới" trong
   quá trình tìm kiếm (với bám tường là tổng số bước robot đã đi, kể cả
   khi đi lặp lại một ô).
4. **Chiều dài đường đi:** tổng số ô trên đường đi cuối cùng (bao gồm cả
   ô xuất phát và ô đích).

Chương trình tự in bảng so sánh ra màn hình và lưu ra file CSV
(`output/bao_cao_danh_gia.csv`).

## Cài đặt

```bash
pip install numpy matplotlib pillow
```

## Cách chạy nhanh

```bash
# Bản đồ mẫu mặc định, chạy đủ 6 thuật toán, xuất ảnh PNG so sánh + CSV
python main.py

# Sinh mê cung "hoàn hảo" (không vòng lặp, đúng 1 đường đi giữa 2 điểm)
python main.py --maze perfect --rows 25 --cols 25 --seed 1

# Sinh bản đồ lưới ngẫu nhiên (có thể có vòng lặp, nhiều đường đi)
python main.py --maze random --rows 20 --cols 20 --wall-prob 0.25 --seed 5

# Đọc bản đồ tự vẽ từ file .txt (xem quy ước ký tự bên dưới)
python main.py --maze file --maze-file mau_phong_trong_bam_tuong_that_bai.txt

# Bật chế độ địa hình có trọng số (một số ô có chi phí 2-3) để thấy rõ
# sự khác biệt giữa BFS (tối ưu số bước) và Dijkstra/A* (tối ưu chi phí)
python main.py --maze random --rows 20 --cols 20 --wall-prob 0.2 --weighted --seed 5

# Chỉ chạy một số thuật toán được chọn
python main.py --algo bfs astar wallfollow

# Xuất thêm animation GIF mô phỏng robot di chuyển theo 1 thuật toán cụ thể
python main.py --animate astar

# Không xuất ảnh PNG (chạy nhanh hơn, chỉ in bảng kết quả ra màn hình)
python main.py --no-visualize
```

Toàn bộ tham số dòng lệnh xem trong `main.py` (`python main.py --help`).

## Quy ước file bản đồ (.txt)

```
#  : tường (không đi qua được)
.  : ô trống, chi phí = 1
S  : điểm xuất phát
G  : điểm đích
2-9: ô trống có chi phí di chuyển cao hơn (địa hình khó đi)
```

Ví dụ file `mau_phong_trong_bam_tuong_that_bai.txt` đi kèm minh họa một
trường hợp kinh điển mà **bám tường thất bại**: robot xuất phát giữa một
căn phòng trống (không chạm tường nào), nên quy tắc "ưu tiên rẽ phải"
khiến robot quẩn quanh một vòng lặp 4 ô ngay tại chỗ và **không bao giờ
tới đích**, trong khi BFS/Dijkstra/A*/Flood Fill đều dễ dàng tìm ra
đường đi ngắn nhất. Đây chính là điểm yếu cố hữu của bám tường: nó chỉ
đảm bảo độ hoàn chỉnh trên mê cung "đơn liên thông" (không có vòng lặp /
không gian mở) và khi robot luôn giữ được tiếp xúc với một mặt tường.

## Cấu trúc dự án

```
maze_solver/
├── maze.py          # Lớp Maze: biểu diễn bản đồ, sinh mê cung, đọc file
├── algorithms.py     # 6 thuật toán giải mê cung, trả về SearchResult
├── metrics.py        # Tính bảng đánh giá theo 4 tiêu chí
├── visualize.py       # Vẽ ảnh PNG + tạo animation GIF bằng matplotlib
├── main.py            # Chương trình chính (CLI)
└── output/             # Kết quả ảnh/CSV được lưu tại đây sau khi chạy
```

## Mở rộng thêm

- Đổi sang di chuyển 8 hướng: chỉnh `self.directions` trong `maze.py`.
- Thêm thuật toán mới: viết hàm nhận `Maze` trả về `SearchResult` trong
  `algorithms.py`, rồi đăng ký vào dict `ALGORITHMS`.
- Đổi bản đồ trọng số tùy ý: dùng `Maze.from_file()` với các ký tự số
  2-9 ở vị trí mong muốn trong file `.txt`.
