"""Generate conceptual diagrams for the thesis (schematic, reproducible)."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

OUT = os.path.dirname(__file__)
BLUE, ORANGE, GREEN, GREY = "#2c7fb8", "#d95f0e", "#31a354", "#888888"


# ---------------------------------------------------------------
# Figure A — three inference paradigms (timeline)
# ---------------------------------------------------------------
def timeline():
    fig, ax = plt.subplots(figsize=(8.4, 4.2))
    ax.set_xlim(0, 12); ax.set_ylim(0, 6.2); ax.axis("off")
    rows = [("Synchronous", 5.2, BLUE), ("Naive Async", 3.1, ORANGE), ("VLASH", 1.0, GREEN)]

    def block(x, y, w, h, color, label, hatch=None, alpha=1.0):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02",
                     fc=color, ec="black", lw=0.8, alpha=alpha, hatch=hatch))
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
                fontsize=8, color="white", weight="bold")

    # Synchronous: infer (stall) then execute, sequential
    block(0.3, 5.2, 1.6, 0.6, BLUE, "infer")
    ax.add_patch(Rectangle((1.9, 5.2), 1.0, 0.6, fc="none", ec=GREY, hatch="////", lw=0.6))
    ax.text(2.4, 5.5, "STALL", ha="center", va="center", fontsize=6.5, color=GREY)
    block(2.9, 5.2, 2.6, 0.6, BLUE, "execute chunk")
    block(5.5, 5.2, 1.6, 0.6, BLUE, "infer")
    ax.add_patch(Rectangle((7.1, 5.2), 1.0, 0.6, fc="none", ec=GREY, hatch="////", lw=0.6))
    block(8.1, 5.2, 2.6, 0.6, BLUE, "execute chunk")

    # Naive async: overlap; new chunk conditioned on stale state
    block(0.3, 3.1, 2.6, 0.6, ORANGE, "execute chunk 0")
    block(2.9, 3.1, 2.6, 0.6, ORANGE, "execute chunk 1")
    block(5.5, 3.1, 2.6, 0.6, ORANGE, "execute chunk 2")
    block(2.0, 3.85, 1.7, 0.5, "#b34700", "infer(s_t)", alpha=0.9)
    block(4.6, 3.85, 1.7, 0.5, "#b34700", "infer(s_t)", alpha=0.9)
    ax.annotate("misaligned: planned at s_t,\nexecuted at s_{t+Δ}", (3.7, 3.0),
                (6.5, 2.35), fontsize=7, color=ORANGE,
                arrowprops=dict(arrowstyle="->", color=ORANGE))

    # VLASH: overlap; new chunk conditioned on rolled-forward state
    block(0.3, 1.0, 2.6, 0.6, GREEN, "execute chunk 0")
    block(2.9, 1.0, 2.6, 0.6, GREEN, "execute chunk 1")
    block(5.5, 1.0, 2.6, 0.6, GREEN, "execute chunk 2")
    block(2.0, 1.75, 2.0, 0.5, "#1d6b34", "infer(s_{t+Δ})", alpha=0.95)
    block(4.6, 1.75, 2.0, 0.5, "#1d6b34", "infer(s_{t+Δ})", alpha=0.95)
    ax.annotate("aligned: rolled-forward\nstate matches execution", (3.9, 0.95),
                (6.7, 0.25), fontsize=7, color=GREEN,
                arrowprops=dict(arrowstyle="->", color=GREEN))

    for name, y, c in rows:
        ax.text(-0.0, y + 0.95 if name != "Synchronous" else y + 0.3, "", fontsize=1)
    ax.text(0.3, 5.95, "Synchronous — stall during inference, slow reaction", fontsize=8.5, weight="bold", color=BLUE)
    ax.text(0.3, 4.55, "Naive Async — no stall, but prediction–execution misalignment", fontsize=8.5, weight="bold", color=ORANGE)
    ax.text(0.3, 2.45, "VLASH — no stall, future-state-aware (aligned)", fontsize=8.5, weight="bold", color=GREEN)
    ax.annotate("", (11.2, 0.5), (0.3, 0.5), arrowprops=dict(arrowstyle="->", color="black", lw=1))
    ax.text(11.2, 0.25, "time", fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "fig_concept_timeline.png"), dpi=170, bbox_inches="tight")
    plt.close()


# ---------------------------------------------------------------
# Figure B — pi0.5 architecture
# ---------------------------------------------------------------
def architecture():
    fig, ax = plt.subplots(figsize=(8.0, 4.6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 7); ax.axis("off")

    def box(x, y, w, h, color, label, fs=8):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03",
                     fc=color, ec="black", lw=0.9))
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=fs, color="black")

    def arrow(x1, y1, x2, y2):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="->",
                     mutation_scale=12, color="black", lw=1.0))

    # Inputs
    box(0.3, 5.6, 2.2, 0.9, "#d5e8f0", "2× RGB cameras\n(224×224)")
    box(0.3, 4.4, 2.2, 0.8, "#d5e8f0", "Task text\n(language)")
    box(0.3, 3.0, 2.2, 0.8, "#fde9d0", "Robot state\ns_t ∈ ℝ⁸")
    # Prefix embedder (VLM)
    box(3.2, 4.5, 2.6, 2.0, "#cfe8cf", "PaliGemma backbone\nSigLIP → tokens\n(~700 token prefix)", fs=8)
    # Suffix embedder
    box(3.2, 2.4, 2.6, 1.4, "#e6d5f0", "Suffix embedder\nnoisy actions + t + state\n(AdaRMS conditioning)", fs=7.5)
    # Joint attention / action expert
    box(6.5, 3.3, 2.9, 2.2, "#f0d5d5", "Gemma action expert\nJoint attention:\nQ from suffix; K,V from\nprefix+suffix", fs=7.5)
    # Output
    box(6.5, 1.2, 2.9, 1.3, "#d5e8f0", "Flow matching →\naction chunk A_t\n(delta joint positions)", fs=7.5)

    arrow(2.5, 6.0, 3.2, 5.7)
    arrow(2.5, 4.8, 3.2, 5.2)
    arrow(2.5, 3.4, 3.2, 3.1)
    arrow(5.8, 5.3, 6.5, 4.8)
    arrow(5.8, 3.0, 6.5, 3.8)
    arrow(7.95, 3.3, 7.95, 2.5)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "fig_concept_pi05.png"), dpi=170, bbox_inches="tight")
    plt.close()


# ---------------------------------------------------------------
# Figure C — state rollforward
# ---------------------------------------------------------------
def rollforward():
    fig, ax = plt.subplots(figsize=(8.0, 3.4))
    ax.set_xlim(0, 10); ax.set_ylim(0, 4); ax.axis("off")
    xs = [1, 3, 5, 7]
    labels = ["s_t", "s_{t+1}", "s_{t+2}", "s_{t+Δ}"]
    for i, (x, lab) in enumerate(zip(xs, labels)):
        c = GREEN if (i == 0 or i == len(xs) - 1) else GREY
        ax.add_patch(plt.Circle((x, 2), 0.32, fc=c, ec="black", lw=1, zorder=3))
        ax.text(x, 2, "", fontsize=1)
        ax.text(x, 1.35, lab, ha="center", fontsize=9)
    for i in range(len(xs) - 1):
        ax.add_patch(FancyArrowPatch((xs[i] + 0.34, 2), (xs[i + 1] - 0.34, 2),
                     arrowstyle="->", mutation_scale=14, color=ORANGE, lw=1.6, zorder=2))
        ax.text((xs[i] + xs[i + 1]) / 2, 2.35, f"+ a_{{t+{i}}}", ha="center", fontsize=8, color=ORANGE)
    ax.text(1, 3.1, "current state\n(known)", ha="center", fontsize=8, color=GREEN)
    ax.text(7, 3.1, "execution-time state\ns_{t+Δ}=s_t+Σ a (exact)", ha="center", fontsize=8, color=GREEN)
    ax.text(5, 0.55, "Pending delta actions are already known → future state computed by a single vector sum (zero overhead)",
            ha="center", fontsize=8.5, style="italic")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "fig_concept_rollforward.png"), dpi=170, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    timeline(); architecture(); rollforward()
    print("Concept figures written to", OUT)
    print(os.listdir(OUT))
