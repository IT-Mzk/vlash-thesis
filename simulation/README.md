# VLASH Simulation — reactive reaching under inference delay

A lightweight, CPU-only experiment that reproduces the core phenomenon of the
thesis at small scale: **prediction–execution misalignment** in asynchronous
VLA inference, and how **state rollforward (VLASH)** removes it.

It deliberately abstracts away the heavy π0.5 model and keeps only what matters
for the misalignment argument: delta actions, open-loop action chunks, and an
injected inference delay Δ.

## Task
A 2-D end-effector must track a **staircase target** (jumps, then holds). The
held target makes overshoot from misalignment a *pure error*, while the jumps
probe reaction. State `s ∈ ℝ²`, action = delta position, clipped to `MAX_STEP`.

## Three controllers
| Controller | Stall? | Conditioning state | Misalignment |
|---|---|---|---|
| **Sync** | yes (Δ steps) | true current state | none (gold accuracy, slow) |
| **Naive-Async** | no | stale `s_t` | grows with Δ |
| **VLASH** | no | rolled-forward `s_{t+Δ} = s_t + Σ pending deltas` | ≈ 0 |

## Metrics
- **Misalignment ε** = ‖s_exec_start − s_assumed‖ (headline quantity)
- **Tracking error** = mean ‖s − g‖
- **Success rate** = % steps within tolerance
- **Smoothness** = mean action jerk (lower = smoother)

## How to run
```bash
pip install numpy pandas matplotlib
python vlash_simulation.py
```
Outputs to `results/`: `results_raw.csv`, `results_summary.csv`,
`results_robustness.csv`, `results_noise.csv`, `results_mismatch.csv`, and 8
figures (`fig_misalignment`, `fig_tracking_error`, `fig_success`,
`fig_smoothness`, `fig_trajectory`, `fig_robustness`, `fig_noise`,
`fig_mismatch`). Reproducible (fixed seed `SEED0`), 50 trials per setting.

## Ablations (all at Δ = 3)
- **Robustness to target dynamics** (`run_robustness`): sweep of the target
  jump magnitude 0.10–0.40. Naive-Async collapses 71% → 40% while VLASH stays
  within a few points of Sync (thesis §3.3.5).
- **Actuation noise** (`run_noise`): zero-mean Gaussian noise on every EXECUTED
  action; rollforward still sums commanded deltas, so the noise is exactly what
  it cannot see. The VLASH margin survives up to σ ≈ 10% of the actuator step
  and closes only when noise dominates all controllers (thesis §3.3.6).
- **Delay misestimation** (`run_mismatch`): VLASH rolls forward Δ + e steps
  while the true delay stays Δ = 3, e ∈ [−2, +2]. A one-step error costs about
  one point of success; ±2 still clears Naive-Async by a wide margin
  (thesis §3.3.7).

## Key results (mean over 50 trials, Δ = 0…4)
- **ε:** Naive-Async grows 0 → 0.036; **VLASH stays 0** at every Δ.
- **Success @ Δ=4:** Sync 74% · **VLASH 69%** · Naive-Async 35%.
- **Tracking error @ Δ=4:** Sync 0.038 · **VLASH 0.046** · Naive-Async 0.071.
- VLASH recovers almost all of the synchronous accuracy that naive async loses,
  while staying smooth. A small residual gap to Sync remains — caused by the
  **stale visual/target observation** (rollforward fixes state, not the scene),
  exactly the limitation discussed in the thesis and the VLASH paper.

## Honest scope / limitations
- Reaction latency is treated **analytically** in the thesis (L_sync = T_exec +
  T_infer vs L_async = T_infer); the abstraction under-represents the real
  synchronous stall, so reaction latency is not claimed from this simulation.
- This is a kinematic abstraction (no contact dynamics, no real VLA); it
  *illustrates and validates* the mechanism, it does not replace the
  full-scale results reported from the VLASH paper.

> Tool note: scaffolded with a GenAI assistant; design, parameters, runs and
> analysis reviewed by the author. Declare GenAI use per supervisor policy.
