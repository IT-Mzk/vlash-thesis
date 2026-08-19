# Tiến độ fine-tune π0.5 trên RTX 3050 — nhật ký phiên (2026-08-17)

> File bàn giao để Claude trên máy khác (MacBook) nắm được đã làm tới đâu.
> LƯU Ý QUAN TRỌNG: toàn bộ môi trường train nằm trong **WSL2 trên máy Windows**. MacBook
> KHÔNG chạy được phần GPU này — Mac chỉ dùng để viết/sửa thesis. Phần train/benchmark phải
> làm trên máy Windows.

## Mục tiêu phiên này
Trả lời câu hỏi Q1 của supervisor bằng cách **tự chạy π0.5 thật trên phần cứng của tác giả**
(RTX 3050 6GB). Ban đầu chọn hướng "train đầy đủ đạt SR gần paper", nhưng sau khi đo được phần
cứng chậm hơn paper ~44× → chuyển sang hướng chắc ăn: **benchmark latency trước** (đã xong),
train là bonus tùy chọn.

## ✅ ĐÃ HOÀN THÀNH

### 1. Môi trường (WSL2) — XONG
- WSL2 + Ubuntu cài trên Windows. GPU passthrough OK: `nvidia-smi` trong Ubuntu thấy
  **RTX 3050 6GB**, driver 576.40, CUDA 12.9.
- Python: bản Ubuntu mặc định là **3.14 (quá mới, không có wheel torch)** → dùng **uv** cài
  **Python 3.12.14** riêng.
- **venv: `~/vlash-thesis/.venv`** (trên ổ Linux native — BẮT BUỘC, xem gotcha #2).
- **torch 2.7.1+cu126**, `torch.cuda.is_available() == True`. bitsandbytes 0.48.2 import OK.
  lerobot 0.4.1, transformers (commit pinned), peft đã cài (`uv pip install -e .`).

### 2. Dữ liệu & model — XONG (đều nằm trên ổ D)
- `HF_HOME=/mnt/d/hf_cache` (model + dataset để trên ổ D vì ổ C chật ~15GB).
- Đã tải: **`lerobot/pi05_base`** (~8GB) và **`lerobot/libero_spatial_image`**
  (52 970 frame, 432 episode).

### 3. Benchmark latency π0.5 — XONG ⭐ (kết quả chính)
- Config: `examples/benchmarks/rtx3050_latency.yaml` (compile off, bf16, 10 flow steps).
- **Kết quả: Mean 4545.90 ms, Median 4540.26 ms, 0.22 FPS.**
- So paper (103 ms trên RTX 4090) → **chậm hơn ~44×**. Chi tiết + diễn giải trong
  **`RESULTS_rtx3050.md`**. Đây là số own-hardware, đủ trả lời Q1.

## File đã thêm vào repo trong phiên này
- `FINETUNE_PLAN.md` — kế hoạch fine-tune đầy đủ (chia gate, có phương án chọn).
- `RESULTS_rtx3050.md` — kết quả benchmark + diễn giải cho thesis.
- `examples/benchmarks/rtx3050_latency.yaml` — config benchmark.
- `PROGRESS_finetune_rtx3050.md` — file này.

## ⚠️ GOTCHAS đã gặp & cách khắc phục (đừng vấp lại)
1. **Python 3.14 quá mới** → không có torch. Dùng uv + Python 3.12.
2. **Không cài package trực tiếp lên /mnt/d** (ổ Windows, lỗi `Operation not permitted`).
   → venv phải ở ổ Linux native; chỉ DỮ LIỆU (model/dataset) mới để /mnt/d.
3. **Tên dataset đúng là `lerobot/libero_spatial_image`** (KHÔNG phải `lerobot/libero_spatial`).
   Là định dạng v3.0, lerobot 0.4.1 đọc được ở chế độ "v2.1 compatibility".
4. **Tokenizer `google/paligemma-3b-pt-224` bị gated** → cần tài khoản HF + bấm "Agree and
   access repository" tại trang model + `hf auth login` dán token (đã làm xong).
5. **Nạp model 8GB bị `Killed` (hết RAM hệ thống)** → đã thêm **swap 32GB trên ổ D** qua
   `C:\Users\ADMIN\.wslconfig` (`[wsl2] swap=32GB / swapFile=D:\wsl\swap.vhdx`).

## Cách RESUME trên máy Windows (mở Ubuntu, chạy)
```bash
cd ~/vlash-thesis
source .venv/bin/activate
export HF_HOME=/mnt/d/hf_cache
# chạy lại benchmark:
vlash benchmark examples/benchmarks/rtx3050_latency.yaml
```
Ghi chú: repo trong WSL (`~/vlash-thesis`) là bản **COPY từ Windows**, chưa nối GitHub auth
(chưa `git push` được từ WSL). Việc commit/push làm từ **GitHub Desktop trên Windows**.

## 🔶 THỬ FINE-TUNE QLoRA — đã chạy được đến vòng train, tạm DỪNG (2026-08-18)

Đã thử Gate 3 (chạy thử QLoRA ngắn 20 step trên `libero_spatial_image`). Kết quả:
- **Nạp model + áp QLoRA 4-bit + gắn LoRA THÀNH CÔNG, KHÔNG OOM** (154M/4B tham số train-được).
  → VRAM 6GB chịu được QLoRA training. Đây là điều quan trọng nhất đã chứng minh.
- Vướng một chuỗi lỗi **lệch kiểu số (dtype)** trong nhánh QLoRA (fp32 vs bf16), đã sửa dần:
  1. `use_state_ground_truth` cho LIBERO (state_dim != action_dim) — sửa xong.
  2. layer_norm fp32 vs bf16 — cast `modules_to_save` sang bf16.
  3. matmul fp32 vs bf16 — quét cast toàn bộ param + buffer sang bf16.
  4. `time_mlp_in` nhận `time_emb` fp32 (time lấy mẫu fp32) — cast input suffix_embedder về bf16.
- Sau fix #4, **tác giả quyết định DỪNG** (benchmark đã đủ cho Q1; train chỉ là bonus).
  Fix #4 chưa được xác nhận chạy ra loss (dừng trước khi test lần cuối).

### File CODE đã sửa trong phiên (để làm QLoRA training chạy trên 6GB — là cải tiến thật)
- `vlash/configs/train_config.py` — thêm field `use_state_ground_truth`.
- `vlash/train.py` — truyền `use_state_ground_truth` vào VLASHDataset/SharedObservationVLASHDataset.
- `vlash/lora/apply.py` — cast toàn bộ param + buffer không-4bit sang compute_dtype (bf16).
- `vlash/policies/pi05/modeling_pi05.py` — cast input của `PI05SuffixEmbedder.forward` (state,
  noisy_actions, time_emb) về compute_dtype để tránh lệch dtype.
- Config train 6GB: `examples/train/pi05/rtx3050.yaml` (chỉ có ở bản WSL, chưa copy về Windows).

### Nếu muốn NỐI TIẾP train sau này
Copy lại `vlash/` từ Windows sang WSL, chạy lại `vlash train examples/train/pi05/rtx3050.yaml`.
Nếu còn 1 lỗi dtype nữa → bọc `torch.autocast("cuda", dtype=bfloat16)` quanh `policy.forward` trong
`update_policy` (vlash/train.py) là dứt điểm. Train đầy đủ đạt SR gần paper vẫn KHÔNG khả thi trên
RTX 3050 (mỗi step nặng); mục tiêu thực tế chỉ là proof-of-pipeline + biểu đồ loss.

## ✅ TRẠNG THÁI CHỐT PHIÊN
- **Deliverable chính cho Q1 = benchmark latency** (`RESULTS_rtx3050.md`) — XONG, an toàn.
- Môi trường + model đã tải vẫn còn trên máy (xem mục "RESUME"), có thể chạy lại bất cứ lúc nào.
- Bước kế: cập nhật Chương 3/4 của thesis với số own-hardware (4546 ms / 0.22 FPS).
```
