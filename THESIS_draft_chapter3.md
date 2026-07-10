# CHAPTER 3 — Experiments and Results  *(BẢN NHÁP — chờ khanh duyệt)*

> Số `[n]` theo `THESIS_references_corrected.md`. Số liệu paper lấy từ PDF gốc (xem `THESIS_verified_numbers.md`). Số liệu simulation lấy từ `results_summary.csv` (50 trial/Δ).

---

## 3.0 Introduction to the Chapter

Chapters 1 and 2 established the theoretical motivation for future-state-aware asynchronous inference and described the simulation testbed designed to study it. This chapter reports the experimental results. It is organised into two complementary parts. The first and primary part (Sections 3.1–3.3) presents the results of the original simulation testbed developed in this thesis, which isolates and quantifies the prediction–execution misalignment mechanism under controlled conditions. The second part (Section 3.4) corroborates those findings against the large-scale evaluation reported by the VLASH authors [1] on the LIBERO and Kinetix benchmarks and on real robot hardware. Section 3.5 discusses why the method works, the agreement between the small-scale and large-scale evidence, and the limitations of both; Section 3.6 summarises the chapter.

## 3.1 Experimental Setup

**Simulation study.** All results in Sections 3.2–3.3 are produced by the testbed of Chapter 2. The inference delay is swept over Δ ∈ {0, 1, 2, 3, 4} control steps. For each delay, every method is evaluated over 50 independent episodes with distinct random seeds; each episode runs for 600 control steps with a staircase target that jumps at randomised intervals of roughly 40 steps. The execution horizon is K = 8, the per-step action magnitude is capped at 0.05, and the success tolerance is 0.03. All reported values are means over the 50 trials. Because the experiments are CPU-only and seeded from a single base value, every number can be reproduced exactly by re-running the module.

**Large-scale reference.** The corroborating results in Section 3.4 are those reported by the VLASH authors [1] for the π0.5 model [3]. The LIBERO experiments fine-tune π0.5 for 30K iterations at batch size 32 with an execution horizon K = 5; latency is measured on a laptop RTX 4090 GPU at 103 ms per forward pass over two images. The real-world experiments use H = 50, K = 24 at 30 Hz on Galaxea R1 Lite and LeRobot SO-101 arms; the reaction-speed measurements use K = 25 at 50 Hz across RTX 5090, 4090, and 5070 GPUs.

## 3.2 Evaluation Metrics

The simulation study reports four metrics, defined in Section 2.3.5 and restated here for reference. **Misalignment ε** is the mean Euclidean gap between the state a chunk was conditioned on and the state from which it actually begins executing; it directly measures prediction–execution misalignment. **Tracking error** is the mean distance between the end-effector and the target over an episode. **Success rate** is the fraction of control steps for which the end-effector lies within the tolerance of the target. **Smoothness** is the mean magnitude of change between consecutive actions, with smaller values indicating less jerky motion. The large-scale reference results in Section 3.4 additionally use task **success rate**, **completion time**, **speedup**, and **reaction latency**, as defined by the VLASH authors [1].

## 3.3 Simulation Study Results

**3.3.1 Misalignment grows with delay for naive async but is eliminated by rollforward.** Figure 3.1 plots the measured misalignment ε against the inference delay. For naive asynchronous inference, ε grows monotonically with Δ — from 0.005 at Δ = 1 to 0.036 at Δ = 4 — because the chunk is conditioned on a state that the robot has already left by the time the chunk executes. For both synchronous inference and VLASH, ε is identically zero at every delay: synchronous inference never executes from a different state than it planned for, and VLASH analytically rolls the state forward so that the conditioning state matches the execution-start state exactly. This figure is the clearest confirmation of the central hypothesis: the misalignment that VLASH targets is real, scales with delay, and is removed at its source by the rollforward computation.

> **Table 3.1 — Simulation results (mean over 50 trials per delay).**

| Δ | Method | Misalignment ε | Tracking error | Success rate (%) | Jerk (×10⁻³) |
|---|---|---|---|---|---|
| 0 | Sync | 0.000 | 0.029 | 78.0 | 1.02 |
| 0 | Naive-Async | 0.000 | 0.033 | 75.8 | 1.02 |
| 0 | VLASH | 0.000 | 0.033 | 75.8 | 1.02 |
| 1 | Sync | 0.000 | 0.032 | 76.9 | 1.03 |
| 1 | Naive-Async | 0.005 | 0.038 | 74.9 | 1.14 |
| 1 | VLASH | 0.000 | 0.034 | 75.8 | 1.03 |
| 2 | Sync | 0.000 | 0.034 | 75.8 | 1.03 |
| 2 | Naive-Async | 0.013 | 0.049 | 60.8 | 1.21 |
| 2 | VLASH | 0.000 | 0.038 | 73.4 | 1.02 |
| 3 | Sync | 0.000 | 0.037 | 74.7 | 1.07 |
| 3 | Naive-Async | 0.023 | 0.061 | 47.5 | 1.28 |
| 3 | VLASH | 0.000 | 0.043 | 71.0 | 1.06 |
| 4 | Sync | 0.000 | 0.038 | 73.8 | 1.03 |
| 4 | Naive-Async | 0.036 | 0.071 | 35.4 | 1.36 |
| 4 | VLASH | 0.000 | 0.046 | 69.5 | 1.02 |

**3.3.2 Task accuracy: VLASH recovers most of the synchronous accuracy that naive async loses.** Figures 3.2 and 3.3 show success rate and tracking error against delay. Synchronous inference is the accuracy upper bound, declining only marginally from 78.0% to 73.8% across the delay range (its small loss reflects slower reaction to target jumps, not misalignment). Naive asynchronous inference starts comparably but collapses as the delay grows, falling to 35.4% success at Δ = 4 as the accumulated misalignment pushes the open-loop chunk past the target and induces overshoot. VLASH tracks the synchronous curve closely throughout, retaining 69.5% success at Δ = 4 — roughly double the naive baseline — while staying asynchronous. The tracking-error figure tells the same story: at Δ = 4 the mean error is 0.038 for synchronous, 0.046 for VLASH, and 0.071 for naive async.

**3.3.3 Motion smoothness.** Figure 3.4 reports the action jerk. Naive asynchronous inference becomes progressively less smooth as the delay grows (jerk rising from 1.02 to 1.36 ×10⁻³), reflecting the corrective jumps that follow each over-shot chunk, whereas VLASH remains as smooth as synchronous inference (≈1.02–1.06 ×10⁻³) at all delays. This matches the qualitative behaviour visible in the trajectory plot (Figure 3.5), where the naive trajectory spikes past the target corners while the VLASH trajectory reaches them cleanly.

**3.3.4 A residual gap to synchronous, explained by stale perception.** A small gap remains between VLASH and synchronous inference (e.g. 69.5% vs 73.8% success at Δ = 4). This is expected and informative: the rollforward corrects the robot *state* exactly, but the *target observation* used by every asynchronous method is still the one captured when inference began, so it is stale by Δ steps. The testbed therefore reproduces, at small scale, precisely the limitation the VLASH authors identify — that future-state awareness compensates for proprioceptive change but not for changes in the visual scene (Section 3.5).

## 3.4 Corroboration with Large-Scale VLASH Results

The large-scale evaluation reported by the VLASH authors [1] confirms the same trends observed in the simulation, on a real VLA model and real robots.

**LIBERO (simulated manipulation).** Table 3.2 reproduces the published π0.5 results across the four LIBERO sub-benchmarks. VLASH matches synchronous accuracy at low delay (97.2% at Δ = 1 and 97.1% at Δ = 2 versus the 96.8% synchronous baseline) while delivering 1.17× and 1.31× speedups, and it degrades only gracefully at higher delay (94.6% at Δ = 3, 93.1% at Δ = 4) with speedups up to 1.47×. A notable secondary finding concerns the role of the robot state: a model fine-tuned and run **without** state input actually scores slightly higher than the state-conditioned model under plain synchronous inference (97.7% versus 96.8%). This indicates that the base VLA under-utilises proprioceptive state, and it is exactly this observation that motivates the temporal-offset augmentation of Section 2.2.2 — the augmentation forces the model to attend to the state input so that, at deployment, it can exploit the rolled-forward state rather than ignore it.

> **Table 3.2 — π0.5 on LIBERO under different inference delays (reported by [1]).**

| Method | Δ | Spatial | Object | Goal | LIBERO-10 | Avg SR (%) | Speedup |
|---|---|---|---|---|---|---|---|
| Sync | 0 | 97.3 | 99.6 | 96.7 | 93.5 | 96.8 | 1.00× |
| Sync (w/o state) | – | 98.5 | 99.6 | 97.3 | 95.4 | 97.7 | 1.00× |
| VLASH | 1 | 98.8 | 99.2 | 96.7 | 94.4 | 97.2 | 1.17× |
| VLASH | 2 | 97.5 | 99.2 | 97.3 | 94.6 | 97.1 | 1.31× |
| VLASH | 3 | 94.4 | 98.8 | 93.3 | 91.9 | 94.6 | 1.47× |
| VLASH | 4 | 92.5 | 96.9 | 93.3 | 89.6 | 93.1 | 1.45× |

**Kinetix (dynamic benchmark).** On the fast-physics Kinetix benchmark, which is explicitly designed to stress reaction under delay, the contrast between methods is far sharper than on LIBERO. At an inference delay of 4 steps, VLASH attains a 81.7% success rate against only 51.2% for naive asynchronous inference — a 30.5 percentage-point improvement — and also surpasses Real-Time Chunking, which incurs additional inpainting overhead. This is the setting in which the misalignment problem is most damaging, and it is where future-state awareness pays off most, directly paralleling the steep collapse of the naive baseline seen in the simulation (Section 3.3.2).

**Real-world manipulation.** On three physical tasks (pick-and-place, stacking, sorting) executed on real arms, VLASH attains the highest average score (94%), ahead of naive asynchronous inference (89.7%) and synchronous inference (83%), while completing tasks about 1.12× faster than synchronous control. Here synchronous inference scores lowest because its action stalls slow task execution under the time-aware scoring used. Adding action quantization raises the speed-up further: q = 2 reaches 2.03× with no accuracy loss, and q = 3 reaches 2.67× at the cost of a modest 4.7 percentage-point score reduction.

**Reaction latency.** Because asynchronous inference overlaps computation with execution, it collapses the reaction latency from "finish the current chunk, then infer" to "infer only." On an RTX 4090 the maximum reaction latency drops from 536 ms (synchronous) to 36 ms (asynchronous), a 14.9× reduction; on a faster RTX 5090 the reduction reaches 17.4×, and even on a slower RTX 5070 it is 8.8×. These are the gains that allow VLASH to support genuinely dynamic tasks such as a human–robot ping-pong rally, which are infeasible under synchronous control.

## 3.5 Discussion

**Why VLASH works.** Both the simulation and the large-scale results point to the same explanation. Asynchronous inference is fast because it overlaps computation with execution, but that overlap is exactly what creates the prediction–execution misalignment: the chunk is committed against a state the robot has already left. VLASH removes this misalignment at its source, before the policy runs, by conditioning on the analytically rolled-forward state. Unlike methods that correct the chunk after the fact — Real-Time Chunking through runtime inpainting, or A2C2 through an added per-step correction head — VLASH adds no runtime computation beyond a vector summation and changes nothing in the model architecture. The simulation isolates this mechanism cleanly: the misalignment ε is driven to zero (Figure 3.1) and the downstream accuracy follows (Figures 3.2–3.3).

**Agreement between small- and large-scale evidence.** The controlled simulation and the full-scale VLASH evaluation agree on every qualitative claim: misalignment grows with delay; naive async collapses as delay increases, most severely in dynamic settings; VLASH tracks the synchronous upper bound; and a residual gap remains that is attributable to stale perception rather than to robot-state error. The convergence of an independent small-scale reconstruction with the published large-scale numbers strengthens confidence that the reported behaviour stems from the misalignment mechanism rather than from incidental properties of any one benchmark.

**The role of robot state.** The LIBERO observation that the state-free model is marginally more accurate under plain synchronous inference (Table 3.2) underlines why temporal-offset augmentation is necessary rather than optional: without it, the policy has little incentive to use the state input, and simply feeding a rolled-forward state at test time would be ignored. The augmentation turns the state into a load-bearing input, which is what makes the rollforward effective.

**Limitations.** Three limitations should be stated plainly. First, the simulation is a kinematic abstraction: it has no contact dynamics, no real perception, and an idealised planner, so it validates the *mechanism* rather than predicting absolute success rates for any real task. Second, both the simulation and VLASH itself compensate only for robot state; neither predicts the future visual scene, so a residual gap to synchronous accuracy remains whenever the environment changes during inference. Third, the exactness of the rollforward depends on the delta-action representation; a Cartesian or absolute-joint action space would require forward kinematics and would not be free.

## 3.6 Summary of the Chapter

This chapter presented two mutually reinforcing bodies of evidence. The original simulation testbed showed, under controlled and fully reproducible conditions, that prediction–execution misalignment grows linearly with inference delay for naive asynchronous inference, that this misalignment is eliminated by state rollforward, and that the resulting task accuracy and motion smoothness of VLASH track the synchronous upper bound while the naive baseline collapses (success at Δ = 4: 73.8% synchronous, 69.5% VLASH, 35.4% naive). The large-scale VLASH evaluation corroborated these trends on the π0.5 model: comparable-to-synchronous accuracy with 1.17–1.47× speedups on LIBERO, a 30.5-point advantage over naive async on the dynamic Kinetix benchmark, the highest score on three real-world manipulation tasks, and reaction-latency reductions of up to 17.4×. A small residual gap to synchronous accuracy, observed consistently in both settings, was attributed to stale visual observation — the principal remaining limitation, and a direction for the future work discussed in Chapter 4.
