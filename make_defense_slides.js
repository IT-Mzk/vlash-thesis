// Defense slides — "Real-Time VLA Inference for Reactive Robotics" (VLASH thesis)
// Design: Midnight Executive (navy 1E2761 / ice CADCFC / white), 16:9, 10 slides.
// Method colors follow the thesis figures: Sync 2C7FB8, Naive D95F0E, VLASH 31A354.
const pptxgen = require("pptxgenjs");

const V = __dirname; // portable: resolves to this repo folder on any machine
const SIM = V + "/simulation/results";
const FIG = V + "/figures";

const NAVY = "1E2761", ICE = "CADCFC", WHITE = "FFFFFF";
const INK = "1A1A2E", MUT = "5A6478", PANEL = "F4F7FC";
const CSYNC = "2C7FB8", CNAIVE = "D95F0E", CVLASH = "31A354";

let p = new pptxgen();
p.layout = "LAYOUT_16x9";
p.author = "Duy Khanh Mac";
p.title = "Real-Time VLA Inference for Reactive Robotics";

// ---------- helpers ----------
function content(num, title, kicker) {
  const s = p.addSlide();
  s.background = { color: WHITE };
  // left motif bar
  s.addShape(p.shapes.RECTANGLE, { x: 0, y: 0, w: 0.14, h: 5.625, fill: { color: NAVY } });
  if (kicker) s.addText(kicker.toUpperCase(), { x: 0.45, y: 0.22, w: 8.8, h: 0.3, fontFace: "Calibri", fontSize: 11, color: MUT, charSpacing: 3, bold: true });
  s.addText(title, { x: 0.42, y: 0.46, w: 9.1, h: 0.62, fontFace: "Georgia", fontSize: 27, color: NAVY, bold: true });
  s.addText(String(num).padStart(2, "0"), { x: 9.35, y: 5.22, w: 0.5, h: 0.3, fontFace: "Calibri", fontSize: 10, color: MUT, align: "right" });
  s.addText("VLASH — Diploma thesis defense · UITM Rzeszow 2026", { x: 0.45, y: 5.22, w: 6.5, h: 0.3, fontFace: "Calibri", fontSize: 9, color: MUT });
  return s;
}
const card = (s, o) => s.addShape(p.shapes.ROUNDED_RECTANGLE, Object.assign({ rectRadius: 0.06, line: { color: "E1E7F2", width: 1 }, fill: { color: PANEL }, shadow: { type: "outer", color: "1E2761", blur: 5, offset: 2, angle: 90, opacity: 0.10 } }, o));

// =================================================== 1 · TITLE
{
  const s = p.addSlide();
  s.background = { color: NAVY };
  s.addShape(p.shapes.RECTANGLE, { x: 0, y: 3.62, w: 10, h: 0.025, fill: { color: ICE } });
  s.addText("DIPLOMA THESIS AT FIRST-CYCLE STUDIES", { x: 0.7, y: 0.75, w: 8.6, h: 0.32, align: "center", fontFace: "Calibri", fontSize: 13, color: ICE, charSpacing: 4, bold: true });
  s.addText("Real-Time Vision-Language-Action (VLA)\nInference for Reactive Robotics", { x: 0.5, y: 1.4, w: 9.0, h: 1.4, align: "center", fontFace: "Georgia", fontSize: 27, color: WHITE, bold: true });
  s.addText("A study of VLASH: future-state-aware asynchronous inference", { x: 0.7, y: 2.95, w: 8.6, h: 0.4, align: "center", fontFace: "Calibri", fontSize: 16, color: ICE, italic: true });
  s.addText([
    { text: "Duy Khanh Mac", options: { bold: true, breakLine: true, color: WHITE } },
    { text: "Record book no. 72850", options: { breakLine: true, color: ICE } },
    { text: "Supervisor: prof. WSIIZ dr inż. Atsuo Murata", options: { color: ICE } },
  ], { x: 0.7, y: 3.85, w: 8.6, h: 1.0, align: "center", fontFace: "Calibri", fontSize: 14 });
  s.addText("University of Information Technology and Management in Rzeszow · 2026", { x: 0.7, y: 5.05, w: 8.6, h: 0.3, align: "center", fontFace: "Calibri", fontSize: 11, color: ICE });
  s.addNotes("Good morning. I will present my diploma thesis on real-time inference for Vision-Language-Action models, based on the VLASH method. The presentation takes about 10 minutes: the problem, the method, my own simulation study, and conclusions.");
}

// =================================================== 2 · PROBLEM
{
  const s = content(2, "The problem: robots that stop to think", "Motivation");
  s.addText([
    { text: "VLA models turn camera images + a language command into robot actions, emitted as short ", options: { breakLine: false } },
    { text: "action chunks", options: { bold: true } },
    { text: ".", options: { breakLine: true } },
  ], { x: 0.45, y: 1.2, w: 4.35, h: 0.85, fontFace: "Calibri", fontSize: 14, color: INK });
  card(s, { x: 0.45, y: 2.1, w: 2.1, h: 1.25 });
  s.addText("103 ms", { x: 0.45, y: 2.22, w: 2.1, h: 0.5, align: "center", fontFace: "Georgia", fontSize: 30, color: NAVY, bold: true });
  s.addText("per π0.5 inference\n(RTX 4090)", { x: 0.45, y: 2.78, w: 2.1, h: 0.5, align: "center", fontFace: "Calibri", fontSize: 10.5, color: MUT });
  card(s, { x: 2.7, y: 2.1, w: 2.1, h: 1.25 });
  s.addText("1–4", { x: 2.7, y: 2.22, w: 2.1, h: 0.5, align: "center", fontFace: "Georgia", fontSize: 30, color: NAVY, bold: true });
  s.addText("control steps pass\nwhile the model thinks", { x: 2.7, y: 2.78, w: 2.1, h: 0.5, align: "center", fontFace: "Calibri", fontSize: 10.5, color: MUT });
  s.addText([
    { text: "Synchronous: ", options: { bold: true, color: CSYNC } },
    { text: "robot freezes every query → jerky “stop–run–stop” motion.", options: { breakLine: true } },
    { text: "Naive asynchronous: ", options: { bold: true, color: CNAIVE } },
    { text: "robot keeps moving, but the plan is made for a state the robot has already left → ", options: { breakLine: false } },
    { text: "prediction–execution misalignment ε.", options: { bold: true } },
  ], { x: 0.45, y: 3.55, w: 4.35, h: 1.55, fontFace: "Calibri", fontSize: 13, color: INK, paraSpaceAfter: 8 });
  s.addImage({ path: FIG + "/fig_concept_timeline.png", x: 5.05, y: 1.35, w: 4.6, h: 2.27 });
  s.addText("Three inference paradigms (thesis Fig. 2, own work)", { x: 5.05, y: 3.68, w: 4.6, h: 0.3, align: "center", fontFace: "Calibri", fontSize: 10, color: MUT, italic: true });
  s.addNotes("VLA models are accurate but slow: about 100 ms per inference even on a strong GPU. Synchronous execution freezes the robot at every query. Naive asynchronous execution keeps the robot moving but plans from a stale state, creating the misalignment epsilon. That misalignment is the core problem of the thesis.");
}

// =================================================== 3 · METHOD
{
  const s = content(3, "VLASH: condition on the future state", "Method under study");
  s.addImage({ path: FIG + "/fig_concept_rollforward.png", x: 0.45, y: 1.15, w: 5.3, h: 2.24 });
  s.addText("State rollforward (thesis Fig. 3, own work)", { x: 0.45, y: 3.42, w: 5.3, h: 0.28, align: "center", fontFace: "Calibri", fontSize: 10, color: MUT, italic: true });
  card(s, { x: 0.45, y: 3.85, w: 5.3, h: 0.85, fill: { color: NAVY } });
  s.addText("s(t+Δ)  =  s(t) + a(t) + a(t+1) + … + a(t+Δ−1)", { x: 0.45, y: 3.85, w: 5.3, h: 0.85, align: "center", fontFace: "Georgia", fontSize: 16, color: WHITE, italic: true });
  s.addText([
    { text: "Pending actions are already known —", options: { breakLine: true } },
    { text: "the future state is one exact vector sum. Zero overhead.", options: { bold: true, breakLine: true } },
  ], { x: 6.0, y: 1.15, w: 3.65, h: 0.9, fontFace: "Calibri", fontSize: 13.5, color: INK });
  const items = [
    ["1", "State rollforward", "at inference: condition the policy on s(t+Δ)"],
    ["2", "Temporal-offset augmentation", "at training: random shifts δ teach the model to use the state"],
    ["3", "Shared-observation pass", "encode the observation once for all offsets → 3.26× faster training"],
  ];
  items.forEach((it, i) => {
    const y = 2.2 + i * 0.95;
    s.addShape(p.shapes.OVAL, { x: 6.0, y: y, w: 0.42, h: 0.42, fill: { color: NAVY } });
    s.addText(it[0], { x: 6.0, y: y, w: 0.42, h: 0.42, align: "center", fontFace: "Calibri", fontSize: 15, color: WHITE, bold: true });
    s.addText([
      { text: it[1], options: { bold: true, breakLine: true, color: NAVY } },
      { text: it[2], options: { color: MUT } },
    ], { x: 6.55, y: y - 0.12, w: 3.15, h: 0.95, fontFace: "Calibri", fontSize: 12 });
  });
  s.addNotes("VLASH removes the misalignment at its source. Because actions are delta joint positions, the state at execution time equals the current state plus the pending deltas — an exact vector sum, computed for free. Training uses temporal-offset augmentation so the model actually reads the state, and a shared-observation pass makes that training 3.26 times faster.");
}

// =================================================== 4 · MY CONTRIBUTION
{
  const s = content(4, "My contribution: a controlled testbed", "Practical part · own work");
  s.addText([
    { text: "Goal: ", options: { bold: true, color: NAVY } },
    { text: "isolate the misalignment mechanism and quantify what rollforward buys, with everything else stripped away.", options: {} },
  ], { x: 0.45, y: 1.15, w: 4.5, h: 0.75, fontFace: "Calibri", fontSize: 13.5, color: INK });
  const rows = [
    ["Task", "2-D reaching; staircase target that jumps, then holds"],
    ["Controllers", "Sync · Naive-Async · VLASH (same planner)"],
    ["Injected delay", "Δ = 0…4 control steps"],
    ["Rigour", "50 seeded trials per setting, ±1 SD error bars"],
    ["Metrics", "misalignment ε, success rate, tracking error, jerk"],
  ];
  rows.forEach((r, i) => {
    const y = 2.0 + i * 0.62;
    s.addShape(p.shapes.RECTANGLE, { x: 0.45, y: y, w: 1.35, h: 0.52, fill: { color: NAVY } });
    s.addText(r[0], { x: 0.45, y: y, w: 1.35, h: 0.52, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 11, color: WHITE, bold: true });
    s.addShape(p.shapes.RECTANGLE, { x: 1.8, y: y, w: 3.15, h: 0.52, fill: { color: i % 2 ? PANEL : "EAF0FA" } });
    s.addText(r[1], { x: 1.88, y: y, w: 3.05, h: 0.52, valign: "middle", fontFace: "Calibri", fontSize: 11, color: INK });
  });
  s.addImage({ path: SIM + "/fig_trajectory.png", x: 5.15, y: 1.3, w: 4.5, h: 2.19 });
  s.addText("Naive overshoots each jump; VLASH settles cleanly (Fig. 8)", { x: 5.15, y: 3.55, w: 4.5, h: 0.3, align: "center", fontFace: "Calibri", fontSize: 10, color: MUT, italic: true });
  card(s, { x: 5.15, y: 4.0, w: 4.5, h: 0.85 });
  s.addText([
    { text: "Fully reproducible: ", options: { bold: true, color: NAVY } },
    { text: "one seed, CPU-only, runs in under a minute; all figures and CSVs regenerate exactly.", options: { color: INK } },
  ], { x: 5.3, y: 4.08, w: 4.2, h: 0.7, fontFace: "Calibri", fontSize: 11.5 });
  s.addNotes("My practical contribution is an original simulation testbed. It keeps only what the misalignment argument needs: delta actions, open-loop chunks, and an injected delay. The three controllers share the same planner, so any difference comes from the inference scheme alone. Everything is seeded and reproducible. The trajectory plot already shows the story: the naive controller overshoots after every target jump.");
}

// =================================================== 5 · RESULT: MECHANISM
{
  const s = content(5, "Result 1 — misalignment eliminated", "Simulation results");
  s.addImage({ path: SIM + "/fig_misalignment.png", x: 0.45, y: 1.25, w: 5.0, h: 3.33 });
  s.addText("Measured misalignment ε vs delay (Fig. 4)", { x: 0.45, y: 4.62, w: 5.0, h: 0.3, align: "center", fontFace: "Calibri", fontSize: 10, color: MUT, italic: true });
  const facts = [
    [CNAIVE, "Naive-Async", "ε grows with delay: 0.005 → 0.036 (Δ = 1 → 4)"],
    [CVLASH, "VLASH", "ε = 0 at every delay — the conditioning state lands exactly on the execution-start state"],
    [CSYNC, "Sync", "ε = 0 by construction, but pays the stall"],
  ];
  facts.forEach((f, i) => {
    const y = 1.45 + i * 1.05;
    s.addShape(p.shapes.RECTANGLE, { x: 5.75, y: y, w: 0.09, h: 0.85, fill: { color: f[0] } });
    s.addText([
      { text: f[1], options: { bold: true, color: f[0], breakLine: true } },
      { text: f[2], options: { color: INK } },
    ], { x: 5.98, y: y - 0.05, w: 3.7, h: 1.0, fontFace: "Calibri", fontSize: 12.5 });
  });
  s.addNotes("First result: the mechanism itself. Measured misalignment grows with delay for the naive controller and is exactly zero for VLASH at every delay — the central claim, confirmed quantitatively. This is the cleanest evidence that rollforward removes the error at its source rather than compensating for it afterwards.");
}

// =================================================== 6 · RESULT: ACCURACY
{
  const s = content(6, "Result 2 — near-sync accuracy, no stall", "Simulation results");
  s.addImage({ path: SIM + "/fig_success.png", x: 0.45, y: 1.25, w: 5.0, h: 3.33 });
  s.addText("Success rate vs delay, ±1 SD over 50 trials (Fig. 5)", { x: 0.45, y: 4.62, w: 5.0, h: 0.3, align: "center", fontFace: "Calibri", fontSize: 10, color: MUT, italic: true });
  s.addText("Success rate at Δ = 4", { x: 5.75, y: 1.3, w: 3.9, h: 0.35, fontFace: "Calibri", fontSize: 13, color: MUT, bold: true });
  const nums = [[CSYNC, "73.8%", "Sync (ceiling, but stalls)"], [CVLASH, "69.5%", "VLASH — asynchronous"], [CNAIVE, "35.4%", "Naive-Async — collapses"]];
  nums.forEach((n, i) => {
    const y = 1.75 + i * 0.98;
    card(s, { x: 5.75, y: y, w: 3.9, h: 0.85 });
    s.addText(n[1], { x: 5.95, y: y + 0.08, w: 1.6, h: 0.7, fontFace: "Georgia", fontSize: 27, color: n[0], bold: true });
    s.addText(n[2], { x: 7.55, y: y + 0.08, w: 2.0, h: 0.7, valign: "middle", fontFace: "Calibri", fontSize: 11.5, color: INK });
  });
  s.addText("VLASH keeps ~double the naive accuracy while never stalling; motion stays as smooth as synchronous.", { x: 5.75, y: 4.72, w: 3.9, h: 0.65, fontFace: "Calibri", fontSize: 11.5, color: MUT, italic: true });
  s.addNotes("Accuracy follows the mechanism. At the largest delay the naive baseline collapses to 35 percent while VLASH holds 69.5 — about double — and stays within four points of the synchronous ceiling. Jerk measurements show VLASH is also as smooth as synchronous control. The remaining gap to sync comes from the stale visual observation, which rollforward does not fix; I return to that in the limitations.");
}

// =================================================== 7 · RESULT: ROBUSTNESS
{
  const s = content(7, "Result 3 — dynamics widen the gap", "Simulation results");
  s.addImage({ path: SIM + "/fig_robustness.png", x: 0.45, y: 1.25, w: 5.0, h: 3.22 });
  s.addText("Success vs target jump magnitude at Δ = 3 (Fig. 9)", { x: 0.45, y: 4.52, w: 5.0, h: 0.3, align: "center", fontFace: "Calibri", fontSize: 10, color: MUT, italic: true });
  card(s, { x: 5.75, y: 1.4, w: 3.9, h: 1.5 });
  s.addText([
    { text: "VLASH lead over Naive-Async", options: { color: MUT, fontSize: 11.5, breakLine: true } },
    { text: "+4.7 → +30.4 pts", options: { color: NAVY, fontSize: 24, bold: true, breakLine: true } },
    { text: "as jump magnitude grows 0.10 → 0.40", options: { color: MUT, fontSize: 11 } },
  ], { x: 5.95, y: 1.52, w: 3.5, h: 1.3, fontFace: "Calibri" });
  s.addText([
    { text: "Faster scene motion during inference → larger misalignment → naive collapses (71% → 40%).", options: { breakLine: true } },
    { text: "VLASH stays within a few points of the synchronous ceiling across the whole range.", options: { breakLine: true } },
    { text: "Mirrors the paper's Kinetix finding: VLASH helps most on fast, reactive tasks.", options: { italic: true, color: MUT } },
  ], { x: 5.75, y: 3.1, w: 3.9, h: 1.9, fontFace: "Calibri", fontSize: 12.5, color: INK, paraSpaceAfter: 8 });
  s.addNotes("Third result: robustness. Sweeping how far the target jumps makes the environment more dynamic. The naive controller falls from 71 to 40 percent success, while VLASH tracks the synchronous ceiling; the lead widens from about 5 to about 30 points. This mirrors, at small scale, the paper's Kinetix result — the method matters most exactly where reactivity matters most.");
}

// =================================================== 8 · RESULT: ASSUMPTIONS
{
  const s = content(8, "Result 4 — stress-testing assumptions", "Simulation results · new experiments");
  s.addImage({ path: SIM + "/fig_noise.png", x: 0.45, y: 1.25, w: 4.34, h: 2.8 });
  s.addImage({ path: SIM + "/fig_mismatch.png", x: 5.15, y: 1.25, w: 4.34, h: 2.8 });
  s.addText("Assumption 1: exact actuation (Fig. 10)", { x: 0.45, y: 4.08, w: 4.5, h: 0.26, align: "center", fontFace: "Calibri", fontSize: 10.5, color: MUT, italic: true });
  s.addText("Assumption 2: known delay Δ (Fig. 11)", { x: 5.15, y: 4.08, w: 4.5, h: 0.26, align: "center", fontFace: "Calibri", fontSize: 10.5, color: MUT, italic: true });
  card(s, { x: 0.45, y: 4.42, w: 4.5, h: 0.68 });
  s.addText([
    { text: "Margin survives noise up to ~10% of the actuator step; ", options: {} },
    { text: "fails only where every scheme fails.", options: { bold: true } },
  ], { x: 0.6, y: 4.46, w: 4.2, h: 0.6, valign: "middle", fontFace: "Calibri", fontSize: 11, color: INK });
  card(s, { x: 5.15, y: 4.42, w: 4.5, h: 0.68 });
  s.addText([
    { text: "±1 step of delay error costs ~1 point; ", options: {} },
    { text: "a moving average of latency is enough.", options: { bold: true } },
  ], { x: 5.3, y: 4.46, w: 4.2, h: 0.6, valign: "middle", fontFace: "Calibri", fontSize: 11, color: INK });
  s.addNotes("Rollforward makes two assumptions the paper does not test: actions execute exactly, and the delay is known. I designed two experiments to stress both. Left: with Gaussian actuation noise the VLASH margin survives up to about a tenth of the actuator step, and disappears only when noise dominates every controller including synchronous. Right: misestimating the delay by one step costs about one point of success; even two steps still beats naive by a wide margin. Neither assumption is fragile — the method is genuinely plug-and-play.");
}

// =================================================== 9 · CORROBORATION + LIMITS
{
  const s = content(9, "Full scale agrees — with honest limits", "Corroboration & limitations");
  const stats = [
    ["97.2%", "LIBERO avg SR at Δ = 1\n(sync baseline 96.8%)"],
    ["+30.5 pts", "over naive async on\nfast-physics Kinetix (Δ = 4)"],
    ["94%", "best avg score on 3 real-robot\ntasks, 1.12× faster than sync"],
    ["14.9×", "cut in max reaction latency\n(536 → 36 ms, RTX 4090)"],
  ];
  stats.forEach((t, i) => {
    const x = 0.45 + (i % 2) * 2.42, y = 1.3 + Math.floor(i / 2) * 1.62;
    card(s, { x: x, y: y, w: 2.28, h: 1.45 });
    s.addText(t[0], { x: x, y: y + 0.12, w: 2.28, h: 0.55, align: "center", fontFace: "Georgia", fontSize: 23, color: NAVY, bold: true });
    s.addText(t[1], { x: x + 0.08, y: y + 0.7, w: 2.12, h: 0.7, align: "center", fontFace: "Calibri", fontSize: 9.5, color: MUT });
  });
  s.addText("Reported by Tang et al. (2025) for π0.5 [1]", { x: 0.45, y: 4.62, w: 4.7, h: 0.3, align: "center", fontFace: "Calibri", fontSize: 10, color: MUT, italic: true });
  s.addText("Limitations — stated plainly", { x: 5.55, y: 1.3, w: 4.1, h: 0.4, fontFace: "Calibri", fontSize: 14, color: NAVY, bold: true });
  s.addText([
    { text: "Stale perception: ", options: { bold: true } },
    { text: "rollforward fixes the robot state, not the visual scene → residual gap to sync in both my testbed and the paper.", options: { breakLine: true } },
    { text: "Kinematic abstraction: ", options: { bold: true } },
    { text: "my testbed has no contact dynamics or real perception; it validates the mechanism, not absolute success rates.", options: { breakLine: true } },
    { text: "Delta actions only: ", options: { bold: true } },
    { text: "exact rollforward needs additive actions; absolute action spaces would need kinematics.", options: {} },
  ], { x: 5.55, y: 1.75, w: 4.1, h: 3.3, valign: "top", fontFace: "Calibri", fontSize: 12, color: INK, paraSpaceAfter: 10 });
  s.addNotes("My small-scale findings agree with the published full-scale results on every qualitative point: near-synchronous accuracy with real speed-ups, the largest gains on the most dynamic benchmark, and large reaction-latency cuts. I state the limitations plainly: rollforward does not fix the stale image, my testbed is a kinematic abstraction, and the exactness of rollforward is a property of delta actions.");
}

// =================================================== 10 · CONCLUSION
{
  const s = p.addSlide();
  s.background = { color: NAVY };
  s.addShape(p.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: ICE } });
  s.addText("CONCLUSIONS", { x: 0.7, y: 0.45, w: 8.6, h: 0.35, fontFace: "Calibri", fontSize: 13, color: ICE, charSpacing: 4, bold: true });
  s.addText([
    { text: "Misalignment, not model speed, is the real obstacle — ", options: { color: WHITE, breakLine: true } },
    { text: "and a vector sum removes it.", options: { color: ICE, breakLine: false } },
  ], { x: 0.7, y: 0.85, w: 8.6, h: 0.95, fontFace: "Georgia", fontSize: 21, bold: true });
  const concl = [
    "Analysed the prediction–execution misalignment of asynchronous VLA inference and the VLASH remedy.",
    "Built an original, reproducible testbed: ε → 0, ~2× naive accuracy at Δ = 4, margin widening with task dynamics.",
    "Contributed two new assumption stress-tests: robust to actuation noise (≤10% step) and to delay misestimation (±1 step ≈ 1 pt).",
  ];
  concl.forEach((c, i) => {
    s.addText([{ text: c, options: { bullet: true } }], { x: 0.9, y: 1.95 + i * 0.62, w: 8.4, h: 0.6, fontFace: "Calibri", fontSize: 13.5, color: WHITE });
  });
  s.addText("FUTURE WORK", { x: 0.7, y: 3.95, w: 8.6, h: 0.3, fontFace: "Calibri", fontSize: 11, color: ICE, charSpacing: 4, bold: true });
  s.addText("Visual-observation rollforward (close the residual gap) · transfer to GR00T / OpenVLA · QLoRA fine-tune of π0.5 on my RTX 3050 (6 GB) following the plan in Section 4.1", { x: 0.7, y: 4.28, w: 8.6, h: 0.65, fontFace: "Calibri", fontSize: 12.5, color: ICE });
  s.addText("Thank you — I welcome your questions.", { x: 0.7, y: 5.05, w: 8.6, h: 0.4, align: "center", fontFace: "Georgia", fontSize: 15, color: WHITE, italic: true });
  s.addNotes("To conclude: the thesis showed that the obstacle to real-time VLA control is not raw model speed but the misalignment asynchrony creates, and that a zero-cost vector sum removes it. My testbed quantified this reproducibly, and my two new stress-tests show the method's assumptions are not fragile. Future work: predicting the visual scene, testing transfer to other architectures, and a real QLoRA fine-tune on my own GPU. Thank you, I am happy to take questions.");
}

p.writeFile({ fileName: V + "/Defense_Slides_VLASH.pptx" }).then(() => console.log("saved 10 slides"));
