"""
vlash_simulation.py
===================================================================
A lightweight, CPU-only simulation that reproduces — at small scale —
the central phenomenon studied in this thesis: prediction-execution
MISALIGNMENT in asynchronous Vision-Language-Action (VLA) inference,
and how FUTURE-STATE-AWARE inference (state rollforward, "VLASH")
removes it.

The simulation deliberately abstracts away the heavy VLA model. It
keeps ONLY the part that matters for the misalignment argument:

  * the robot moves with DELTA actions  a_t  (s_{t+1} = s_t + a_t),
  * a policy produces an OPEN-LOOP action chunk of length K,
  * inference takes Δ control steps, during which the world evolves.

Three controllers are compared:
  (1) SYNC          - robot freezes during inference (no stall hiding)
  (2) NAIVE-ASYNC   - robot keeps moving; chunk conditioned on stale s_t
  (3) VLASH         - robot keeps moving; chunk conditioned on the
                      analytically rolled-forward state s_{t+Δ}

Task: 2-D end-effector must track a MOVING target (sinusoid + random
jumps), so that BOTH reaction latency AND alignment matter.

Author: Duy Khanh Mac  (thesis: Real-Time VLA Inference for Reactive Robotics)
Tool note: scaffolded with the help of a GenAI assistant; experiments,
parameters and analysis verified by the author.  (Declare per supervisor.)
===================================================================
"""

from __future__ import annotations
import os
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")  # headless backend
import matplotlib.pyplot as plt

# ------------------------------------------------------------------
# Global experiment constants
# ------------------------------------------------------------------
DT          = 1.0       # one control step
K           = 8         # execution horizon (actions executed per chunk)
MAX_STEP    = 0.05      # max |delta| per axis per step (action clip)
EPISODE_LEN = 600       # control steps per episode
JUMP_EVERY  = 40        # target holds, then jumps (reach-and-hold task)
JUMP_SIZE   = 0.25      # magnitude of each target jump
TOL         = 0.03      # tracking tolerance for "success"
SEED0       = 20260615
QUANT       = 1.0       # action-quantization factor (1 = no quantization)


# ------------------------------------------------------------------
# Target  g_t  (the "environment") — STAIRCASE: jump, then hold.
# A held target removes the "accidental lead" confound of a smoothly
# drifting target: any overshoot from misalignment is now pure error,
# while the jumps still probe reaction latency.
# ------------------------------------------------------------------
def make_target(rng: np.random.Generator, n: int, jump_size: float = None):
    js = JUMP_SIZE if jump_size is None else jump_size
    g = np.zeros((n, 2))
    cur = np.array([0.5, 0.5])
    jumps = []
    next_jump = int(rng.integers(JUMP_EVERY - 8, JUMP_EVERY + 8))  # random phase
    for t in range(n):
        if t == next_jump:
            cur = np.clip(cur + rng.uniform(-js, js, size=2), 0.1, 0.9)
            jumps.append(t)
            next_jump = t + int(rng.integers(JUMP_EVERY - 8, JUMP_EVERY + 8))
        g[t] = cur
    return g, np.array(jumps)


# ------------------------------------------------------------------
# Policy:  open-loop chunk planner
# ------------------------------------------------------------------
def plan_chunk(s_cond: np.ndarray, g_obs: np.ndarray) -> np.ndarray:
    """
    Plan an OPEN-LOOP chunk of H delta-actions that, if executed from the
    conditioning state s_cond, drives the end-effector onto the observed
    target g_obs over the execution horizon K.

    This is the crux: the chunk is a fixed list of deltas. If it is later
    executed from a DIFFERENT start state, every delta is the same but the
    landing point shifts by exactly (actual_start - s_cond) = the
    misalignment error epsilon.
    """
    direction = (g_obs - s_cond) / K            # constant-velocity to target
    # QUANT models action quantization: a macro-action of q grouped deltas covers
    # up to q times the per-step distance, so the robot moves q times faster.
    direction = np.clip(direction, -MAX_STEP * QUANT, MAX_STEP * QUANT)
    return np.tile(direction, (K, 1))           # K identical deltas


# ------------------------------------------------------------------
# Controllers
# ------------------------------------------------------------------
def _exec_noise(rng, sd):
    """Zero-mean Gaussian actuation noise added to each EXECUTED action.
    The commanded delta stays what the policy planned; only the realised
    motion differs. Rollforward sums commanded deltas, so this noise is
    exactly the part of the future state it cannot see."""
    if rng is None or sd <= 0.0:
        return 0.0
    return rng.normal(0.0, sd, 2)


def run_sync(g_true: np.ndarray, delta: int, noise_sd: float = 0.0, nrng=None):
    """
    SYNCHRONOUS: each inference the robot FREEZES for `delta` steps
    (action stall), then executes a chunk of K actions. No misalignment
    (it plans and executes from the same state) but slow to react.
    """
    n = len(g_true)
    s = np.array([0.5, 0.5]); pos = []; acts = []; eps = []
    t = 0
    while t < n:
        for _ in range(delta):                  # --- stall during inference ---
            if t >= n: break
            pos.append(s.copy()); acts.append(np.zeros(2)); eps.append(0.0); t += 1
        if t >= n: break
        g_obs = g_true[t]                        # observe AFTER the stall
        chunk = plan_chunk(s, g_obs)
        for k in range(K):
            if t >= n: break
            a = chunk[k]; s = s + a + _exec_noise(nrng, noise_sd)
            pos.append(s.copy()); acts.append(a); eps.append(0.0); t += 1
    return np.array(pos[:n]), np.array(acts[:n]), np.array(eps[:n])


def run_async(g_true: np.ndarray, delta: int, rollforward: bool,
              noise_sd: float = 0.0, nrng=None, assumed_delta: int = None):
    """
    ASYNCHRONOUS: the robot never stalls. Inference launched `delta` steps
    before the current chunk runs out; the new chunk is conditioned on
    either the stale state (naive) or the rolled-forward state (VLASH),
    and starts executing `delta` steps later.

    rollforward=False -> NAIVE-ASYNC ; rollforward=True -> VLASH
    """
    n = len(g_true)
    s = np.array([0.5, 0.5]); pos = []; acts = []; eps = []
    cur = plan_chunk(s, g_true[0]); cur_k = 0
    pending = None
    s_launch = None                              # true state at launch (for ε bookkeeping)

    t = 0
    while t < n:
        # launch next inference `delta` steps before the chunk is exhausted
        if cur_k == K - delta and pending is None:
            g_obs = g_true[t]                    # target obs is STALE (future unknown)
            s_launch = s.copy()
            if rollforward:                      # roll state forward through known pending deltas
                d_ass = delta if assumed_delta is None else max(0, assumed_delta)
                s_future = s.copy()
                for j in range(d_ass):
                    # clamp: if the assumed delay overruns the chunk, extrapolate
                    # with the last commanded delta (chunk deltas are constant)
                    s_future = s_future + cur[min(cur_k + j, K - 1)]
                s_cond = s_future                # future-state-aware (exact iff d_ass == delta, no noise)
            else:
                s_cond = s.copy()                # stale current state
            pending = plan_chunk(s_cond, g_obs)

        a = cur[cur_k]; s = s + a + _exec_noise(nrng, noise_sd)   # execute one action
        pos.append(s.copy()); acts.append(a)
        cur_k += 1

        # swap when the chunk is exhausted (pending is ready by construction)
        if cur_k >= K:
            # misalignment actually incurred this cycle = |s_exec_start - s_assumed|
            eps_cycle = float(np.linalg.norm(s - s_launch)) if (s_launch is not None and not rollforward) else 0.0
            eps.append(eps_cycle)
            if pending is not None:
                cur = pending; pending = None
            else:
                cur = plan_chunk(s, g_true[t])
            cur_k = 0
            s_launch = None
        else:
            eps.append(eps[-1] if eps else 0.0)
        t += 1
    return np.array(pos[:n]), np.array(acts[:n]), np.array(eps[:n])


# ------------------------------------------------------------------
# Metrics
# ------------------------------------------------------------------
def metrics(pos, acts, g_true, eps, jumps, delta):
    err = np.linalg.norm(pos - g_true, axis=1)
    mean_err = float(err.mean())
    # smoothness: mean magnitude of action change (jerk proxy)
    jerk = float(np.linalg.norm(np.diff(acts, axis=0), axis=1).mean())
    # success: fraction of steps within tolerance
    success = float((err < TOL).mean())
    # mean misalignment error epsilon (the headline quantity)
    misalign = float(np.mean(eps))
    # reaction latency: steps after each jump until error first recovers below 2*TOL
    lat = []
    for j in jumps:
        seg = err[j:j + JUMP_EVERY]
        below = np.where(seg < 2 * TOL)[0]
        lat.append(int(below[0]) if len(below) else JUMP_EVERY)
    reaction = float(np.mean(lat)) if lat else 0.0
    return dict(mean_err=mean_err, jerk=jerk, success=success,
                misalign=misalign, reaction=reaction)


# ------------------------------------------------------------------
# Experiment driver
# ------------------------------------------------------------------
def run_all(deltas=(0, 1, 2, 3, 4), trials=50, outdir="."):
    rows = []
    traj_cache = {}   # for the example-trajectory figure
    for delta in deltas:
        for tr in range(trials):
            rng = np.random.default_rng(SEED0 + 1000 * delta + tr)
            g, jumps = make_target(rng, EPISODE_LEN)

            runs = {
                "Sync":        run_sync(g, delta),
                "Naive-Async": run_async(g, delta, rollforward=False),
                "VLASH":       run_async(g, delta, rollforward=True),
            }
            for name, (pos, acts, eps) in runs.items():
                m = metrics(pos, acts, g, eps, jumps, delta)
                m.update(method=name, delta=delta, trial=tr)
                rows.append(m)
                if tr == 0 and delta == 3:
                    traj_cache[name] = (pos, g, jumps)

    df = pd.DataFrame(rows)
    os.makedirs(outdir, exist_ok=True)
    df.to_csv(os.path.join(outdir, "results_raw.csv"), index=False)

    # aggregate (mean + standard deviation over trials)
    agg = (df.groupby(["method", "delta"])
             .agg(mean_err=("mean_err", "mean"), sd_err=("mean_err", "std"),
                  jerk=("jerk", "mean"),
                  success=("success", "mean"), sd_success=("success", "std"),
                  misalign=("misalign", "mean"),
                  reaction=("reaction", "mean"))
             .reset_index())
    agg.to_csv(os.path.join(outdir, "results_summary.csv"), index=False)
    return df, agg, traj_cache


# ------------------------------------------------------------------
# Figures
# ------------------------------------------------------------------
COLORS = {"Sync": "#2c7fb8", "Naive-Async": "#d95f0e", "VLASH": "#31a354"}


def fig_tracking_error(agg, outdir):
    plt.figure(figsize=(6, 4))
    for m in ["Sync", "Naive-Async", "VLASH"]:
        sub = agg[agg.method == m].sort_values("delta")
        plt.errorbar(sub.delta, sub.mean_err, yerr=sub.sd_err, fmt="o-",
                     color=COLORS[m], label=m, lw=2, capsize=3, elinewidth=1)
    plt.xlabel("Inference delay  Δ  (control steps)")
    plt.ylabel("Mean tracking error  ||s − g||")
    plt.title("Tracking error vs inference delay  (±1 SD over 50 trials)")
    plt.legend(); plt.grid(alpha=.3); plt.tight_layout()
    plt.savefig(os.path.join(outdir, "fig_tracking_error.png"), dpi=160)
    plt.close()


def fig_success(agg, outdir):
    plt.figure(figsize=(6, 4))
    for m in ["Sync", "Naive-Async", "VLASH"]:
        sub = agg[agg.method == m].sort_values("delta")
        plt.errorbar(sub.delta, 100 * sub.success, yerr=100 * sub.sd_success, fmt="s-",
                     color=COLORS[m], label=m, lw=2, capsize=3, elinewidth=1)
    plt.xlabel("Inference delay  Δ  (control steps)")
    plt.ylabel("Success rate (% steps within tolerance)")
    plt.title("Success rate vs inference delay  (±1 SD over 50 trials)")
    plt.legend(); plt.grid(alpha=.3); plt.tight_layout()
    plt.savefig(os.path.join(outdir, "fig_success.png"), dpi=160)
    plt.close()


def fig_smoothness(agg, outdir):
    plt.figure(figsize=(6, 4))
    for m in ["Sync", "Naive-Async", "VLASH"]:
        sub = agg[agg.method == m].sort_values("delta")
        plt.plot(sub.delta, 1000 * sub.jerk, "^-", color=COLORS[m], label=m, lw=2)
    plt.xlabel("Inference delay  Δ  (control steps)")
    plt.ylabel("Action jerk  (×10⁻³, lower = smoother)")
    plt.title("Motion smoothness vs inference delay")
    plt.legend(); plt.grid(alpha=.3); plt.tight_layout()
    plt.savefig(os.path.join(outdir, "fig_smoothness.png"), dpi=160)
    plt.close()


def fig_misalign(agg, outdir):
    plt.figure(figsize=(6, 4))
    for m in ["Sync", "Naive-Async", "VLASH"]:
        sub = agg[agg.method == m].sort_values("delta")
        plt.plot(sub.delta, sub.misalign, "D-", color=COLORS[m], label=m, lw=2)
    plt.xlabel("Inference delay  Δ  (control steps)")
    plt.ylabel("Mean misalignment error  ε = ‖s_exec − s_assumed‖")
    plt.title("Prediction–execution misalignment vs delay")
    plt.legend(); plt.grid(alpha=.3); plt.tight_layout()
    plt.savefig(os.path.join(outdir, "fig_misalignment.png"), dpi=160)
    plt.close()


def run_robustness(outdir, delta=3, trials=50, sizes=(0.10, 0.20, 0.30, 0.40)):
    """Sweep the target jump magnitude (how dynamic the environment is) at a fixed
    delay and record the success rate of each controller. Larger jumps mean faster
    motion during inference, so the naive misalignment grows and its accuracy should
    fall away faster than VLASH and synchronous inference."""
    rows = []
    for js in sizes:
        for tr in range(trials):
            rng = np.random.default_rng(SEED0 + 9000 + int(js * 1000) + tr)
            g, jumps = make_target(rng, EPISODE_LEN, jump_size=js)
            runs = {
                "Sync":        run_sync(g, delta),
                "Naive-Async": run_async(g, delta, rollforward=False),
                "VLASH":       run_async(g, delta, rollforward=True),
            }
            for name, (pos, acts, eps) in runs.items():
                m = metrics(pos, acts, g, eps, jumps, delta)
                rows.append(dict(jump=js, method=name, success=m["success"]))
    df = pd.DataFrame(rows)
    agg = (df.groupby(["method", "jump"]).agg(success=("success", "mean")).reset_index())
    agg.to_csv(os.path.join(outdir, "results_robustness.csv"), index=False)
    return agg


def fig_robustness(agg, outdir):
    plt.figure(figsize=(6.2, 4))
    for m in ["Sync", "Naive-Async", "VLASH"]:
        sub = agg[agg.method == m].sort_values("jump")
        plt.plot(sub.jump, 100 * sub.success, "o-", color=COLORS[m], label=m, lw=2)
    plt.xlabel("Target jump magnitude  (more dynamic →)")
    plt.ylabel("Success rate (%)")
    plt.title("Robustness to target dynamics  (Δ = 3)")
    plt.legend(); plt.grid(alpha=.3); plt.tight_layout()
    plt.savefig(os.path.join(outdir, "fig_robustness.png"), dpi=160)
    plt.close()


def run_noise(outdir, delta=3, trials=50, sigmas=(0.0, 0.0025, 0.005, 0.01, 0.02)):
    """Sweep zero-mean Gaussian actuation noise (per axis, per step) added to
    every EXECUTED action. State rollforward sums COMMANDED deltas, so under
    noise the rolled-forward state misses the accumulated noise of the pending
    steps (about sigma * sqrt(2*delta) in norm). The sweep asks how fast that
    unmodelled drift erodes the VLASH advantage over naive-async."""
    rows = []
    for sd in sigmas:
        for tr in range(trials):
            rng = np.random.default_rng(SEED0 + 31000 + int(sd * 100000) + tr)
            g, jumps = make_target(rng, EPISODE_LEN)
            nseed = SEED0 + 77000 + int(sd * 100000) + 91 * tr
            runs = {
                "Sync":        run_sync(g, delta, noise_sd=sd,
                                        nrng=np.random.default_rng(nseed + 1)),
                "Naive-Async": run_async(g, delta, rollforward=False, noise_sd=sd,
                                         nrng=np.random.default_rng(nseed + 2)),
                "VLASH":       run_async(g, delta, rollforward=True, noise_sd=sd,
                                         nrng=np.random.default_rng(nseed + 3)),
            }
            for name, (pos, acts, eps) in runs.items():
                m = metrics(pos, acts, g, eps, jumps, delta)
                rows.append(dict(sigma=sd, method=name,
                                 success=m["success"], mean_err=m["mean_err"]))
    df = pd.DataFrame(rows)
    agg = (df.groupby(["method", "sigma"])
             .agg(success=("success", "mean"), sd_success=("success", "std"),
                  mean_err=("mean_err", "mean"))
             .reset_index())
    agg.to_csv(os.path.join(outdir, "results_noise.csv"), index=False)
    return agg


def fig_noise(agg, outdir):
    plt.figure(figsize=(6.2, 4))
    for m in ["Sync", "Naive-Async", "VLASH"]:
        sub = agg[agg.method == m].sort_values("sigma")
        plt.errorbar(sub.sigma, 100 * sub.success, yerr=100 * sub.sd_success,
                     fmt="o-", color=COLORS[m], label=m, lw=2, capsize=3,
                     elinewidth=1)
    plt.xlabel("Actuation noise  σ  (per axis, per step; actuator step = 0.05)")
    plt.ylabel("Success rate (%)")
    plt.title("Sensitivity to actuation noise  (Δ = 3)")
    plt.legend(); plt.grid(alpha=.3); plt.tight_layout()
    plt.savefig(os.path.join(outdir, "fig_noise.png"), dpi=160)
    plt.close()


def run_mismatch(outdir, delta=3, trials=50, errors=(-2, -1, 0, 1, 2)):
    """VLASH needs an estimate of the delay to know HOW FAR to roll the state
    forward. Real inference latency jitters, so the estimate can be off. Sweep
    a systematic estimation error e: the controller rolls forward delta + e
    steps while the true delay stays at delta. e = -delta would reduce to
    naive-async; e = 0 is exact VLASH."""
    rows = []
    for e in errors:
        for tr in range(trials):
            rng = np.random.default_rng(SEED0 + 52000 + 1000 * (e + 10) + tr)
            g, jumps = make_target(rng, EPISODE_LEN)
            pos, acts, eps = run_async(g, delta, rollforward=True,
                                       assumed_delta=delta + e)
            m = metrics(pos, acts, g, eps, jumps, delta)
            rows.append(dict(err=e, method="VLASH", success=m["success"]))
    # reference levels: naive-async and sync on the same task distribution
    ref = {"Naive-Async": [], "Sync": []}
    for tr in range(trials):
        rng = np.random.default_rng(SEED0 + 52000 + 1000 * 10 + tr)  # same targets as e=0
        g, jumps = make_target(rng, EPISODE_LEN)
        pos, acts, eps = run_async(g, delta, rollforward=False)
        ref["Naive-Async"].append(metrics(pos, acts, g, eps, jumps, delta)["success"])
        pos, acts, eps = run_sync(g, delta)
        ref["Sync"].append(metrics(pos, acts, g, eps, jumps, delta)["success"])
    df = pd.DataFrame(rows)
    agg = (df.groupby("err")
             .agg(success=("success", "mean"), sd_success=("success", "std"))
             .reset_index())
    agg["naive_ref"] = float(np.mean(ref["Naive-Async"]))
    agg["sync_ref"] = float(np.mean(ref["Sync"]))
    agg.to_csv(os.path.join(outdir, "results_mismatch.csv"), index=False)
    return agg


def fig_mismatch(agg, outdir):
    plt.figure(figsize=(6.2, 4))
    plt.errorbar(agg.err, 100 * agg.success, yerr=100 * agg.sd_success,
                 fmt="o-", color=COLORS["VLASH"], lw=2, capsize=3, elinewidth=1,
                 label="VLASH (misestimated Δ)")
    plt.axhline(100 * agg.naive_ref.iloc[0], color=COLORS["Naive-Async"],
                ls="--", lw=1.8, label="Naive-Async (no rollforward)")
    plt.axhline(100 * agg.sync_ref.iloc[0], color=COLORS["Sync"],
                ls=":", lw=1.8, label="Sync (upper reference)")
    plt.xticks(agg.err)
    plt.xlabel("Delay estimation error  e = Δ_assumed − Δ_true  (steps)")
    plt.ylabel("Success rate (%)")
    plt.title("Sensitivity to delay misestimation  (Δ_true = 3)")
    plt.legend(); plt.grid(alpha=.3); plt.tight_layout()
    plt.savefig(os.path.join(outdir, "fig_mismatch.png"), dpi=160)
    plt.close()


def fig_trajectory(traj_cache, outdir):
    """Position-vs-time view: clearer than a 2-D tangle. Shows the x-coordinate
    of the end-effector tracking the (step-shaped) target over a short window,
    so naive overshoot after each target jump is directly visible."""
    if not traj_cache:
        return
    W = 230  # window of control steps (a few target jumps -> readable)
    g = next(iter(traj_cache.values()))[1]
    t = range(W)
    plt.figure(figsize=(7.6, 3.7))
    plt.step(t, g[:W, 0], where="post", color="black", ls="--", lw=1.6,
             alpha=.8, label="Target (x)")
    for m in ["Sync", "Naive-Async", "VLASH"]:
        if m in traj_cache:
            pos = traj_cache[m][0]
            plt.plot(t, pos[:W, 0], color=COLORS[m], lw=1.6, label=m, alpha=.95)
    plt.xlabel("Control step"); plt.ylabel("End-effector x-coordinate")
    plt.title("Tracking over time at Δ = 3  (x-coordinate)")
    plt.legend(loc="upper right", ncol=2, fontsize=8)
    plt.grid(alpha=.3); plt.tight_layout()
    plt.savefig(os.path.join(outdir, "fig_trajectory.png"), dpi=160)
    plt.close()


# ------------------------------------------------------------------
if __name__ == "__main__":
    OUT = os.path.join(os.path.dirname(__file__), "results")
    df, agg, traj = run_all(outdir=OUT)
    fig_tracking_error(agg, OUT)
    fig_success(agg, OUT)
    fig_smoothness(agg, OUT)
    fig_misalign(agg, OUT)
    fig_trajectory(traj, OUT)

    robust = run_robustness(OUT)
    fig_robustness(robust, OUT)

    noise = run_noise(OUT)
    fig_noise(noise, OUT)

    mism = run_mismatch(OUT)
    fig_mismatch(mism, OUT)

    pd.set_option("display.width", 120)
    print("\n=== SUMMARY (mean over 50 trials per Δ) ===")
    print(agg.to_string(index=False))
    print("\n=== ROBUSTNESS to target dynamics (Δ=3, mean over 50 trials) ===")
    print(robust.pivot(index="jump", columns="method", values="success").to_string())
    print("\n=== ACTUATION NOISE sweep (Δ=3, mean over 50 trials) ===")
    print(noise.pivot(index="sigma", columns="method", values="success").to_string())
    print("\n=== DELAY MISESTIMATION sweep (Δ_true=3, VLASH, 50 trials) ===")
    print(mism.to_string(index=False))
    print(f"\nSaved CSV + figures to: {OUT}")
