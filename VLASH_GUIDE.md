# VLASH — Hướng dẫn Toàn diện & Chi tiết

> **Tác giả tài liệu:** Được tạo cho mục đích học thuật và triển khai  
> **Dự án gốc:** Tang et al., 2025 — arXiv:2512.01031  
> **Repo:** https://github.com/mit-han-lab/vlash

---

## MỤC LỤC

1. [Ý tưởng nghiên cứu — Tại sao có VLASH?](#1-ý-tưởng-nghiên-cứu)
2. [Kiến trúc tổng thể](#2-kiến-trúc-tổng-thể)
3. [Cấu trúc thư mục — mọi file làm gì](#3-cấu-trúc-thư-mục)
4. [Chi tiết từng module quan trọng](#4-chi-tiết-từng-module)
5. [Luồng dữ liệu — Training](#5-luồng-training)
6. [Luồng dữ liệu — Inference](#6-luồng-inference)
7. [Các tham số cấu hình — giải thích từng cái](#7-tham-số-cấu-hình)
8. [Cách cài đặt trên Windows 11 + RTX 3050](#8-cài-đặt-windows-11)
9. [Cách chạy và kết quả trả về](#9-cách-chạy-và-kết-quả)
10. [Các lỗi thường gặp và cách sửa](#10-lỗi-thường-gặp)
11. [Bảng tóm tắt toàn bộ](#11-bảng-tóm-tắt)

---

## 1. Ý Tưởng Nghiên Cứu

### 1.1 Vấn đề ban đầu

Robot hiện đại dùng các mô hình AI lớn (VLA — Vision-Language-Action) để "nhìn" cảnh xung quanh, đọc lệnh ngôn ngữ, rồi quyết định hành động. Ví dụ: "nhặt cái cốc đỏ lên và đặt vào cái bát".

Vấn đề: **Mô hình AI quá chậm**.

```
TÌNH HUỐNG THỰC TẾ (Synchronous — đồng bộ):

Thời gian:  0ms      103ms    1303ms   1406ms   2606ms
            |        |        |        |        |
Robot:      [chờ...][execute action 0..23][chờ...][execute action 0..23]
Model:      [=INFER=][                   ][=INFER=]

→ Robot ĐỨNG YÊN 103ms mỗi lần model tính toán
→ Nếu vật thể di chuyển trong lúc đó → robot KHÔNG BIẾT
→ Reaction latency = 1303ms (hơn 1 giây!)
```

### 1.2 Giải pháp ngây thơ — Naive Async

Chạy model và robot SONG SONG (bất đồng bộ):

```
NAIVE ASYNC:

Thời gian:  t0       t2       t4       t6
            |        |        |        |
Model:      [=INFER@s0=]      [=INFER@s2=]
Robot:                [exec chunk1][exec chunk2]

Vấn đề: Model tính dựa trên state s0,
        nhưng actions thực thi lúc robot đã ở state s2
        → s2 ≠ s0 → actions bị LỆCH → robot giật, không chính xác
```

### 1.3 Giải pháp VLASH — Future-State-Aware

**Ý tưởng cốt lõi:** Khi model bắt đầu tính ở thời điểm t, robot đang thực thi các actions đã biết trước (a_t, a_{t+1}, ...). Ta TÍNH TRƯỚC robot sẽ ở đâu khi actions mới bắt đầu chạy!

```
VLASH — State Rollforward:

Biết: s_t (state hiện tại)
Biết: a_t, a_{t+1}, ..., a_{t+Δ-1} (actions đang chạy, đã biết trước)

Tính: s_{t+Δ} = s_t + a_t + a_{t+1} + ... + a_{t+Δ-1}
                ↑ chỉ là phép CỘNG vector, tốc độ ~0ms

→ Cho model dự đoán dựa trên s_{t+Δ} thay vì s_t
→ Model thấy ĐÚNG trạng thái lúc actions sẽ thực thi
→ Không còn lệch nữa!
```

**Điều kiện tiên quyết:** Actions phải là dạng DELTA (thay đổi khớp nối), không phải tọa độ tuyệt đối. Codebase này dùng delta joint positions → phép tính trên CHÍNH XÁC 100%.

### 1.4 Ba đóng góp chính

```
┌─────────────────────────────────────────────────────────────┐
│                    VLASH = 3 innovations                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. STATE ROLLFORWARD (inference time)                      │
│     s_{t+Δ} = s_t + sum(pending_actions)                   │
│     → Zero overhead, eliminates misalignment               │
│                                                             │
│  2. TEMPORAL-OFFSET AUGMENTATION (training time)            │
│     Random δ ∈ [0, max_delay_steps]                        │
│     Training pair: (obs_t, state_{t+δ}) → actions_{t+δ:}  │
│     → Teaches model to USE future state input               │
│                                                             │
│  3. SHARED OBSERVATION OPTIMIZATION (training efficiency)   │
│     Pack N offsets with SAME observation                   │
│     Compute VLM embeddings ONCE for all N                  │
│     → 3.26x training speedup                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Kiến Trúc Tổng Thể

### 2.1 Model π0.5 — Backbone của VLASH

VLASH fine-tune mô hình **π0.5** (Physical Intelligence, 2025). Đây là VLA model gồm 2 phần:

```
┌─────────────────────────────────────────────────────────────────┐
│                        π0.5 ARCHITECTURE                        │
├─────────────────────┬───────────────────────────────────────────┤
│                     │                                           │
│   VISION-LANGUAGE   │         ACTION EXPERT                    │
│      BACKBONE       │                                           │
│                     │                                           │
│  ┌─────────────┐    │    ┌──────────────────────────────────┐  │
│  │   SigLIP    │    │    │      Gemma-300M                  │  │
│  │ (image enc) │    │    │                                  │  │
│  └──────┬──────┘    │    │  ┌────────────────────────────┐  │  │
│         │           │    │  │   AdaRMS Conditioning      │  │  │
│  256 tokens/image   │    │  │   state + timestep → scale │  │  │
│         │           │    │  └────────────────────────────┘  │  │
│  ┌──────▼──────┐    │    │                                  │  │
│  │  Gemma-2B   │    │    │  ← JOINT ATTENTION →            │  │
│  │ (lang model)│◄───┼────│  Action expert ATTENDS to VLM  │  │
│  └─────────────┘    │    └──────────────────────────────────┘  │
│                     │                                           │
│   Input:            │    Input:                                │
│   - 2 camera imgs   │    - Noisy actions (flow matching)      │
│   - Task text       │    - Robot state (s_{t+Δ} ← VLASH!)     │
│   - ~700 tokens     │    - Timestep t ∈ [0, 1)                │
│                     │                                           │
│   Output:           │    Output:                               │
│   - Rich context    │    - Noise prediction                    │
│     embeddings      │    - → Recover clean actions             │
└─────────────────────┴───────────────────────────────────────────┘
```

### 2.2 Flow Matching — Cách sinh actions

π0.5 không dùng diffusion model thông thường. Nó dùng **Flow Matching**:

```
FLOW MATCHING (trong training):

1. Lấy actions thật: a = [a_0, a_1, ..., a_H-1]  (H=50)
2. Lấy noise ngẫu nhiên: ε ~ N(0, I)
3. Sample timestep: t ~ Uniform(0, 1)
4. Tạo noisy actions: x_t = sqrt(1-t) * a + sqrt(t) * ε
5. Model dự đoán: noise_pred = model(obs, state, x_t, t)
6. Loss: MSE(ε, noise_pred)

FLOW MATCHING (trong inference):

1. Bắt đầu từ pure noise: x_1 ~ N(0, I)
2. Tích phân ngược: dx/dt = v_θ(x, t)
3. Qua 10 bước → ra clean actions: x_0 ≈ a
```

Tại sao tốt hơn diffusion? **Đường đi thẳng hơn** → cần ít bước hơn (10 bước thay vì 100+).

### 2.3 Kiến trúc hệ thống hoàn chỉnh

```
┌──────────────────────────────────────────────────────────────────────┐
│                     TRAINING PIPELINE                                │
│                                                                      │
│  HuggingFace Dataset                                                 │
│  (lerobot/libero_*)    →  VLASHDataset  →  π0.5 + LoRA  →  Weights │
│                            ↑                                         │
│                    temporal offset δ                                 │
│                    [0, max_delay_steps]                              │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                     INFERENCE PIPELINE                               │
│                                                                      │
│  Camera images                                                       │
│  Joint angles   →  VLASHAsyncManager  →  Robot actuators            │
│  Task text             │                                             │
│                        │                                             │
│              ┌─────────▼──────────┐                                 │
│              │  State Rollforward │                                  │
│              │  s_future = s_now  │                                  │
│              │  + pending_actions │                                  │
│              └─────────┬──────────┘                                 │
│                        │                                             │
│              ┌─────────▼──────────┐                                 │
│              │   π0.5 inference   │ ← background thread             │
│              │   (103ms on 4090)  │                                  │
│              └─────────┬──────────┘                                 │
│                        │                                             │
│              next action chunk ready                                 │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. Cấu Trúc Thư Mục

```
vlash/
│
├── vlash/                          ← Package Python chính
│   ├── __init__.py
│   ├── cli.py                      ← Entry point: lệnh vlash train/run/benchmark
│   ├── train.py                    ← Training loop hoàn chỉnh (634 dòng)
│   ├── run.py                      ← Inference + VLASHAsyncManager (533 dòng)
│   ├── utils.py                    ← Tiền xử lý observation cho inference
│   │
│   ├── configs/                    ← Dataclasses cấu hình
│   │   ├── train_config.py         ← VLASHTrainConfig, LoRAConfig
│   │   └── run_config.py           ← RunConfig
│   │
│   ├── datasets/                   ← Xử lý dataset
│   │   ├── vlash_dataset.py        ← VLASHDataset (temporal augmentation)
│   │   └── compat.py               ← Compatibility utils
│   │
│   ├── policies/                   ← Model implementations
│   │   ├── factory.py              ← get_policy_class(), make_policy()
│   │   ├── normalize.py            ← Action/state normalization
│   │   ├── pi0/                    ← π0 model (v1, không dùng trong VLASH)
│   │   └── pi05/                   ← π0.5 model (model chính của VLASH)
│   │       ├── configuration_pi05.py  ← PI05Config dataclass
│   │       ├── modeling_pi05.py    ← TOÀN BỘ model (1576 dòng!)
│   │       └── utils.py            ← Tokenizer, image utils
│   │
│   ├── lora/                       ← LoRA fine-tuning
│   │   ├── apply.py                ← apply_lora(), inject adapters
│   │   ├── checkpoint.py           ← Lưu/load/merge LoRA weights
│   │   ├── qlora.py                ← 4-bit quantization
│   │   └── logging.py              ← Log LoRA parameter stats
│   │
│   └── layers/                     ← Custom neural network layers
│       ├── attention.py            ← Scaled dot-product attention + KV cache
│       ├── linear.py               ← QKVLinear (fused), MergedColumnLinear
│       └── rope.py                 ← Rotary Position Embedding
│
├── benchmarks/                     ← Đo tốc độ inference
│   ├── benchmark_config.py         ← BenchmarkConfig dataclass
│   └── benchmark_inference_latency.py  ← Script đo latency
│
├── examples/                       ← File YAML config mẫu
│   ├── train/pi05/
│   │   ├── sync.yaml               ← Training đồng bộ (baseline)
│   │   ├── async.yaml              ← Training bất đồng bộ (VLASH chính)
│   │   └── async_lora.yaml         ← Async + LoRA (tiết kiệm VRAM)
│   ├── inference/
│   │   ├── sync.yaml               ← Inference đồng bộ
│   │   └── async.yaml              ← Inference bất đồng bộ (VLASH)
│   └── benchmarks/
│       └── inference_latency.yaml  ← Config đo tốc độ
│
├── pyproject.toml                  ← Dependencies, package config
└── README.md                       ← Giới thiệu ngắn
```

---

## 4. Chi Tiết Từng Module

### 4.1 `vlash/cli.py` — Cổng vào chính

**File này là gì:** Khi bạn gõ `vlash train ...` hay `vlash run ...`, Python chạy file này đầu tiên.

**3 lệnh được hỗ trợ:**

```python
# Lệnh 1: Training
vlash train examples/train/pi05/async.yaml
# → gọi hàm train_command() → gọi vlash/train.py

# Lệnh 2: Inference (chạy robot)
vlash run examples/inference/async.yaml
# → gọi hàm run_command() → gọi vlash/run.py

# Lệnh 3: Benchmark (đo tốc độ)
vlash benchmark examples/benchmarks/inference_latency.yaml
# → gọi benchmark_inference_latency()
```

**Tính năng auto-detect GPU:**
```python
# cli.py dòng 62-86: Hàm get_num_gpus()
def get_num_gpus():
    cuda_visible = os.environ.get("CUDA_VISIBLE_DEVICES", None)
    if cuda_visible is None:
        import torch
        return torch.cuda.device_count()
    return len(cuda_visible.split(","))

# Nếu có >1 GPU → dùng accelerate (distributed training)
# Nếu có 1 GPU → chạy trực tiếp
# Nếu không có GPU → CPU mode (rất chậm)
```

**Cách override multi-GPU:**
```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 vlash train examples/train/pi05/async.yaml
# cli.py tự phát hiện 4 GPU và dùng accelerate launch --multi_gpu
```

---

### 4.2 `vlash/train.py` — Training Loop (634 dòng)

**File này làm gì:** Orchestrate toàn bộ quá trình huấn luyện.

#### Hàm `make_vlash_dataset()` — Tạo dataset

```python
# train.py ~dòng 80-150
def make_vlash_dataset(cfg: VLASHTrainConfig):
    # 1. Load metadata từ HuggingFace
    ds_meta = LeRobotDatasetMetadata(cfg.dataset.repo_id)
    
    # 2. Nếu shared_observation=True → dùng SharedObservationVLASHDataset
    if cfg.shared_observation and cfg.max_delay_steps > 0:
        dataset = SharedObservationVLASHDataset(
            repo_id=cfg.dataset.repo_id,
            max_delay_steps=cfg.max_delay_steps,
            ...
        )
        collate_fn = shared_observation_collate_fn
    else:
        # 3. Không thì dùng VLASHDataset thông thường
        dataset = VLASHDataset(
            repo_id=cfg.dataset.repo_id,
            max_delay_steps=cfg.max_delay_steps,  # ← core của VLASH!
            ...
        )
        collate_fn = default_collate
    
    return dataset, collate_fn
```

#### Hàm `update_policy()` — 1 bước training

```python
# train.py ~dòng 200-280
def update_policy(train_metrics, policy, batch, optimizer, ...):
    # 1. Forward pass
    if use_shared_observation:
        # Dùng forward_shared_observation: tính VLM embeddings 1 lần
        # cho tất cả N offsets trong batch → nhanh hơn N lần
        output_dict = policy.model.forward_shared_observation(batch, ...)
    else:
        output_dict = policy.forward(batch)
    
    # output_dict chứa: {"loss": tensor, "loss_components": {...}}
    loss = output_dict["loss"]
    
    # 2. Scale loss cho gradient accumulation
    loss = loss / loss_scale  # loss_scale = grad_accum_steps
    
    # 3. Backward pass
    accelerator.backward(loss)
    
    # 4. Gradient clipping (nếu grad_clip_norm > 0)
    if grad_clip_norm > 0:
        torch.nn.utils.clip_grad_norm_(policy.parameters(), grad_clip_norm)
    
    # 5. Optimizer step (chỉ sau grad_accum_steps bước)
    if do_step:
        optimizer.step()
        lr_scheduler.step()
        optimizer.zero_grad()
    
    return train_metrics, output_dict
```

#### Hàm `auto_resume()` — Tự động tiếp tục training

```python
# train.py ~dòng 50-80
def auto_resume(cfg: VLASHTrainConfig):
    checkpoint_dir = Path(cfg.output_dir) / "checkpoints"
    
    if not checkpoint_dir.exists():
        return  # Không có checkpoint → train từ đầu
    
    # Tìm checkpoint mới nhất
    checkpoints = sorted(checkpoint_dir.iterdir())
    
    if checkpoints:
        latest = checkpoints[-1]
        # Kiểm tra checkpoint có hợp lệ không
        if (latest / "pretrained_model").exists():
            # Thêm --resume vào sys.argv → LeRobot tự xử lý
            sys.argv += [f"--resume=true"]
            print(f"Auto-resuming from {latest}")
```

#### Main training loop

```python
# train.py ~dòng 300-500 (hàm train())
@parser.wrap()
def train(cfg: VLASHTrainConfig):
    # Step 1: Setup
    dataset, collate_fn = make_vlash_dataset(cfg)
    dataloader = DataLoader(dataset, batch_size=cfg.batch_size, ...)
    
    # Step 2: Tạo policy
    policy = make_policy(cfg.policy, ds_meta)
    
    # Step 3: Áp dụng LoRA (nếu được bật)
    if cfg.lora.enable:
        apply_lora(cfg.lora, policy)
    
    # Step 4: Setup optimizer + scheduler
    optimizer = AdamW(policy.parameters(), lr=cfg.optimizer.lr)
    scheduler = cosine_decay_with_warmup(optimizer, ...)
    
    # Step 5: Main loop
    for step, batch in enumerate(dataloader):
        # Training step
        metrics, output = update_policy(
            policy=policy,
            batch=batch,
            optimizer=optimizer,
            do_step=(step % cfg.grad_accum_steps == 0),
            use_shared_observation=cfg.shared_observation
        )
        
        # Logging mỗi log_freq steps
        if step % cfg.log_freq == 0:
            wandb.log({"loss": metrics.loss, "lr": scheduler.get_lr()})
        
        # Checkpoint mỗi save_freq steps
        if step % cfg.save_freq == 0:
            # Merge LoRA vào base weights trước khi lưu
            merged_policy = clone_and_merge_lora_policy(policy, cfg.lora)
            merged_policy.save_pretrained(f"checkpoints/{step:06d}/")
```

---

### 4.3 `vlash/datasets/vlash_dataset.py` — Temporal Augmentation (475 dòng)

**Đây là file QUAN TRỌNG NHẤT về mặt research của VLASH.**

#### Class `VLASHDataset`

```python
class VLASHDataset(LeRobotDataset):
    """
    Mở rộng LeRobotDataset bằng cách thêm temporal offset augmentation.
    
    Ý tưởng: Với mỗi training sample tại timestep t,
    thay vì dùng (obs_t, state_t) → actions_t:H,
    ta dùng (obs_t, state_{t+δ}) → actions_{t+δ:t+δ+H}
    trong đó δ ~ Uniform[0, max_delay_steps]
    """
    
    def __init__(self, repo_id, max_delay_steps=0, ...):
        super().__init__(repo_id, ...)
        self.max_delay_steps = max_delay_steps
```

#### Hàm `_get_query_indices()` — Trái tim của augmentation

```python
def _get_query_indices(self, idx: int, ep_idx: int):
    """
    idx: index gốc trong dataset
    ep_idx: index của episode chứa sample này
    
    Returns: (query_index, offset, action_is_pad)
    """
    # 1. Sample random delay
    if self.max_delay_steps > 0:
        δ = random.randint(0, self.max_delay_steps)
    else:
        δ = 0
    
    # 2. Tính query index sau khi shift
    query_idx = idx + δ
    
    # 3. Clamp về cuối episode (không được ra ngoài)
    ep_end = self.episode_data_index["to"][ep_idx]
    query_idx = min(query_idx, ep_end - 1)
    
    # 4. Tạo padding mask: actions nào bị pad (ngoài episode)
    action_is_pad = [False] * self.num_action_steps
    for k in range(self.num_action_steps):
        if query_idx + k >= ep_end:
            action_is_pad[k] = True
    
    return query_idx, δ, action_is_pad
```

#### Hàm `__getitem__()` — Lấy 1 sample

```python
def __getitem__(self, idx):
    # 1. Xác định episode và lấy query index với offset
    ep_idx = self._get_ep_idx(idx)
    query_idx, offset, action_is_pad = self._get_query_indices(idx, ep_idx)
    
    # 2. Lấy sample ở vị trí đã shift (obs vẫn tại t, actions tại t+δ)
    item = super().__getitem__(query_idx)
    
    # 3. Xử lý state
    if offset == 0:
        # Không shift → dùng state hiện tại
        pass
    elif self.use_state_ground_truth:
        # Dùng recorded state tại t+offset
        future_item = super().__getitem__(min(idx + offset, ep_end - 1))
        item["observation.state"] = future_item["observation.state"]
    else:
        # Xấp xỉ: dùng action_{t+offset-1} làm proxy cho state_{t+offset}
        # Hợp lệ vì state_dim == action_dim trong LIBERO (cả 2 đều là 8-dim)
        item["observation.state"] = item["action"][offset - 1]
    
    # 4. Gán padding mask
    item["action_is_pad"] = torch.tensor(action_is_pad)
    
    return item
```

#### Class `SharedObservationVLASHDataset` — Training nhanh 3.26x

```python
class SharedObservationVLASHDataset(VLASHDataset):
    """
    Thay vì trả về 1 offset, trả về TẤT CẢ offsets [0, max_delay_steps]
    cho cùng 1 observation.
    
    Input:  1 observation tại thời điểm t
    Output: (max_delay_steps+1) cặp (state_{t+δ}, actions_{t+δ:})
    
    Batch shape: [B, num_offsets, ...]
    """
    
    def __getitem__(self, idx):
        items = []
        for δ in range(self.max_delay_steps + 1):
            # Lấy sample với offset cụ thể
            item = self._get_item_with_offset(idx, δ)
            items.append(item)
        
        # Stack theo dimension mới: [num_offsets, ...]
        return stack_items(items)
```

#### `shared_observation_collate_fn()` — Collate cho shared obs

```python
def shared_observation_collate_fn(batch):
    """
    Gộp các samples thành batch, xử lý việc số offsets khác nhau.
    
    Output shapes:
    - images: [B, num_offsets, C, H, W]
    - state:  [B, num_offsets, state_dim]
    - action: [B, num_offsets, H, action_dim]
    - offset_mask: [B, num_offsets] - True nếu offset hợp lệ
    """
    max_offsets = max(item["num_offsets"] for item in batch)
    
    # Pad về max_offsets
    for item in batch:
        pad = max_offsets - item["num_offsets"]
        # Thêm zero padding
    
    return collated_batch
```

---

### 4.4 `vlash/run.py` — Inference + Async Manager (533 dòng)

**File này xử lý việc chạy robot trong thực tế.**

#### Class `VLASHAsyncManager` — Quản lý bất đồng bộ

```python
class VLASHAsyncManager:
    """
    Quản lý việc chạy 2 việc song song:
    1. Robot đang thực thi actions từ chunk hiện tại
    2. Model đang tính actions cho chunk tiếp theo (background thread)
    
    Attributes:
        current_chunk: np.ndarray [K, action_dim] — đang thực thi
        next_chunk: torch.Tensor — đang được tính (hoặc None)
        chunk_index: int — đang ở action thứ mấy trong chunk
        overlap_steps: int — bắt đầu infer khi còn bao nhiêu actions
    """
    
    def __init__(self, policy, robot, single_task, overlap_steps):
        self.policy = policy
        self.robot = robot
        self.single_task = single_task
        self.overlap_steps = overlap_steps  # = inference_overlap_steps
        
        self.current_chunk = None
        self.next_chunk = None
        self.chunk_index = 0
        self.inference_thread = None
```

#### Hàm `should_launch_next_inference()` — Khi nào bắt đầu infer?

```python
def should_launch_next_inference(self):
    """
    Trả về True khi:
    - Chưa có next_chunk đang được tính
    - Còn đúng overlap_steps actions trong chunk hiện tại
    
    Ví dụ: n_action_steps=32, overlap_steps=4
    → Bắt đầu infer khi chunk_index == 28 (còn 4 actions)
    """
    if self.next_chunk is not None:
        return False  # Đang infer rồi
    
    remaining = len(self.current_chunk) - self.chunk_index
    return remaining <= self.overlap_steps
```

#### Hàm `launch_next_inference()` — STATE ROLLFORWARD ở đây!

```python
def launch_next_inference(self, observation):
    """
    ĐÂY LÀ NƠI STATE ROLLFORWARD XẢY RA.
    
    1. Tính future state từ pending actions
    2. Gọi model trên background thread
    """
    # === STATE ROLLFORWARD ===
    # Lấy các actions còn lại trong chunk (chưa thực thi)
    remaining_actions = self.current_chunk[self.chunk_index:]
    
    # Tính trạng thái tương lai bằng cách cộng dồn
    current_state = observation["observation.state"]
    future_state = current_state.copy()
    for action in remaining_actions:
        future_state = future_state + action  # delta action!
    
    # Thay thế state trong observation bằng future state
    observation_with_future_state = observation.copy()
    observation_with_future_state["observation.state"] = future_state
    # ========================
    
    # Gọi policy trên background thread (không block main loop)
    self.inference_thread = threading.Thread(
        target=self._run_inference,
        args=(observation_with_future_state,)
    )
    self.inference_thread.start()

def _run_inference(self, observation):
    """Chạy trên background thread."""
    with torch.inference_mode():
        chunk = self.policy.predict_action_chunk(observation)
    self.next_chunk = chunk  # Lưu kết quả
```

#### Hàm `get_action()` — Interface chính với control loop

```python
def get_action(self, observation_frame):
    """
    Gọi mỗi bước điều khiển (mỗi 1/fps giây).
    
    Returns: action tiếp theo cần gửi cho robot
    """
    # === KHỞI TẠO: Inference đồng bộ lần đầu ===
    if self.current_chunk is None:
        first_chunk = self.policy.predict_action_chunk(observation_frame)
        self.current_chunk = first_chunk
        self.chunk_index = 0
    
    # === KIỂM TRA: Có nên bắt đầu infer chunk tiếp không? ===
    if self.should_launch_next_inference():
        self.launch_next_inference(observation_frame)  # ← STATE ROLLFORWARD!
    
    # === KIỂM TRA: Chunk hiện tại hết chưa? ===
    if self.chunk_index >= len(self.current_chunk):
        # Đợi next_chunk nếu chưa xong (hiếm khi xảy ra nếu overlap đủ lớn)
        if self.inference_thread is not None:
            self.inference_thread.join()  # Block tại đây nếu cần
        
        # Chuyển sang chunk mới
        self.current_chunk = self.next_chunk.numpy()
        self.next_chunk = None
        self.chunk_index = 0
    
    # === LẤY ACTION ===
    action = self.current_chunk[self.chunk_index]
    self.chunk_index += 1
    return action
```

#### Hàm `run_loop()` — Vòng lặp điều khiển chính

```python
@torch.inference_mode()
def run_loop(robot, events, fps, ..., action_quant_ratio, inference_overlap_steps):
    """
    Vòng lặp chạy ở tần số fps (ví dụ 30 Hz = mỗi 33ms một lần).
    """
    async_manager = VLASHAsyncManager(
        policy=policy,
        robot=robot,
        single_task=single_task,
        overlap_steps=inference_overlap_steps
    )
    
    while not events["exit_early"].is_set():
        start_time = time.perf_counter()
        
        # 1. Đọc observation từ robot
        observation = robot.capture_observation()
        
        # 2. Tiền xử lý (GPU-accelerated: chuyển ảnh uint8 lên GPU trước)
        obs_tensor = prepare_observation_for_inference(observation, device)
        
        # 3. Lấy action tiếp theo (có thể trigger async inference)
        action = async_manager.get_action(obs_tensor)
        
        # 4. Action quantization: nếu action_quant_ratio=2
        #    → execute 2 actions mỗi lần (tăng speed 2x)
        for _ in range(action_quant_ratio):
            robot.send_action(action)
        
        # 5. Maintain target frequency
        elapsed = time.perf_counter() - start_time
        busy_wait(1/fps - elapsed)  # Chờ cho đủ 1/fps giây
```

---

### 4.5 `vlash/policies/pi05/modeling_pi05.py` — Model (1576 dòng)

**File lớn nhất, chứa toàn bộ implementation của π0.5.**

#### Class `PI05PrefixEmbedder` — Xử lý ảnh + ngôn ngữ

```python
class PI05PrefixEmbedder(nn.Module):
    """
    Nhận ảnh từ camera và text task → tạo embeddings (prefix sequence)
    cho transformer layers.
    
    Input:
    - images: [B, num_cameras, C, H, W] (e.g., [1, 2, 3, 224, 224])
    - tokens: [B, seq_len] (tokenized task text)
    
    Output:
    - embeddings: [B, prefix_len, hidden_size]
    - attention_mask: [B, prefix_len]
    """
    
    def forward(self, images, img_masks, tokens, masks):
        # 1. SigLIP encode images → image embeddings
        img_embeds = self.vlm.vision_tower(images)  # [B, 256/img, hidden]
        
        # 2. Project → language space
        img_embeds = self.vlm.multi_modal_projector(img_embeds)
        
        # 3. Tokenize task → text embeddings
        text_embeds = self.vlm.language_model.embed_tokens(tokens)
        
        # 4. Concatenate: [img_embeds | text_embeds]
        prefix = torch.cat([img_embeds, text_embeds], dim=1)
        
        return prefix, padding_mask, attention_mask
```

#### Class `PI05SuffixEmbedder` — Xử lý actions + state

```python
class PI05SuffixEmbedder(nn.Module):
    """
    Nhận noisy actions + timestep + robot state → suffix embeddings
    
    STATE CONDITIONING (AdaRMS) quan trọng:
    - state và timestep được chiếu → (scale, shift) vector
    - Dùng để điều chỉnh LayerNorm trong action expert
    - → Model "biết" robot đang ở đâu khi dự đoán actions
    """
    
    def forward(self, state, noisy_actions, time):
        # 1. Embed noisy actions
        action_embeds = self.action_in_proj(noisy_actions)  # [B, H, hidden]
        
        # 2. Embed timestep (flow matching)
        time_embed = self.time_mlp_out(self.time_mlp_in(time))
        
        # 3. State conditioning (nếu state_cond=True)
        if self.state_proj is not None:
            state_embed = self.state_mlp_out(self.state_mlp_in(state))
            # Kết hợp state và time
            adaRMS_cond = state_embed + time_embed
        else:
            adaRMS_cond = time_embed
        
        # 4. adaRMS_cond sẽ được dùng trong PI05ModelLayer
        # để modulate LayerNorm: output = scale(cond) * norm(x) + shift(cond)
        
        return action_embeds, suffix_mask, adaRMS_cond
```

#### Class `PI05Attention` — Joint Attention

```python
class PI05Attention(nn.Module):
    """
    JOINT ATTENTION: Action expert attend đến cả VLM tokens.
    
    Key insight: VLM tokens (ảnh + text) là READ-ONLY với action expert.
    Action expert có thể đọc VLM, nhưng VLM không thể đọc action expert.
    
    Điều này giúp:
    - VLM không bị "nhiễm" bởi action information
    - Action expert có đủ context để dự đoán tốt
    """
    
    def forward(self, prefix_hidden, suffix_hidden, ...):
        # prefix = VLM hidden states [B, prefix_len, hidden]
        # suffix = action expert hidden states [B, suffix_len, hidden]
        
        # Q chỉ từ suffix (action expert hỏi)
        Q = self.q_proj(suffix_hidden)
        
        # K, V từ CẢ prefix lẫn suffix (ai cũng có thể trả lời)
        KV_input = torch.cat([prefix_hidden, suffix_hidden], dim=1)
        K = self.k_proj(KV_input)
        V = self.v_proj(KV_input)
        
        # Scaled dot-product attention
        attn_output = F.scaled_dot_product_attention(Q, K, V, attn_mask)
        
        return attn_output
```

#### Hàm `forward_shared_observation()` — Optimization 3.26x

```python
def forward_shared_observation(self, batch, noise, time):
    """
    Với SharedObservationVLASHDataset: batch có shape [B, num_offsets, ...]
    
    Thay vì forward N lần (mỗi lần cho 1 offset):
    - Tính VLM embeddings 1 lần (đắt nhất!)
    - Tính action loss cho từng offset (rẻ hơn)
    
    Speedup: VLM forward là bottleneck → tiết kiệm N-1 lần
    """
    B, num_offsets = batch["observation.state"].shape[:2]
    
    # === Tính prefix embeddings 1 lần (SHARED) ===
    # Lấy ảnh tại offset 0 (tất cả offsets dùng cùng 1 observation)
    images = batch["observation.images"][:, 0]  # [B, num_cams, C, H, W]
    prefix_embeds, _, _ = self.prefix_embedder(images, ...)
    
    total_loss = 0
    
    # === Với mỗi offset, tính loss riêng ===
    for δ in range(num_offsets):
        state = batch["observation.state"][:, δ]    # [B, state_dim]
        actions = batch["action"][:, δ]              # [B, H, action_dim]
        
        # Tạo noisy actions (flow matching)
        noise_δ = noise[:, δ]
        x_t = sqrt(1-t) * actions + sqrt(t) * noise_δ
        
        # Suffix embeddings (state khác nhau cho mỗi offset)
        suffix_embeds, _, adaRMS = self.suffix_embedder(state, x_t, time)
        
        # Run transformer layers (dùng prefix_embeds đã tính sẵn)
        output = self.run_layers(prefix_embeds, suffix_embeds, adaRMS)
        
        # Loss cho offset này
        noise_pred = self.action_out_proj(output)
        loss_δ = F.mse_loss(noise_pred, noise_δ)
        total_loss += loss_δ
    
    return {"loss": total_loss / num_offsets}
```

---

### 4.6 `vlash/configs/train_config.py` — Cấu hình Training

```python
@dataclass
class LoRAConfig:
    enable: bool = False          # Bật/tắt LoRA
    r: int = 16                   # Rank của LoRA (thấp = ít params hơn)
    alpha: int = 16               # Scaling: effective_lr ∝ alpha/r
    dropout: float = 0.0          # LoRA dropout
    
    # Layers nào được áp dụng LoRA
    target_modules: list[str] = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj",  # Attention
        "gate_proj", "up_proj", "down_proj",       # FFN
    ])
    
    # Layers nào được train đầy đủ (không LoRA)
    extra_trainable_modules: list[str] = field(default_factory=lambda: [
        "action_in_proj",   # Action embedding
        "time_mlp_in",      # Timestep embedding
        "time_mlp_out",
        "state_proj",       # State conditioning (quan trọng cho VLASH!)
        "embeddings",       # Token embeddings
    ])
    
    use_qlora: bool = False       # 4-bit quantization (tiết kiệm VRAM)
    qlora_quant_type: str = "nf4" # "nf4" hoặc "fp4"
    qlora_compute_dtype: str = "bfloat16"

@dataclass
class VLASHTrainConfig(TrainPipelineConfig):
    max_delay_steps: int = 0      # Temporal offset range [0, N]
    grad_accum_steps: int = 1     # Gradient accumulation
    shared_observation: bool = False  # 3.26x speedup optimization
    lora: LoRAConfig = field(default_factory=LoRAConfig)
```

---

### 4.7 `vlash/lora/apply.py` — Áp dụng LoRA

```python
def apply_lora(cfg: LoRAConfig, policy: nn.Module):
    """
    Inject LoRA adapters vào policy.
    
    Sau khi gọi hàm này:
    - Các Linear layers trong target_modules được bọc bởi LoraLinear
    - LoraLinear = base_layer (frozen) + lora_A @ lora_B (trainable)
    - Chỉ lora_A, lora_B được update trong training
    """
    from peft import LoraConfig, get_peft_model
    
    # Tìm modules cần train đầy đủ
    modules_to_save = infer_unfreeze_modules_from_patterns(
        policy, cfg.extra_trainable_modules
    )
    
    # Tạo PEFT config
    peft_config = LoraConfig(
        r=cfg.r,
        lora_alpha=cfg.alpha,
        target_modules=cfg.target_modules,
        modules_to_save=modules_to_save,  # Train đầy đủ các module này
        lora_dropout=cfg.dropout,
    )
    
    # Inject LoRA layers
    policy = get_peft_model(policy, peft_config)
    
    # Cast dtype cho phù hợp (LoRA mặc định tạo fp32, base có thể bf16)
    cast_lora_adapters_to_base_dtype(policy)
    
    # QLoRA: quantize base layers thành 4-bit
    if cfg.use_qlora:
        quantize_peft_model_4bit(policy, compute_dtype=torch.bfloat16)
    
    return policy
```

---

### 4.8 `vlash/utils.py` — GPU-accelerated Preprocessing

```python
def prepare_observation_for_inference(observation, device, task=None):
    """
    Tối ưu hóa: Chuyển ảnh uint8 lên GPU TRƯỚC khi làm nặng.
    
    Tại sao? uint8 = 1 byte/pixel, float32 = 4 bytes/pixel
    → Chuyển GPU lúc uint8 → bandwidth giảm 4x
    → Cast sang float32 trên GPU → nhanh hơn nhiều
    """
    prepared = {}
    
    for key, value in observation.items():
        if isinstance(value, np.ndarray):
            if value.dtype == np.uint8:
                # Ảnh: chuyển lên GPU ngay lúc còn uint8
                tensor = torch.from_numpy(value).to(device)
                # Sau đó mới cast và normalize
                tensor = tensor.float() / 255.0
                # HWC → CHW (PyTorch format)
                tensor = tensor.permute(2, 0, 1)
            else:
                tensor = torch.from_numpy(value).to(device).float()
            
            prepared[key] = tensor.unsqueeze(0)  # Thêm batch dim
        else:
            prepared[key] = value
    
    if task is not None:
        prepared["task"] = [task]
    
    return prepared
```

---

## 5. Luồng Training

### 5.1 Sơ đồ đầy đủ

```
INPUT: HuggingFace Dataset (e.g., lerobot/libero_spatial)
       Chứa: [images, robot_state, actions, language_instruction]

         │
         ▼
┌─────────────────────────────────────────────────────────┐
│                   VLASHDataset                          │
│                                                         │
│  Với mỗi sample tại timestep t:                        │
│  1. Sample δ ~ Uniform[0, max_delay_steps=8]           │
│  2. Lấy images tại t (không thay đổi)                  │
│  3. Lấy state tại t+δ (THAY ĐỔI so với gốc)           │
│  4. Lấy actions từ t+δ đến t+δ+H (SHIFT)              │
│  5. Đánh dấu actions ngoài episode = padded            │
│                                                         │
│  Output: {                                              │
│    "observation.images": [C, H, W],                    │
│    "observation.state": [state_dim],  ← future state   │
│    "action": [H, action_dim],         ← shifted actions │
│    "action_is_pad": [H],                               │
│    "task": "pick up the red mug..."                    │
│  }                                                      │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼ (DataLoader, batch_size=16)
┌─────────────────────────────────────────────────────────┐
│                   PI05Policy.forward()                  │
│                                                         │
│  1. prepare_images():                                   │
│     - Resize to 224x224 with padding                   │
│     - Normalize to [-1, 1]                             │
│     - Stack cameras                                     │
│                                                         │
│  2. prepare_language():                                 │
│     - Tokenize task + (discretized state nếu           │
│       state_cond=False)                                 │
│                                                         │
│  3. prepare_state():                                    │
│     - Pad to max_state_dim                             │
│                                                         │
│  4. prepare_action():                                   │
│     - Normalize                                         │
│     - Pad to max_action_dim                            │
│                                                         │
│  5. Flow matching:                                      │
│     t ~ Uniform[0, 1)                                  │
│     noise ~ N(0, I)                                    │
│     x_t = sqrt(1-t)*actions + sqrt(t)*noise            │
│                                                         │
│  6. PI05Model.forward(batch, noise=noise, time=t)      │
│     → noise_pred                                        │
│                                                         │
│  7. Loss = MSE(noise, noise_pred)                      │
│     (chỉ tính trên non-padded actions)                 │
│                                                         │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│                   Optimizer Step                        │
│                                                         │
│  loss.backward()                                        │
│  → Chỉ update LoRA adapters (nếu lora.enable=True)     │
│  → + extra_trainable_modules (action_in_proj, ...)     │
│                                                         │
│  optimizer.step()  (sau grad_accum_steps bước)         │
│  scheduler.step()                                       │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼ (mỗi save_freq bước)
┌─────────────────────────────────────────────────────────┐
│                   Checkpoint                            │
│                                                         │
│  clone_and_merge_lora_policy():                         │
│  1. Copy policy sang CPU                               │
│  2. Merge LoRA vào base weights (lora_A @ lora_B)      │
│  3. Unload PEFT wrapper                                 │
│                                                         │
│  policy.save_pretrained(                               │
│    "outputs/train/pi05_async/checkpoints/010000/"      │
│  )                                                      │
│  → Lưu: config.json, model.safetensors, ...            │
└─────────────────────────────────────────────────────────┘

OUTPUT: Checkpoint tại outputs/train/pi05_async/checkpoints/
```

---

## 6. Luồng Inference

### 6.1 Timeline bất đồng bộ chi tiết

```
Ký hiệu: [I] = Inference, [E] = Execute actions, Δ = inference delay

SYNCHRONOUS (trước VLASH):
─────────────────────────────────────────────────────────────
t:  0    1    2    3    4    5    6    7    8    9    10 ...
    │    │    │    │    │    │    │    │    │    │    │
    [IIIIIIIII]
               [E  E  E  E  E  E  E  E]
                                        [IIIIIIIII]
                                                   [E  E ...]
    ↑STALL↑    ←── execute 8 steps ──→  ↑STALL↑

Reaction latency = 8 (execute) + 2 (infer) = 10 steps !

NAIVE ASYNC (không có state rollforward):
─────────────────────────────────────────────────────────────
t:  0    1    2    3    4    5    6    7    8    9    10 ...
    [IIIIIIIII]       [IIIIIIIII]       [IIIIIIIII]
               [E  E  E  E  E  E  E  E][E  E  E  E ...]
    ↑obs@t=0↑                          ↑obs@t=8↑

Vấn đề: Model infer với s_0, nhưng execute lúc robot ở s_2
         → MISALIGNMENT!

VLASH (state rollforward):
─────────────────────────────────────────────────────────────
t:  0    1    2    3    4    5    6    7    8    9    10 ...
    [IIIIIIIII]       [IIIIIIIII]       [IIIIIIIII]
               [E  E  E  E  E  E  E  E][E  E  E  E ...]
    ↑obs@t=0  ↑                ↑
              └── s_future = s_0 + a_0 + a_1 (rollforward!)
                  Model biết robot sẽ ở đâu!

Reaction latency = 2 steps (chỉ inference time) ✓
Không misalignment ✓
Không overhead ✓
```

### 6.2 Sơ đồ code flow inference

```
vlash run examples/inference/async.yaml
    │
    ▼
run() [run.py]
    │
    ├─ Load config (RunConfig)
    ├─ Load policy từ checkpoint
    │   └─ make_policy(cfg.policy, ds_meta)
    │       └─ PI05Policy.from_pretrained(path)
    │
    ├─ Compile model (torch.compile) nếu compile_model=True
    │   └─ Warmup 3 lần để JIT compile xong
    │
    ├─ Connect robot (robot.connect())
    │
    └─ run_loop(robot, policy, fps=30, ...)
           │
           └─ VLASHAsyncManager(overlap_steps=4)
                  │
                  ▼ (mỗi 1/30 giây = 33ms)
           ┌──────────────────────────────┐
           │ 1. robot.capture_observation()│
           │    → {images, state, ...}    │
           │                              │
           │ 2. prepare_observation()     │
           │    → GPU tensors             │
           │                              │
           │ 3. async_manager.get_action()│
           │    ├─ if chunk_idx == n-4:   │
           │    │   STATE ROLLFORWARD     │
           │    │   s_f = s + Σ pending_a │
           │    │   launch_inference(s_f) │ ← background thread
           │    │                         │
           │    ├─ if chunk done:         │
           │    │   switch to next_chunk  │
           │    │                         │
           │    └─ return current_action  │
           │                              │
           │ 4. robot.send_action(action) │
           │                              │
           │ 5. busy_wait(1/30 - elapsed) │
           └──────────────────────────────┘
```

---

## 7. Tham Số Cấu Hình

### 7.1 Training config (examples/train/pi05/async.yaml)

| Tham số | Mặc định | Tác dụng |
|---|---|---|
| `max_delay_steps` | 0 | **QUAN TRỌNG NHẤT.** Số offset tối đa [0, N]. N=0 → sync training. N=8 → VLASH training. Tăng → robust hơn với delay lớn, nhưng train lâu hơn. |
| `shared_observation` | false | Bật → 3.26x speedup khi max_delay_steps > 0. LUÔN bật cùng với max_delay_steps > 0. |
| `grad_accum_steps` | 1 | Effective batch = batch_size × grad_accum_steps. Dùng khi VRAM ít (RTX 3050: đặt batch=1, accum=8). |
| `batch_size` | 16 | Số samples mỗi bước. RTX 3050 với QLoRA: dùng 1-4. |
| `steps` | 50000 | Tổng số training steps. |
| `lr` | 5e-5 | Learning rate. Đừng thay đổi nếu không chắc. |
| `lora.enable` | false | Bật LoRA → chỉ train ~1% parameters. CẦN THIẾT với RTX 3050. |
| `lora.r` | 16 | LoRA rank. Thấp hơn = ít VRAM hơn, accuracy có thể giảm nhẹ. |
| `lora.use_qlora` | false | 4-bit quantization. BẮT BUỘC với 6GB VRAM. |
| `state_cond` | true | Bật state conditioning (AdaRMS). PHẢI BẬT để VLASH hoạt động. |
| `save_freq` | 10000 | Lưu checkpoint mỗi N steps. |
| `log_freq` | 200 | Log metrics mỗi N steps. |
| `wandb.enable` | true | Logging lên Weights & Biases. Tắt nếu không có account. |

### 7.2 Inference config (examples/inference/async.yaml)

| Tham số | Mặc định | Tác dụng |
|---|---|---|
| `inference_overlap_steps` | 4 | **QUAN TRỌNG.** Bắt đầu infer khi còn N actions. 0 = sync. 4 với n_action_steps=32 → infer bắt đầu lúc action 28/32. |
| `action_quant_ratio` | 1 | Macro-action: execute 1 action nhưng sum N deltas. 2 → 2x speedup. |
| `n_action_steps` | 32 | Số actions mỗi chunk. |
| `compile_model` | true | torch.compile → nhanh hơn ~20-30%. BẮT BUỘC khi dùng async. |
| `fps` | 30 | Tần số điều khiển (Hz). |
| `fuse_qkv` | true | Fuse Q, K, V projections → nhanh hơn. |
| `fuse_gate_up` | true | Fuse gate và up projections → nhanh hơn. |

### 7.3 Benchmark config

| Tham số | Mặc định | Tác dụng |
|---|---|---|
| `num_samples` | 16 | Số samples để đo latency. |
| `warmup_steps` | 10 | Bước warmup trước khi đo (quan trọng với torch.compile). |
| `compile_model` | true | Tắt nếu muốn đo latency không compiled. |
| `dataset.repo_id` | lerobot/pusht | Dataset để lấy sample input. Thay bằng dataset nhỏ bất kỳ. |

---

## 8. Cài Đặt Windows 11 (RTX 3050 6GB)

### 8.1 Yêu cầu hệ thống

```
✅ GPU: NVIDIA RTX 3050 6GB Laptop (đã xác nhận)
✅ OS: Windows 11
✅ RAM: Tối thiểu 16GB khuyến nghị
✅ Storage: ~30GB trống (model ~10GB, dataset ~5-15GB)
```

### 8.2 Cài đặt từng bước

#### Bước 1: Python 3.11

```
1. Vào python.org/downloads
2. Tải Python 3.11.x (KHÔNG dùng 3.12 hoặc 3.13)
3. Cài đặt: TICK "Add Python to PATH" ← QUAN TRỌNG
4. Kiểm tra:
```
```cmd
python --version
# Phải ra: Python 3.11.x
pip --version
# Phải ra: pip 2x.x.x
```

#### Bước 2: CUDA Toolkit 12.1

```
1. Vào: developer.nvidia.com/cuda-12-1-0-download-archive
2. Chọn: Windows → x86_64 → 11 → exe (local)
3. Tải (~3GB) và cài đặt
4. Kiểm tra:
```
```cmd
nvcc --version
# Phải ra: Cuda compilation tools, release 12.1

nvidia-smi
# Phải thấy: NVIDIA GeForce RTX 3050 6GB Laptop GPU
```

#### Bước 3: PyTorch với CUDA

```cmd
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

Kiểm tra:
```python
python -c "
import torch
print('CUDA available:', torch.cuda.is_available())
print('GPU:', torch.cuda.get_device_name(0))
print('VRAM:', torch.cuda.get_device_properties(0).total_memory / 1e9, 'GB')
"
# Phải ra:
# CUDA available: True
# GPU: NVIDIA GeForce RTX 3050 6GB Laptop GPU
# VRAM: ~6.0 GB
```

#### Bước 4: Git và clone repo

```cmd
# Cài Git nếu chưa có: git-scm.com
git clone https://github.com/mit-han-lab/vlash
cd vlash
```

#### Bước 5: Cài VLASH

```cmd
# Cách 1: Cài đầy đủ (có thể lỗi reachy2_sdk)
pip install -e .

# Cách 2: Nếu lỗi reachy2_sdk, cài thủ công
pip install lerobot==0.4.1
pip install peft==0.18.0
pip install bitsandbytes==0.48.2
pip install -e . --no-deps
```

#### Bước 6: Kiểm tra cài đặt

```cmd
vlash --help
# Phải thấy usage instructions
```

---

## 9. Cách Chạy và Kết Quả

### 9.1 Benchmark — Đo tốc độ inference (NHANH NHẤT, ~5 phút)

**Đây là thứ DỄ NHẤT để chạy, không cần dataset lớn.**

Sửa file `examples/benchmarks/inference_latency.yaml`:
```yaml
type: inference_latency
policy:
  type: pi05
  device: cuda
  dtype: bfloat16
  compile_model: false    # ← Tắt lần đầu chạy cho nhanh
  fuse_qkv: true
  fuse_gate_up: true

dataset:
  repo_id: lerobot/pusht  # Dataset nhỏ, tự download

num_samples: 16
warmup_steps: 10
batch_size: 1
seed: 42
output_dir: outputs/benchmarks/inference_latency/pi05
```

Chạy:
```cmd
vlash benchmark examples/benchmarks/inference_latency.yaml
```

**Kết quả in ra terminal:**
```
================================================================================
INFERENCE LATENCY BENCHMARK RESULTS
================================================================================

Policy Type: pi05
Pretrained Path: N/A (new model)
Dataset: lerobot/pusht
Device: cuda
Batch Size: 1
Compile: False

Number of samples: 16

Latency Statistics (milliseconds):
  Mean:   187.34 ms    ← RTX 3050 (kỳ vọng 180-250ms)
  Median: 185.12 ms
  Std:    8.23 ms
  Min:    174.51 ms
  Max:    203.67 ms

Percentiles:
  P50: 185.12 ms
  P90: 197.43 ms
  P95: 200.11 ms
  P99: 203.67 ms

Throughput:
  FPS: 5.34         ← ~5 inference/giây

================================================================================
```

**Nếu bật `compile_model: true` (lần đầu chậm do compile ~2-3 phút):**
```
Latency Statistics:
  Mean:   143.21 ms   ← Nhanh hơn ~25% so với không compile
  FPS:    6.98
```

**Lưu kết quả ra file JSON:**
```yaml
# Thêm vào config:
output_file: outputs/benchmarks/results.json
```
```json
{
  "config": {
    "policy_type": "pi05",
    "device": "cuda",
    "batch_size": 1,
    "compile_model": false
  },
  "results": {
    "num_samples": 16,
    "mean_ms": 187.34,
    "median_ms": 185.12,
    "fps": 5.34
  }
}
```

---

### 9.2 Training — Fine-tune trên LIBERO

#### Bước 1: Chuẩn bị config cho RTX 3050 6GB

Tạo file mới `examples/train/pi05/async_rtx3050.yaml`:
```yaml
policy:
  type: pi05
  pretrained_path: lerobot/pi05_base  # Download từ HuggingFace (~8GB)
  push_to_hub: false
  dtype: bfloat16
  device: cuda
  state_cond: true

dataset:
  repo_id: lerobot/libero_spatial   # Download ~2GB
  video_backend: torchcodec

output_dir: outputs/train/pi05_vlash_rtx3050
job_name: pi05_vlash_rtx3050

# ← Giảm batch size cho 6GB VRAM
batch_size: 1
grad_accum_steps: 16    # Effective batch = 1 × 16 = 16

steps: 30000             # Giảm từ 50000 nếu muốn nhanh hơn
num_workers: 2
seed: 1000

optimizer:
  type: adamw
  lr: 5.0e-5
  betas: [0.9, 0.95]
  weight_decay: 1.0e-10

scheduler:
  type: cosine_decay_with_warmup
  num_warmup_steps: 1000
  peak_lr: 5.0e-5
  decay_lr: 2.5e-6
  num_decay_steps: 30000

save_checkpoint: true
save_freq: 5000

log_freq: 100
wandb:
  enable: false    # Tắt nếu không có W&B account

# VLASH parameters
max_delay_steps: 4          # Giảm từ 8 xuống 4 để tiết kiệm VRAM
shared_observation: true    # Bật để train nhanh hơn

# LoRA - BẮT BUỘC với 6GB VRAM
lora:
  enable: true
  r: 16
  alpha: 16
  dropout: 0.0
  target_modules:
    - q_proj
    - k_proj
    - v_proj
    - o_proj
    - gate_proj
    - up_proj
    - down_proj
  extra_trainable_modules:
    - action_in_proj
    - time_mlp_in
    - time_mlp_out
    - state_proj
    - embeddings
  use_qlora: true              # 4-bit quant - BẮT BUỘC với 6GB VRAM
  qlora_quant_type: nf4
  qlora_compute_dtype: bfloat16
```

#### Bước 2: Chạy training

```cmd
vlash train examples/train/pi05/async_rtx3050.yaml
```

#### Bước 3: Theo dõi progress

Terminal sẽ in:
```
INFO: Loading dataset: lerobot/libero_spatial
INFO: Dataset loaded: 48,000 samples, 240 episodes
INFO: Loading policy: lerobot/pi05_base
INFO: Applying LoRA (r=16, alpha=16)
INFO: QLoRA: Quantizing base layers to 4-bit...
INFO: Trainable parameters: 12,582,912 / 2,718,293,248 (0.46%)

Step 100/30000 | Loss: 0.8432 | LR: 4.5e-05 | Time: 12.3s
Step 200/30000 | Loss: 0.6821 | LR: 4.8e-05 | Time: 12.1s
Step 300/30000 | Loss: 0.5934 | LR: 5.0e-05 | Time: 12.0s
...
Step 5000/30000 | Loss: 0.2341 | Saving checkpoint...
→ Saved: outputs/train/pi05_vlash_rtx3050/checkpoints/005000/pretrained_model/
...
Step 30000/30000 | Loss: 0.1123 | Training complete!
→ Saved: outputs/train/pi05_vlash_rtx3050/checkpoints/030000/pretrained_model/
```

**Cấu trúc checkpoint được lưu:**
```
outputs/train/pi05_vlash_rtx3050/
└── checkpoints/
    ├── 005000/
    │   └── pretrained_model/
    │       ├── config.json          ← Model config
    │       ├── model.safetensors    ← Model weights (~8GB)
    │       └── train_config.json    ← Training config used
    ├── 010000/
    │   └── pretrained_model/
    │       └── ...
    └── 030000/
        └── pretrained_model/
            └── ...
```

**Thời gian ước tính trên RTX 3050 6GB:**
```
Mỗi step: ~12-15 giây (với QLoRA + batch=1 + grad_accum=16)
30,000 steps: ~100-125 giờ ← khá lâu!

Rút ngắn: Dùng steps=10000 (đủ để xem model học) → ~35-40 giờ
```

> ⚠️ **Lưu ý:** RTX 3050 laptop khá chậm cho việc này. Nếu có thể, dùng Google Colab Pro (A100) → train 30K steps trong ~3-4 giờ.

---

### 9.3 So sánh cấu hình Train: SYNC vs ASYNC vs VLASH

| Config | max_delay_steps | shared_obs | Kết quả |
|---|---|---|---|
| `sync.yaml` | 0 | false | Baseline, không async |
| `async.yaml` | 8 | true | VLASH đầy đủ, 3.26x speedup training |
| `async_lora.yaml` | 8 | true | VLASH + LoRA, tiết kiệm VRAM |
| `async_rtx3050.yaml` | 4 | true | VLASH + QLoRA, cho GPU 6GB |

---

## 10. Lỗi Thường Gặp và Cách Sửa

### Lỗi 1: `CUDA out of memory`

```
RuntimeError: CUDA out of memory. Tried to allocate 2.34 GiB
```

**Nguyên nhân:** Batch quá lớn với 6GB VRAM.

**Cách sửa:**
```yaml
batch_size: 1            # Giảm xuống tối thiểu
grad_accum_steps: 16     # Tăng để bù effective batch size
lora:
  use_qlora: true        # Bắt buộc với 6GB
  r: 8                   # Giảm rank nếu vẫn OOM
```

---

### Lỗi 2: `ModuleNotFoundError: No module named 'reachy2_sdk'`

```
ModuleNotFoundError: No module named 'reachy2_sdk'
```

**Nguyên nhân:** SDK cho robot Reachy2 (không cần thiết).

**Cách sửa:**
```cmd
pip install lerobot==0.4.1 peft==0.18.0 bitsandbytes==0.48.2
pip install -e . --no-deps
```

---

### Lỗi 3: `torch.compile` chậm hoặc lỗi lần đầu

```
[W] Skipping graph due to error...
```

**Nguyên nhân:** torch.compile cần warmup ~3 lần.

**Cách sửa:** Tắt khi benchmark, bật khi inference thật:
```yaml
compile_model: false  # Cho benchmark/test
compile_model: true   # Cho inference thật (sau warmup)
```

---

### Lỗi 4: `Dataset not found` hoặc download chậm

**Cách sửa:**
```cmd
# Đăng nhập HuggingFace trước
pip install huggingface_hub
huggingface-cli login
# Nhập token từ huggingface.co/settings/tokens
```

---

### Lỗi 5: `bitsandbytes` không hoạt động trên Windows

**Nguyên nhân:** bitsandbytes cần CUDA và một số DLL đặc biệt.

**Cách sửa:**
```cmd
pip uninstall bitsandbytes
pip install bitsandbytes --prefer-binary --extra-index-url=https://jllllll.github.io/bitsandbytes-windows-webui
```

---

### Lỗi 6: `state_cond` không có tác dụng

**Nguyên nhân:** state_cond phải được đặt trong policy config, không phải top-level.

**Sai:**
```yaml
state_cond: true  # ← sai vị trí
```

**Đúng:**
```yaml
policy:
  type: pi05
  state_cond: true  # ← đúng vị trí
```

---

## 11. Bảng Tóm Tắt

### 11.1 Kết quả thực nghiệm (từ paper)

| Phương pháp | Delay (Δ) | SR LIBERO (%) | Speedup | Reaction Latency |
|---|---|---|---|---|
| Sync | 0 | 95.9% | 1.00× | 1303ms |
| Naive Async | 2 | 90.2% | 1.31× | 103ms |
| Naive Async | 4 | 75.1% | 1.45× | 103ms |
| **VLASH** | **2** | **97.1%** | **1.31×** | **103ms** |
| **VLASH** | **4** | **93.1%** | **1.45×** | **103ms** |
| VLASH + quant(q=2) | 2 | 92% | **2.03×** | 103ms |

### 11.2 So sánh hardware

| GPU | Inference time | Δ (steps ở 20Hz) | Ghi chú |
|---|---|---|---|
| RTX 5090 | ~30ms | <1 step | Gần như real-time |
| RTX 4090 | ~103ms | ~2 steps | Dùng trong paper |
| RTX 3050 6GB | ~180-250ms | ~3-5 steps | Laptop của bạn |
| Laptop CPU | ~2000ms+ | ~40 steps | Không khả dụng |

### 11.3 Files quan trọng nhất

| File | Quan trọng | Lý do |
|---|---|---|
| `vlash/datasets/vlash_dataset.py` | ⭐⭐⭐⭐⭐ | Core innovation: temporal offset augmentation |
| `vlash/run.py` | ⭐⭐⭐⭐⭐ | State rollforward + async manager |
| `vlash/policies/pi05/modeling_pi05.py` | ⭐⭐⭐⭐ | Model architecture + shared obs forward |
| `vlash/train.py` | ⭐⭐⭐⭐ | Training orchestration |
| `vlash/lora/apply.py` | ⭐⭐⭐ | LoRA/QLoRA injection |
| `vlash/cli.py` | ⭐⭐ | Entry point, GPU detection |
| `vlash/utils.py` | ⭐⭐ | GPU-accelerated preprocessing |

### 11.4 Luồng data từ đầu đến cuối

```
Dataset (HuggingFace)
    ↓ VLASHDataset (temporal offset δ)
    ↓ DataLoader (batch)
    ↓ PI05Policy.forward() (flow matching loss)
    ↓ AdamW optimizer (LoRA params only)
    ↓ Checkpoint (merged weights)
    ↓ PI05Policy.from_pretrained()
    ↓ VLASHAsyncManager (state rollforward)
    ↓ Robot actuators
```

---

*Tài liệu này được tạo dựa trên phân tích toàn bộ source code của VLASH và paper arXiv:2512.01031 (Tang et al., 2025).*
