# CHAPTER 2 — System Design and Methodology  *(BẢN NHÁP — Bước A, chờ khanh duyệt)*

> Citation đang dùng số `[n]` theo `THESIS_references_corrected.md`:
> [1]VLASH [2]π0 [3]π0.5 [4]SmolVLA [5]RTC [6]A2C2 [7]LIBERO [8]ACT
> [9]Kinetix [10]LoRA [11]Flow Matching [12]RT-2 [13]PaliGemma [14]SigLIP [15]GR00T [16]OpenVLA

---

## 2.0 Introduction to the Chapter

Chapter 1 established why synchronous VLA inference is insufficient for reactive robotics, and why existing asynchronous approaches fail to simultaneously achieve zero runtime overhead, architectural compatibility, and accurate misalignment compensation. The present chapter describes the methodology and the system designed in this thesis to study and validate a solution to that problem.

The contribution of this thesis is twofold. First, it studies the **VLASH** method [1] — a future-state-aware asynchronous inference framework for VLA models — and presents it in a unified, self-contained form (Section 2.2). Second, and central to the practical part of this work, it designs and implements an **original simulation testbed** (Sections 2.3–2.4) that reproduces, in a controlled and fully reproducible setting, the prediction–execution misalignment phenomenon and quantifies how three different inference strategies — synchronous, naive asynchronous, and future-state-aware (VLASH) — behave as the inference delay grows. The testbed deliberately abstracts away the heavy VLA model so that the misalignment mechanism can be isolated, measured, and visualised without access to large-scale GPU clusters.

The chapter is organised as follows. Section 2.1 states the system goals and scope. Section 2.2 summarises the VLASH method under study. Section 2.3 describes the design of the simulation testbed: the tracking task, the state and action representation, the inference-delay model, the three controllers (with their algorithms), and the evaluation metrics. Section 2.4 documents the implementation, parameters, tools, and reproducibility. Section 2.5 relates the abstracted testbed to the full-scale reference implementation (the VLASH codebase, π0.5, and the LIBERO benchmark) and to the author's own hardware. Section 2.6 summarises the chapter.

## 2.1 Overview and Objectives of the System

**Goal.** The system developed in this thesis is a lightweight, CPU-only **simulation testbed** whose purpose is to demonstrate, measure, and compare the three inference strategies introduced in Chapter 1 under a common, controlled task. The guiding question is operational: *as the inference delay Δ increases, how does each strategy degrade — in accuracy, in motion smoothness, and in the underlying prediction–execution misalignment?*

**Scope and assumptions.** To isolate the misalignment mechanism, the testbed makes three simplifying assumptions, each justified by the analysis in Chapter 1:

1. The robot is modelled as a point end-effector moving in a 2-D plane; its configuration is captured by a low-dimensional state vector. This preserves the *delta-action* property that makes state rollforward exact (Section 2.2) while removing the cost of a full kinematic or contact-dynamics simulator.
2. The policy is replaced by a deterministic open-loop *chunk planner* that produces a sequence of delta actions toward an observed target. This retains the essential structure of action chunking — a block of actions committed in advance — which is the structural cause of misalignment.
3. The inference delay Δ is modelled directly as an integer number of control steps, allowing it to be swept as an independent variable rather than measured from wall-clock timing on a particular GPU.

Under these assumptions the testbed is not a substitute for the full-scale VLA experiments reported by the VLASH authors [1]; rather, it is an instrument that *illustrates and validates the mechanism* at small scale, with complete reproducibility and transparency. The full-scale results are used in Section 3.4 as large-scale corroboration.

## 2.2 The VLASH Method Under Study

This section summarises the method that the testbed implements and evaluates. It condenses the four components of VLASH [1] introduced informally in Chapter 1.

**2.2.1 State rollforward (inference).** Under asynchronous inference, when the policy is queried at control step *t*, the robot is still executing the pending actions of the current chunk. Because actions are *delta joint positions* (`s_{t+1} = s_t + a_t`), the future state at which the new chunk will begin executing can be computed exactly and at negligible cost as a vector sum over the already-known pending actions:

```
s_{t+Δ} = s_t + Σ_{i=0}^{Δ−1} a_{t+i}
```

The policy is then conditioned on this analytically rolled-forward state instead of the stale current state, `π_θ(A_{t+Δ} | o_t, s_{t+Δ})`. This single substitution is the entire runtime change; it removes the state-misalignment error without any additional model call.

**2.2.2 Temporal-offset augmentation (training).** State rollforward only helps if the policy has learned to exploit a future state that is temporally offset from the observation. VLASH achieves this during fine-tuning by sampling a random offset `δ ~ Uniform{0, …, max_delay_steps}` for each training sample and forming the pair `(o_t, s_{t+δ}) → a_{t+δ : t+δ+H}` — the observation at *t* but the state and target actions at *t + δ*. Training across the full range of offsets makes the policy robust to any inference delay, including the synchronous case δ = 0.

**2.2.3 Shared-observation optimisation (efficiency).** Because every offset for a given timestep shares the same ~700-token observation, VLASH packs N offset branches into a single forward pass with a block-sparse attention mask: observation tokens are encoded once and attended to by all branches, while each state–action branch is isolated from the others. This yields the reported ~3.26× training speedup at equal effective batch size.

**2.2.4 Action quantization (optional speed-up).** Grouping *q* consecutive delta actions into one macro-action `â_i = a_{iq} + … + a_{(i+1)q−1}` lets the policy emit `H/q` outputs per chunk, trading temporal resolution for throughput. The VLASH authors report a 2.03× end-to-end speed-up at q = 2 with negligible accuracy loss on real-world tasks [1].

Of these four components, the testbed in this thesis focuses on the one that governs deployment-time behaviour — **state rollforward** (2.2.1) — since it is the component responsible for the accuracy difference between naive asynchronous and future-state-aware inference. Temporal-offset augmentation (2.2.2) is modelled implicitly: the chunk planner is, by construction, able to use whichever conditioning state it is given, which corresponds to an idealised policy that has been perfectly trained with offset augmentation.

## 2.3 Design of the Simulation Testbed

**2.3.1 The tracking task.** The testbed implements a *reactive reaching* task. A point end-effector with position `s ∈ ℝ²` must keep itself on a moving target `g_t ∈ ℝ²`. The target follows a **staircase** profile: it holds a fixed position for a randomised interval (≈ 40 control steps) and then jumps by a random displacement of magnitude up to 0.25 before holding again. The held segments make any overshoot caused by misalignment a *pure tracking error* (a smoothly drifting target was rejected during design because it allows naive overshoot to accidentally anticipate the target, masking the very effect under study), while the jumps probe how quickly each strategy reacts to a sudden change.

**2.3.2 State and action representation.** Consistent with the delta-action property exploited by VLASH, the action is an incremental displacement `a ∈ ℝ²`, clipped to a maximum magnitude per step, and the dynamics are the exact summation `s_{t+1} = s_t + a_t`. This is the minimal representation for which state rollforward is exact.

**2.3.3 The chunk planner.** Given a conditioning state `s_cond` and an observed target `g_obs`, the planner produces an open-loop chunk of *K* identical delta actions that, if executed from `s_cond`, drive the end-effector onto `g_obs`:

```
a_k = clip( (g_obs − s_cond) / K , −MAX_STEP, +MAX_STEP ),   k = 0 … K−1
```

The chunk is *open-loop*: the same fixed deltas are applied wherever the robot actually is. If the chunk is later executed from a different start state, every delta is unchanged but the landing point shifts by exactly the misalignment `ε = s_exec_start − s_cond`. This makes the planner an ideal probe for the misalignment mechanism.

**2.3.4 The three controllers.** All three share the planner; they differ only in *when* inference runs and *which state* it conditions on.

*Algorithm 1 — Synchronous.* The robot freezes for Δ steps (the action stall) while inference runs, then executes a chunk of K actions planned from the state it just observed. There is no misalignment (it plans and executes from the same state) but the robot is idle during every inference and reacts slowly to target jumps.

*Algorithm 2 — Naive asynchronous.* The robot never freezes. Inference for the next chunk is launched Δ steps before the current chunk is exhausted and conditioned on the **stale** current state `s_t`; the resulting chunk begins executing Δ steps later, from `s_{t+Δ}`. The incurred misalignment is `ε = ‖s_{t+Δ} − s_t‖`, i.e. the displacement accumulated during inference.

*Algorithm 3 — VLASH (future-state-aware).* Identical to Algorithm 2 except that the conditioning state is rolled forward through the known pending deltas, `s_cond = s_t + Σ_{j=0}^{Δ−1} a_{t+j}`. Because those deltas are exactly the ones that will execute before the swap, the rolled-forward state equals the true execution-start state, and the modelled misalignment is `ε = 0` by construction. Note that the target observation `g_obs` remains stale in all asynchronous cases — the simulation cannot see the future scene — which faithfully reproduces VLASH's stated limitation that rollforward compensates for robot state but not for visual change.

**2.3.5 Evaluation metrics.** Four metrics are recorded per episode and averaged over trials:

- **Misalignment ε** — the mean `‖s_exec_start − s_assumed‖` per chunk swap; the headline quantity that directly measures prediction–execution misalignment.
- **Tracking error** — the mean Euclidean distance `‖s − g‖` over the episode.
- **Success rate** — the fraction of control steps for which `‖s − g‖` is within a fixed tolerance.
- **Smoothness (jerk)** — the mean magnitude of the change between consecutive actions, `mean ‖a_k − a_{k−1}‖`; lower is smoother.

Reaction latency is treated analytically in this thesis (Section 2.4 and Chapter 3) rather than measured from the testbed, because the kinematic abstraction under-represents the true synchronous stall and would therefore understate the asynchronous reaction advantage established in Chapter 1.

## 2.4 Implementation

The testbed is implemented in **Python 3** using **NumPy** for the dynamics and metrics and **Matplotlib** for the figures; no machine-learning framework or GPU is required, so the experiments run in seconds on a standard laptop. The implementation is a single, documented module (`vlash_simulation.py`) organised into the target generator, the chunk planner, the three controllers, the metric functions, and an experiment driver that sweeps the delay and aggregates results.

**Parameters.** The principal parameters are the execution horizon `K = 8`, the action clip `MAX_STEP = 0.05`, the target jump interval (≈ 40 steps) and magnitude (0.25), the success tolerance (0.03), and the episode length (600 steps). Each delay level Δ ∈ {0, 1, 2, 3, 4} is evaluated over 50 independent trials with distinct random seeds; every figure and table reported in Chapter 3 is the mean over those trials.

**Reproducibility.** All randomness derives from a single base seed, so every reported number can be regenerated exactly by re-running the module. Raw per-trial results and aggregated summaries are written to CSV alongside the figures.

**Tools and libraries.** Python 3.11, NumPy, pandas (aggregation/CSV), and Matplotlib (Agg backend, headless). Development used Git for version control and VS Code as the editor.

## 2.5 Relation to the Full-Scale Reference Implementation

The abstracted testbed is intentionally a small model of a much larger system. The full-scale reference — used for the corroborating results in Section 3.4 — is the VLASH codebase [1] built on HuggingFace LeRobot, which fine-tunes the **π0.5** model [3] (a PaliGemma vision-language backbone [13] with a Gemma action expert and a flow-matching action head [11]) on the **LIBERO** manipulation benchmark [7]. There, the state is the 8-dimensional Franka Panda configuration (seven joint angles and a gripper), the observation is two 224×224 RGB images plus a language instruction, and the action is an 8-dimensional delta joint command — the same delta property the testbed relies on.

This thesis also targets eventual execution on the author's own hardware, an **NVIDIA RTX 3050 (6 GB)** laptop, for which the reference configuration uses 4-bit QLoRA quantization and LoRA adapters to fit the model in memory. A full fine-tune and LIBERO evaluation on this hardware is identified as the natural next step in Section 4.1; the simulation testbed in this chapter is the feasible, self-contained practical contribution delivered within the scope of this thesis.

## 2.6 Summary of the Chapter

This chapter presented the methodology of the thesis. It summarised the VLASH method under study — state rollforward, temporal-offset augmentation, the shared-observation optimisation, and action quantization (Section 2.2) — and then described the original contribution: a lightweight, fully reproducible simulation testbed that implements a reactive reaching task with delta actions and an explicit inference-delay model (Section 2.3), realising three controllers (synchronous, naive asynchronous, and VLASH) that differ only in the state on which they condition. Four metrics — misalignment, tracking error, success rate, and smoothness — were defined to quantify behaviour as the delay grows. Section 2.4 documented the implementation, parameters, and reproducibility, and Section 2.5 related the testbed to the full-scale π0.5/LIBERO reference and to the author's target hardware. Chapter 3 reports the results of this testbed and corroborates them against the large-scale VLASH evaluation.
