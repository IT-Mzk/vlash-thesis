# Số liệu chuẩn từ PDF gốc (2512.01031v1) — dùng để sửa Chương 3 (Bước B)

> Đã đọc trực tiếp Table 1, 2, 3 và Fig 6, 7 trong PDF. Đây là nguồn sự thật.

## A. LIBERO (Table 1, π0.5) — ⚠️ Paper KHÔNG có Naive-Async cho LIBERO

| Method | Δ | Spatial | Object | Goal | LIBERO-10 | **Avg SR** | Steps | Time(s) | Speedup |
|---|---|---|---|---|---|---|---|---|---|
| Sync | 0 | 97.3 | 99.6 | 96.7 | 93.5 | **96.8** | 156.0 | 8.4 | – |
| **Sync (w/o state)** | – | 98.5 | 99.6 | 97.3 | 95.4 | **97.7** (+0.9) | 157.2 | 8.4 | – |
| VLASH | 1 | 98.8 | 99.2 | 96.7 | 94.4 | **97.2** | 153.9 | 7.2 | 1.17× |
| VLASH | 2 | 97.5 | 99.2 | 97.3 | 94.6 | **97.1** | 157.6 | 6.4 | 1.31× |
| VLASH | 3 | 94.4 | 98.8 | 93.3 | 91.9 | **94.6** | 167.3 | 5.7 | 1.47× |
| VLASH | 4 | 92.5 | 96.9 | 93.3 | 89.6 | **93.1** | 176.7 | 5.8 | 1.45× |

**Sửa bắt buộc:**
1. **Sync (w/o state) = 97.7% > Sync 96.8%** → visual-only TỐT HƠN. Thesis đang ghi ngược (91.6 < 95.9) + diễn giải sai. Phải viết lại: VLA *under-utilize* robot state ⇒ đây chính là lý do cần temporal-offset augmentation để ép model dùng state.
2. **Bỏ toàn bộ số Naive-Async cho LIBERO** (94.3/90.2/83.2/75.1 là **bịa** — paper nói rõ "trên LIBERO các phương pháp async hành xử tương tự, nên chỉ so với sync"). So sánh Naive-Async nằm ở **Kinetix**.
3. Số per-column Spatial/Object/Goal/LIBERO-10 phải thay bằng số đúng ở bảng trên.
4. Sync avg = **96.8** (không phải 95.9). LIBERO dùng **K=5** (không phải K=24 — K=24 là của real-world).

## B. Kinetix (Fig 6 + text) — đây MỚI là chỗ so Naive-Async
- VLASH @ Δ=4 = **81.7%**, Naive-Async = **51.2%** → **+30.5%**. ✓ (đã đúng trong thesis)
- Sync ~84.3%, RTC ~71.8%: **cần đọc lại Fig 6 để xác nhận chính xác** (text chỉ nêu rõ 81.7 vs 51.2). Tạm coi RTC≈71.8 là "cần verify từ đồ thị".

## C. Real-World (Fig 7) — ⚠️ SAI NHIỀU trong thesis
Thang điểm 2-point → "score percentage". 3 task: Pick&Place, Stacking, Sorting. 16 rollout/method.

| Method | **Avg score** | Ghi chú |
|---|---|---|
| Sync | **83%** | thesis ghi sai 0.92 |
| Naive-Async | **89.7%** | thesis ghi sai 0.78 |
| **VLASH** | **94%** | ✓ khớp |

- **Sửa narrative:** thứ tự đúng là **VLASH 94% > Naive 89.7% > Sync 83%** (Sync THẤP NHẤT vì stall làm chậm/hỏng task trong thang điểm này). Thesis đang nói Naive tệ nhất (0.78) → SAI.
- Completion time: VLASH 18.8s vs Sync 21s → **1.12× speedup** ✓.
- Quantization: **q=2 → 2.03× speedup** giữ nguyên accuracy; **q=3 → 2.67× speedup, giảm 4.7% score**. (Thesis ghi "2.67× additional throughput" → SAI: 2.67× là TỔNG speedup ở q=3, không phải "thêm".)
- Per-task time (Fig 7): Sync 14.4/18.0/30.6 · Naive 13.0/18.2/27.8 · VLASH 13.9/16.6/25.9 · q2 8.2/9.9/15.1 · q3 7.1/7.8/11.5.

## D. Reaction latency (Table 2) — ⚠️ thesis ghép sai cặp GPU
π0.5, 1 ảnh, K=25 @ 50Hz, execution duration 500ms. Max reaction = exec + infer (Sync) / infer (Async).

| GPU | Infer (ms) | Sync reaction | Async reaction | Speedup |
|---|---|---|---|---|
| RTX 5090 | 30.4 | 530.4 | 30.4 | **17.4×** |
| RTX 4090 | 36.1 | 536.1 | 36.1 | **14.9×** |
| RTX 5070 | 64.1 | 564.1 | 64.1 | **8.8×** |

- Thesis ghi "530 ms → 36 ms (14.9×)" = **ghép sai** (530 là Sync của 5090, 36 là Async của 4090; 530/36=14.7). Sửa thành: **536 → 36 = 14.9× (RTX 4090)** hoặc **530 → 30 = 17.4× (RTX 5090)**.
- Headline của paper (abstract) là **17.4×**.

## E. Fine-tuning efficiency (Table 3)
- Original: 420.99 ms/step; LIBERO @10K/20K/30K = 94.1 / 97.1 / 96.8
- VLASH: 129.29 ms/step; @10K/20K/30K = 87.1 / 94.4 / 96.6 → **3.26× / step** ✓
- Cấu hình: Δmax=**3**, effective batch 16/GPU (64 global), 4×H100, DDP. (Thesis Ch2 ghi max_delay_steps=8 & N=4 — đó là *default codebase*, còn *thí nghiệm paper* dùng Δmax=3. Khi mô tả thí nghiệm paper nên dùng Δmax=3.)

## F. References bổ sung từ PDF
- π0 = Black, Brown, Driess, et al., arXiv:2410.24164, 2024.
- RTC = Black, Galliker, Levine, arXiv:2506.07339, 2025.
- Gemini Robotics 1.5 = Abdolmaleki et al., arXiv:2510.03342, 2025 (cho Intro/Future Work).
- LeRobot = Cadene et al., github.com/huggingface/lerobot, 2024.
- Authors VLASH (xác nhận): Jiaming Tang, Yufei Sun, Yilong Zhao, Shang Yang, Yujun Lin, Zhuoyang Zhang, James Hou, Yao Lu, Zhijian Liu, Song Han (MIT/NVIDIA/Tsinghua/Berkeley/UCSD/Caltech).

## G. Tóm tắt narrative ĐÚNG cho Ch3 (rất quan trọng cho similarity & tính đúng)
- LIBERO: VLASH ≈ Sync ở mọi Δ (97.2→93.1), tốc độ 1.17–1.47×. Phát hiện phụ: **Sync no-state (97.7) > Sync (96.8)** → VLA chưa khai thác state → động lực cho augmentation.
- Kinetix (động): VLASH 81.7 vs Naive 51.2 (+30.5), vs RTC ~71.8 → rollforward thắng cả inpainting trong môi trường động.
- Real-world: **VLASH 94 > Naive 89.7 > Sync 83**, 1.12× (q=2: 2.03×; q=3: 2.67×, −4.7%).
- Reaction: tới **17.4×** (RTX 5090) / 14.9× (4090) / 8.8× (5070).
