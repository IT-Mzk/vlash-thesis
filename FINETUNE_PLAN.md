# Kế hoạch fine-tune π0.5 THẬT trên RTX 3050 6GB — VLASH thesis

> ## ⭐ PHƯƠNG ÁN ĐƯỢC CHỌN (cập nhật 2026-08-16) — đọc phần này trước
>
> Bối cảnh: khanh **mới làm lần đầu**, còn **~2 tuần** tới deadline, card **6GB**, ổ C ít
> dung lượng nhưng **ổ D còn >200GB**. Vì vậy đổi mục tiêu từ "đạt SR bằng paper" (rủi ro
> quá cao cho người mới trong 2 tuần) sang hướng **CHẮC ĂN mà vẫn là thí nghiệm thật**:
>
> 1. **ƯU TIÊN 1 — chắc ăn:** dựng môi trường (Gate 0→2) rồi chạy **benchmark latency**
>    trên π0.5 thật (Gate 4b). Cho ra **con số phần cứng của riêng bạn** — "π0.5 inference
>    = X ms trên RTX 3050 → Δ ≈ N bước ở 20Hz". Không cần train, không cần giả lập → gần như
>    chắc chắn ra kết quả. **Đây một mình nó đã trả lời được câu Q1 của thầy.**
> 2. **ƯU TIÊN 2 — bonus (chỉ nếu Ưu tiên 1 xong sớm):** fine-tune QLoRA ngắn trên
>    `libero_spatial` (Gate 3→4a), lấy **biểu đồ loss hội tụ**.
> 3. **BỎ — eval Success Rate (Gate 5):** cần render MuJoCo headless trong WSL, quá dễ kẹt
>    trong 2 tuần. Giữ như "future work" trong thesis (đúng như bản hiện tại).
>
> **Thứ tự vàng: chạy benchmark latency TRƯỚC khi train.** Benchmark dùng model gốc, không
> phụ thuộc train — nên lấy con số an toàn về túi trước, rồi mới thử train như phần thưởng thêm.
>
> Ổ đĩa: mọi thứ nặng (model ~8GB + dataset ~2GB) để trên **ổ D** qua đường dẫn `/mnt/d`
> trong WSL — xem Gate 2. Ổ C chỉ giữ bản Ubuntu gọn.
>
> Bên dưới vẫn giữ đầy đủ các Gate để tham khảo, nhưng bạn chỉ cần bám 3 dòng ưu tiên trên.

---

*(Phần dưới là kế hoạch chi tiết đầy đủ — chia thành các CỔNG (gate). Mỗi cổng là một mốc
kiểm tra; chỉ đi tiếp khi cổng trước PASS. Theo phương án đã chọn, bạn đi Gate 0→2, rồi
Gate 4b (benchmark) trước, sau đó Gate 3→4a nếu còn thời gian, và bỏ Gate 5.)*

---

## 0. Đọc trước — sự thật về phần cứng (đừng bỏ qua)

π0.5 = PaliGemma-2B (vision-language) + Gemma-300M (action expert) ≈ **2.3 tỷ tham số**.
Ngay cả với QLoRA 4-bit, nhét model + activation + optimizer state vào **6GB VRAM** là
cực chật. Chính `THESIS_roadmap_and_error_report.md` của bạn đã xếp việc này:
**"Rất mạnh về học thuật · Thấp/khó khả thi · Rủi ro cao (có thể không chạy xong)."**

Ba nút thắt lớn nhất, theo thứ tự khó:

1. **VRAM khi train** — dễ OOM (Out Of Memory). Gỡ bằng: QLoRA nf4 + `gradient_checkpointing` +
   `batch_size=1` + `grad_accum` cao + giảm `max_delay_steps` + (nếu cần) tắt `shared_observation`.
2. **Tốc độ** — 3050 chậm hơn 4090 (phần cứng gốc của paper) nhiều lần. Lịch train của paper là
   **50 000 step**; trên 3050 điều đó là bất khả thi trong khung thời gian thesis. Ta sẽ train
   **ít step hơn nhiều trên MỘT suite** rồi báo cáo trung thực khoảng cách với paper.
3. **Eval SR** — muốn có con số Success Rate phải **chạy được LIBERO simulator (MuJoCo)** ở chế độ
   headless trong WSL2 (render EGL/OpenGL không màn hình). Đây thường là phần khó nhất, khó hơn cả train.

**Định nghĩa "thành công" thực tế cho thesis (đặt kỳ vọng đúng ngay từ đầu):**
Đạt SR *bằng đúng* paper (95%+) trên 6GB gần như không khả thi. Nhưng một đóng góp
"own experiment" **rất mạnh** và hoàn toàn trong tầm với là:

> "Tôi đã tự fine-tune π0.5 bằng QLoRA trên RTX 3050, train được N step trên LIBERO-Spatial,
> loss hội tụ (có biểu đồ), đo latency inference thật trên card của mình, chạy eval và đạt
> SR = X% — thấp hơn paper vì ngân sách tính toán hạn chế, và tôi phân tích rõ vì sao."

Con số đó **là số của chính bạn** → mạnh hơn nhiều so với chỉ trích lại bảng paper. Cả khi
không chạm được SR của paper, Gate 3–4 dưới đây vẫn cho bạn một chương thực nghiệm đầy đủ.

**Ước lượng tài nguyên:** cần **~40–50GB đĩa trống** (base model ~8GB + dataset ~2GB +
môi trường ~15GB + checkpoint/outputs). Thời gian: 1 buổi setup + nhiều giờ đến vài ngày train.

---

## GATE 0 — Xác minh môi trường (làm NGAY, ~15 phút)

Mục tiêu: biết chính xác máy đang có gì để không cài lại thừa. Mở **PowerShell** chạy:

```powershell
wsl --status                 # WSL2 đã cài chưa? distro mặc định là gì?
wsl -l -v                    # liệt kê distro + version (cần VERSION = 2)
nvidia-smi                   # driver Windows + tên GPU (phải thấy "RTX 3050")
Get-PSDrive C | Select-Object Used,Free   # dung lượng trống ổ C (cần >50GB)
```

Nếu đã có Ubuntu trong WSL2, mở nó (`wsl`) rồi chạy tiếp:

```bash
nvidia-smi                   # trong Ubuntu PHẢI thấy RTX 3050 (driver Windows tự expose)
python3 --version
df -h ~                      # dung lượng trống trong WSL
free -h                      # RAM (khuyến nghị ≥16GB để dataloader không nghẽn)
```

**→ Copy toàn bộ output gửi lại cho tôi.** Dựa vào đó tôi chốt chính xác bạn bắt đầu từ
Gate 1 (cài mới) hay nhảy thẳng Gate 2. **PASS khi:** `nvidia-smi` trong Ubuntu thấy RTX 3050,
và ổ C còn > 50GB.

---

## GATE 1 — Nền tảng WSL2 + driver (bỏ qua nếu Gate 0 đã có sẵn)

`bitsandbytes` (QLoRA 4-bit) chạy Linux ổn hơn Windows nhiều → **bắt buộc train trong WSL2**.

```powershell
# PowerShell (Admin) — cài Ubuntu, xong khởi động lại máy
wsl --install -d Ubuntu-24.04
```

- Cài **driver NVIDIA mới nhất cho Windows** (từ trang NVIDIA hoặc GeForce Experience).
  Driver Windows tự expose GPU vào WSL — **KHÔNG cài driver NVIDIA bên trong Ubuntu** (sẽ hỏng).
- Kiểm tra: trong Ubuntu gõ `nvidia-smi`, phải thấy RTX 3050 và mức VRAM 6144 MiB.

**PASS khi:** `nvidia-smi` trong Ubuntu hiển thị đúng card.

---

## GATE 2 — Môi trường Python + cài VLASH (trong Ubuntu/WSL, ~30–45 phút)

**Đĩa: đưa mọi thứ nặng sang ổ D (>200GB).** Trong WSL, ổ D của Windows chính là `/mnt/d`.
Ta clone code và để cache model/dataset ở đó để ổ C khỏi đầy:

```bash
# tạo thư mục làm việc trên ổ D + bắt HuggingFace cache về ổ D (dòng này lưu vĩnh viễn)
mkdir -p /mnt/d/vlash_work /mnt/d/hf_cache
echo 'export HF_HOME=/mnt/d/hf_cache' >> ~/.bashrc && source ~/.bashrc
cd /mnt/d/vlash_work
```

```bash
sudo apt update && sudo apt install -y python3-venv python3-pip git build-essential

# Lấy code từ repo riêng của bạn (đã có trên GitHub: IT-Mzk/vlash-thesis)
git clone https://github.com/IT-Mzk/vlash-thesis.git
cd vlash-thesis

python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip

# PyTorch bản CUDA (khớp CUDA 12.x của driver)
pip install torch --index-url https://download.pytorch.org/whl/cu121

# Cài vlash + toàn bộ dependency theo pyproject (lerobot 0.4.1, peft, bitsandbytes, transformers pinned)
pip install -e .
```

Kiểm tra GPU nhìn thấy từ PyTorch:

```bash
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
# Kỳ vọng in ra: ... True NVIDIA GeForce RTX 3050 ...
```

Kiểm tra bitsandbytes bắt được CUDA (đây là mắt xích hay hỏng nhất):

```bash
python -c "import bitsandbytes as bnb; print('bnb OK')"
```

**PASS khi:** cả hai lệnh trên chạy sạch, không lỗi CUDA/bitsandbytes.
Nếu lỗi `bitsandbytes`: gần như luôn do sai bản CUDA — báo tôi log, tôi chỉ cách vá.

---

## GATE 3 — "Model sống" trên card: tải + 1 training step KHÔNG OOM (~1 buổi)

Đây là cổng quan trọng nhất. Trước khi mơ tới SR, phải chứng minh **một** step train chạy
được trong 6GB. Nếu OOM ở đây thì mọi thứ phía sau vô nghĩa — nên ta test sớm và rẻ.

### 3a. Tải sẵn base model + dataset (một lần)

```bash
# Base π0.5 (~8GB) và LIBERO-Spatial (~2GB) — tải về cache HuggingFace
huggingface-cli download lerobot/pi05_base
huggingface-cli download lerobot/libero_spatial --repo-type dataset
```

> Ghi chú: `libero_spatial` là suite nhỏ, phù hợp làm suite đầu tiên. Các suite khác
> (`libero_object`, `libero_goal`, `libero_10`) để dành sau nếu Gate 4 dư thời gian.

### 3b. Tạo config cho 6GB — `examples/train/pi05/rtx3050.yaml`

Lấy `async_lora.yaml` làm gốc và siết cho vừa 6GB. Điểm khác so với bản gốc:

```yaml
policy:
  type: pi05
  pretrained_path: lerobot/pi05_base
  dtype: bfloat16
  device: cuda
  state_cond: true            # BẮT BUỘC cho VLASH (bật AdaRMS dùng state)
  gradient_checkpointing: true # ĐỔI compute lấy VRAM — gần như bắt buộc trên 6GB

dataset:
  repo_id: lerobot/libero_spatial
  video_backend: torchcodec

output_dir: outputs/train/pi05_rtx3050
job_name: pi05_rtx3050
batch_size: 1
grad_accum_steps: 16          # batch hiệu dụng = 16
steps: 3000                   # GATE 3 chỉ cần chạy ~20 step để test OOM; số thật đặt ở Gate 4
num_workers: 2                # 3050 laptop: để thấp cho đỡ nghẽn RAM
seed: 1000

use_policy_training_preset: false
optimizer: { type: adamw, lr: 5.0e-5, betas: [0.9, 0.95], weight_decay: 1.0e-10 }
scheduler: { type: cosine_decay_with_warmup, num_warmup_steps: 200, peak_lr: 5.0e-5, decay_lr: 2.5e-6, num_decay_steps: 3000 }

save_checkpoint: true
save_freq: 1000
log_freq: 20
wandb: { enable: false }      # tắt để đơn giản; loss vẫn in ra console

max_delay_steps: 4            # giảm từ 8 → tiết kiệm VRAM & tăng tốc
shared_observation: false     # TẮT trước để giảm activation memory; bật lại ở Gate 4 nếu VRAM dư

lora:
  enable: true
  backend: peft
  r: 16
  alpha: 16
  dropout: 0
  use_qlora: true             # BẮT BUỘC với 6GB (4-bit nf4)
  qlora_quant_type: nf4
  qlora_compute_dtype: bfloat16
  extra_trainable_modules:    # NHỮNG module này train FULL, không phải LoRA — sống còn với VLASH
    - action_in_proj
    - action_out_proj
    - time_mlp_in
    - time_mlp_out
    - state_proj
    - state_mlp_in
    - state_mlp_out
    - embeddings
    - input_layernorm
    - post_attention_layernorm
  target_modules: [q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj, out_proj, fc1, fc2]
```

### 3c. Chạy thử — canh VRAM ở terminal thứ 2

```bash
# Terminal 1:
vlash train examples/train/pi05/rtx3050.yaml
# Terminal 2 (canh VRAM realtime — nếu chạm ~6GB là sắp OOM):
watch -n 1 nvidia-smi
```

**PASS khi:** vượt qua ~20 step, loss có in ra và đang giảm dần, **không** OOM.
Lúc này Ctrl+C dừng lại — Gate 3 chỉ cần chứng minh pipeline sống.

**Nếu OOM** — hạ theo thứ tự (dừng ngay khi hết OOM):
1. `gradient_checkpointing: true` (nếu chưa) → 2. `max_delay_steps: 2` →
3. `shared_observation: false` (nếu đang true) → 4. giảm `num_workers: 0` →
5. báo tôi log để cân nhắc optimizer 8-bit (`paged_adamw_8bit`, cần chỉnh code một chút).

---

## GATE 4b — Benchmark latency trên π0.5 thật ⭐ (ƯU TIÊN 1 — làm phần này TRƯỚC)

> Chạy được ngay sau Gate 2, **không cần train, không cần Gate 3**. Đây là con số an toàn nhất.

```bash
vlash benchmark examples/benchmarks/inference_latency.yaml
```

Ghi lại ms/inference trên RTX 3050 → suy ra Δ (số action bị trễ) ở 20Hz. Kỳ vọng ~180–250ms
→ Δ ≈ 3–5 bước. **Đây là con số phần cứng của riêng bạn** — vào thẳng Chương 3, và một mình
nó đã đủ trả lời Q1. Nếu benchmark OOM (hiếm, vì inference nhẹ hơn train): báo tôi, ta bật
4-bit cho inference.

**PASS khi:** có một con số latency đo thật trên RTX 3050. *Xong cái này là bạn đã có
đóng góp own-experiment an toàn về túi — mọi thứ sau đây chỉ là điểm cộng.*

---

## GATE 4a — Fine-tune QLoRA ngắn (ƯU TIÊN 2 — bonus, chỉ nếu 4b xong sớm)

Khi Gate 3 PASS, mở `steps` lên mức thực tế và để chạy dài. Chiến lược "gần SR paper" trên 6GB:

- **Tập trung MỘT suite** (`libero_spatial`) thay vì cả 4 — dồn toàn bộ ngân sách step vào đó.
- Đặt `steps` theo tốc độ đo được: sau Gate 3 bạn biết ~ số giây/step → chọn số step chạy vừa
  qua đêm hoặc vài ngày. Ví dụ nếu ~3 s/step thì 10 000 step ≈ 8 tiếng.
- `save_freq` hợp lý (vd 2000) để mất điện/treo vẫn resume được (`auto_resume` tự tìm checkpoint).
- Theo dõi loss giảm và ổn định. Xuất **biểu đồ loss** → 1 hình cho Chương 3.

**PASS khi:** có checkpoint đã train + biểu đồ loss hội tụ. Ghép với con số latency ở Gate 4b
là bạn đã có một "own experiment" đủ mạnh cho thesis, kể cả khi chưa eval SR.

---

## GATE 5 — Eval Success Rate trên LIBERO (khó nhất — chỉ làm nếu Gate 4 xong sớm)

Đây là bước cho ra con số **SR** để so với paper. Rào cản: phải chạy được **LIBERO/MuJoCo
render headless** trong WSL2 (không có màn hình → cần EGL/OSMesa). Đây là phần hay vỡ nhất.

Kế hoạch khi tới đây (tôi sẽ hướng dẫn chi tiết từng lệnh lúc đó, vì phụ thuộc phiên bản):
1. Cài LIBERO benchmark + robosuite/MuJoCo trong WSL, set `MUJOCO_GL=egl` (render không màn hình).
2. Chạy eval policy đã train trên `libero_spatial` ở Δ = 1–4, chế độ Sync / Naive-Async / VLASH.
3. Lập bảng SR của **chính bạn**, đặt cạnh bảng paper, **phân tích khoảng cách** (ít step, 1 suite,
   6GB) — phần phân tích trung thực này chính là điểm mạnh học thuật, không phải điểm yếu.

**PASS khi:** có ít nhất một dòng SR đo được từ model của bạn. Nếu render headless không lên
được trong thời gian cho phép → **fallback**: giữ Gate 4 (train loss + latency thật) làm đóng góp
own-experiment, và trình bày eval SR như "đã setup, chặn ở render headless" — vẫn hợp lệ.

---

## Bản đồ đưa kết quả vào thesis (Chương 3 / §4.1)

| Có được từ | Đưa vào |
|---|---|
| Gate 3 | Một câu: "pipeline QLoRA chạy được trên RTX 3050 6GB" + cấu hình đã dùng |
| Gate 4 | Biểu đồ loss hội tụ (1 hình) + bảng latency đo thật trên 3050 → mục thực nghiệm mới |
| Gate 5 | Bảng SR của riêng bạn cạnh bảng paper + phân tích khoảng cách |
| Nếu Gate 5 chặn | Trình bày như giới hạn phần cứng + hướng future work — vẫn là đóng góp thật |

Việc này chuyển §4.1 từ "future work" thành **một chương thực nghiệm own-data** → đúng yêu cầu Q1.

---

## Quy tắc 2 máy khi làm

- Code/config sửa trong WSL: `git add -A && git commit -m "..." && git push` để đồng bộ.
- Checkpoint và dataset **không** commit lên GitHub (quá nặng) — `.gitignore` đã loại `outputs/`.
- Khi cần tôi hỗ trợ ở máy Windows: mở Cowork, chọn folder, dán log lỗi vào — tôi đọc được ngay.

## Bước kế tiếp NGAY BÂY GIỜ

Chạy **GATE 0** ở trên và gửi tôi output. Tôi sẽ chốt điểm bắt đầu và đưa lệnh cụ thể cho gate tiếp theo.
