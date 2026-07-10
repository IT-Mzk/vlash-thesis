# VLASH — Project Brief for Claude

## PROJECT STATUS (updated 2026-07-06 — read this first)

This folder contains BOTH the VLASH codebase AND the user's bachelor-thesis
deliverables built on it. Work done so far (on macOS; everything is in files,
so any Claude instance on any machine can continue):

**Deliverables (done):**
- `Thesis_VLASH_MacDuyKhanh.docx` / `.pdf` — **32-page thesis, complete**.
  Original cover page preserved (source: `cover_source.docx`). UITM format:
  A4, TNR 12pt, 2cm margins, page-numbered TOC, List of Symbols, 11 figures,
  8 tables, IEEE refs [n], prose de-AI-ified (no em-dashes).
- `Defense_Slides_VLASH.pptx` — 10-slide English defense deck (navy theme,
  fade animations, speaker notes). Built by `make_defense_slides.js`.
- `Defense_Speech_7min.docx` — verbatim 7-minute English speech script with
  Vietnamese coaching notes. Built by `make_speech_doc.js`.
- `simulation/vlash_simulation.py` — the thesis's own-work testbed
  (Sync / Naive-Async / VLASH). Includes delay sweep, robustness sweep,
  and two assumption stress-tests (actuation noise §3.3.6, delay
  misestimation §3.3.7). Fully seeded (SEED0=20260615): re-running
  reproduces every thesis number exactly (Tab. 4–7).

**Thesis build pipeline (2-pass, needed only when editing content):**
1. edit prose/figures inside `build_thesis_v2.py` → 2. run it →
3. convert docx→PDF (LibreOffice `soffice` or MS Word) →
4. `python detect_pages.py` (writes `pagemap.json` for TOC page numbers) →
5. run `build_thesis_v2.py` again → convert final PDF.
All scripts now use **file-relative paths** (portable to any machine).
Cowork sandbox note: overwriting an existing PDF on the mount may fail;
convert to /tmp then `cat /tmp/x.pdf > target.pdf`.

**Pending (user must do):** ask supervisor the 6 questions in
`THESIS_supervisor_questions.md` (Q1 sim-sufficiency, Q4 faculty name on
cover, Q5 GenAI declaration, Q2 paper-table vs similarity); run the
university similarity check. Optional next step (only if supervisor requires,
Q1): real QLoRA fine-tune of π0.5 on the user's RTX 3050 6GB — plan is in
thesis §4.1 and `WINDOWS_SETUP_ROADMAP.md` (phase 5).

**Git:** `origin` currently points to the upstream `mit-han-lab/vlash` repo
(no push rights). Follow `WINDOWS_SETUP_ROADMAP.md` phase 2 to move work to
the user's own GitHub repo. Thesis files are not yet committed.

## What This Project Is

VLASH (arXiv:2512.01031, Tang et al. 2025) fine-tunes VLA (Vision-Language-Action) models for **real-time asynchronous robot control**. Built on top of HuggingFace LeRobot. The base model is **π0.5** (PaliGemma-2B vision-language backbone + Gemma-300M action expert, flow matching).

## Core Research Idea

**Problem:** VLA inference takes 103ms (RTX 4090). In async deployment, model predicts actions conditioned on state `s_t`, but actions execute at `s_{t+Δ}` → misalignment → robot jitters.

**VLASH solution — State Rollforward:**
```
s_{t+Δ} = s_t + a_t + a_{t+1} + ... + a_{t+Δ-1}
```
Pending actions are already known → compute future state analytically (zero overhead). Condition policy on `s_{t+Δ}` instead of `s_t`. Works because actions are **delta joint positions** (additive).

**Three innovations:**
1. **State Rollforward** (inference): substitute `s_{t+Δ}` before calling policy — only a vector sum
2. **Temporal-Offset Augmentation** (training): random `δ ∈ [0, max_delay_steps]` shifts training pairs `(obs_t, state_{t+δ}) → actions_{t+δ:}`
3. **Shared Observation Optimization** (training efficiency): pack N offsets with same observation into one forward pass → 3.26× speedup

## Critical Files

| File | Purpose |
|---|---|
| `vlash/datasets/vlash_dataset.py` | **Core innovation.** `VLASHDataset._get_query_indices()` does temporal offset sampling. `SharedObservationVLASHDataset` packs N offsets per forward pass. |
| `vlash/run.py` | **State rollforward lives here.** `VLASHAsyncManager.launch_next_inference()` sums pending actions to compute `s_future` before calling policy. `get_action()` is the main interface. |
| `vlash/policies/pi05/modeling_pi05.py` | π0.5 model (1576 lines). `PI05SuffixEmbedder` handles AdaRMS state conditioning. `forward_shared_observation()` is the 3.26× speedup path. |
| `vlash/train.py` | Training orchestration. `update_policy()` handles grad accumulation + shared obs. `auto_resume()` checks for existing checkpoints. |
| `vlash/configs/train_config.py` | `VLASHTrainConfig` (max_delay_steps, shared_observation, lora) + `LoRAConfig` (r, alpha, use_qlora). |
| `vlash/lora/apply.py` | `apply_lora()` injects PEFT adapters. `extra_trainable_modules` (action_in_proj, state_proj, time_mlp_*) are trained fully — critical for VLASH to work. |
| `vlash/lora/checkpoint.py` | `clone_and_merge_lora_policy()` merges LoRA into base before saving. Handles QLoRA dequantization. |
| `vlash/lora/qlora.py` | 4-bit quantization via bitsandbytes. Replaces `nn.Linear` → `bnb.nn.Linear4bit` in base layers only (not LoRA adapters). |
| `vlash/utils.py` | `prepare_observation_for_inference()`: transfers uint8 images to GPU before casting to float — bandwidth optimization. |
| `vlash/cli.py` | Entry point. Auto-detects GPU count, uses `accelerate launch` for multi-GPU. |

## Architecture: π0.5

```
Input: 2 RGB cameras (224×224) + task text + robot state (8-dim)

PI05PrefixEmbedder:
  SigLIP → 256 tokens/image → project → concat with text tokens
  Output: ~700 token prefix sequence

PI05SuffixEmbedder:
  noisy_actions + timestep t + state → suffix embeddings
  AdaRMS: state+time → (scale, shift) for LayerNorm in action expert

PI05Attention (Joint):
  Q from action expert suffix only
  K, V from concat(prefix, suffix) — action expert reads VLM context

Flow matching loss:
  x_t = sqrt(1-t)*actions + sqrt(t)*noise
  loss = MSE(noise, model(obs, state, x_t, t))

Inference: integrate dx/dt = v_θ(x,t) for 10 steps → clean actions
```

## Key Parameters

**Training:**
- `max_delay_steps=8` — temporal offset range. 0=sync baseline, 8=full VLASH
- `shared_observation=true` — always pair with max_delay_steps>0, gives 3.26× speedup
- `state_cond=true` — MUST be true for VLASH; enables AdaRMS in PI05SuffixEmbedder
- `lora.use_qlora=true` — required for 6GB VRAM (RTX 3050)
- `lora.extra_trainable_modules` — includes `state_proj`, `action_in_proj`, `time_mlp_*` — these are NOT LoRA, trained fully, critical for VLASH's state conditioning

**Inference:**
- `inference_overlap_steps=4` — start next inference when 4 actions remain in chunk
- `action_quant_ratio=2` — macro-actions: sum 2 deltas → 2× speedup, minimal accuracy loss
- `compile_model=true` — required for async (enables CPU/GPU overlap in background thread)

## Data Flow

**Training:**
```
LeRobot dataset → VLASHDataset (random δ, shift state+actions) →
DataLoader → PI05Policy.forward() / forward_shared_observation() →
flow matching loss → AdamW (LoRA params only) → checkpoint
```

**Inference:**
```
robot.capture_observation() → prepare_observation_for_inference() →
VLASHAsyncManager.get_action():
  └─ at overlap point: sum pending_actions → s_future →
     launch policy(obs_t, s_future) on background thread →
     switch chunk when ready (zero stall)
→ robot.send_action()
```

## Commands

```bash
# Training
vlash train examples/train/pi05/async.yaml

# Inference (real robot)
vlash run examples/inference/async.yaml

# Benchmark inference latency (no robot needed)
vlash benchmark examples/benchmarks/inference_latency.yaml

# Multi-GPU
CUDA_VISIBLE_DEVICES=0,1,2,3 vlash train examples/train/pi05/async.yaml
```

## Config for RTX 3050 6GB (user's hardware)

```yaml
batch_size: 1
grad_accum_steps: 16      # effective batch = 16
max_delay_steps: 4        # reduced from 8
lora:
  enable: true
  r: 16
  use_qlora: true          # mandatory for 6GB
policy:
  state_cond: true
shared_observation: true
wandb:
  enable: false
```

## Results (from paper, RTX 4090)

| Method | Delay Δ | LIBERO SR | Speedup | Reaction Latency |
|---|---|---|---|---|
| Sync | 0 | 95.9% | 1.00× | 1303ms |
| Naive Async | 4 | 75.1% | 1.45× | 103ms |
| **VLASH** | **4** | **93.1%** | **1.45×** | **103ms** |
| VLASH+quant(q=2) | 2 | 92% | 2.03× | 103ms |
| VLASH Kinetix | 4 | 81.7% | — | — |

RTX 3050 expected: ~180-250ms inference → Δ ≈ 3-5 steps at 20Hz.

## Dependencies

```
lerobot==0.4.1          # HuggingFace robot learning framework (base)
transformers @ git      # Pinned commit: dcddb970176382c0fcf4521b0c0e6fc15894dfe0
peft==0.18.0            # LoRA via PEFT
bitsandbytes==0.48.2    # QLoRA 4-bit quantization
```

## Important Conventions

- Actions are **delta joint positions** (8-dim: 7 joints + gripper). This is what makes rollforward exact.
- Dataset format: LeRobot standard (`observation.images`, `observation.state`, `action`, `language_instruction`)
- Checkpoints saved as merged weights (LoRA fused in). Raw LoRA adapters saved separately in `lora_adapters/` subfolder for resume.
- `state_cond=False` means state is discretized and appended to language tokens instead — different path, worse for VLASH.
- `shared_observation_collate_fn` must be used as DataLoader collate_fn when using `SharedObservationVLASHDataset`.
- Background inference thread writes to `self.next_chunk`; main loop reads it. No explicit lock needed because Python GIL + numpy assignment is atomic for this use case.

## Thesis Context

This codebase is the basis for a bachelor thesis (UITM Rzeszow, Poland) titled "Real-Time Vision-Language-Action (VLA) Inference for Reactive Robotics." Thesis chapters map to paper sections: Ch1=Background (paper §1-3), Ch2=System Design (paper §4 + codebase), Ch3=Experiments (paper §5), Ch4=Conclusion (paper §6).
