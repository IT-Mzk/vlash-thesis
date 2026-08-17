# Kết quả thực nghiệm trên phần cứng của tác giả (RTX 3050 6GB)

> Own-hardware experiments cho thesis VLASH. Chạy trong WSL2/Ubuntu trên laptop Windows 11.
> Đây là số đo của chính tác giả, KHÔNG trích từ paper.

## Cấu hình phần cứng & phần mềm

| Mục | Giá trị |
|---|---|
| GPU | NVIDIA GeForce RTX 3050 Laptop, 6 GB VRAM |
| Driver / CUDA | 576.40 / CUDA 12.9 |
| Môi trường | WSL2 + Ubuntu, Python 3.12, torch 2.7.1+cu126 |
| Model | `lerobot/pi05_base` — π0.5 (PaliGemma-2B + Gemma-300M, ~2.3B tham số) |
| Precision | bfloat16 |
| Flow-matching steps | 10 (`num_inference_steps`) |
| torch.compile | tắt (eager mode) |
| Dataset mẫu | `lerobot/libero_spatial_image` (52 970 frame, 2 camera + state + language) |

## Benchmark 1 — Độ trễ inference của π0.5 (chế độ đồng bộ)

Ngày chạy: 2026-08-17. 16 mẫu đo, 10 bước warmup, batch size 1.

| Chỉ số | Giá trị (ms) |
|---|---|
| Mean | **4545.90** |
| Median | 4540.26 |
| Std | 102.71 |
| Min | 4413.58 |
| Max | 4781.29 |
| P50 | 4540.26 |
| P90 | 4657.89 |
| P95 | 4702.70 |
| P99 | 4765.57 |
| **Throughput** | **0.22 FPS** |

### Diễn giải cho thesis

Paper VLASH báo cáo độ trễ inference của π0.5 là **103 ms trên RTX 4090**. Trên RTX 3050 6GB
(laptop) của tác giả, độ trễ đo được là **≈ 4546 ms — chậm hơn khoảng 44×**, tương đương chỉ
**0.22 lần suy luận mỗi giây**.

Ở tốc độ này, điều khiển robot theo chế độ **đồng bộ** (chờ model trả về action mới hành động)
là hoàn toàn bất khả thi cho thời gian thực. Kết quả này **củng cố trực tiếp động lực của VLASH**:
độ trễ inference càng lớn thì độ lệch giữa trạng thái lúc dự đoán (`s_t`) và lúc thực thi (`s_{t+Δ}`)
càng nghiêm trọng; do đó cơ chế bất đồng bộ + *state rollforward* của VLASH càng thiết yếu trên
phần cứng phổ thông. Nói cách khác, vấn đề mà VLASH giải quyết còn gay gắt hơn trên RTX 3050 so với
trên RTX 4090.

### Ghi chú về điều kiện đo
- `compile_model` tắt và model chạy dưới áp lực bộ nhớ (WSL dùng swap 32 GB trên ổ D để nạp được
  model 2.3B tham số trong giới hạn RAM). Độ trễ "tối ưu" với `torch.compile` + fusion có thể thấp
  hơn, nhưng vẫn cao hơn nhiều lần so với RTX 4090.
- Mỗi lần "inference" gồm 10 bước tích phân flow-matching (10 lượt forward qua model 2.3B), giải
  thích vì sao tổng thời gian ≈ 4.5 s trên GPU laptop.

## Cách tái lập

```bash
# trong WSL, môi trường đã cài (xem FINETUNE_PLAN.md)
cd ~/vlash-thesis
source .venv/bin/activate
export HF_HOME=/mnt/d/hf_cache
vlash benchmark examples/benchmarks/rtx3050_latency.yaml
```
