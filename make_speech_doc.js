// Defense speech script (7 minutes) — Word document
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        HeadingLevel, AlignmentType, LevelFormat, BorderStyle, WidthType,
        ShadingType, PageNumber, Footer } = require("docx");
const fs = require("fs");

const NAVY = "1E2761", GRAY = "6B7280", TEAL = "0E7490", INK = "1F2937";
const W = 9026; // A4, 1" margins

// ---- run parser: **bold**, «optional (gray italic)» ----
function runs(text, base = {}) {
  const out = [];
  text.split("«").forEach((chunk, i) => {
    if (i === 0) { emit(chunk, false); return; }
    const [opt, rest] = chunk.split("»");
    emit(opt, true); if (rest) emit(rest, false);
  });
  function emit(t, optional) {
    t.split("**").forEach((seg, j) => {
      if (!seg) return;
      out.push(new TextRun(Object.assign({
        text: seg, bold: j % 2 === 1,
        italics: optional, color: optional ? GRAY : (base.color || INK),
        font: "Calibri", size: base.size || 24,
      }, optional ? { } : {})));
    });
  }
  return out;
}
const scriptPara = (t) => new Paragraph({ alignment: AlignmentType.JUSTIFIED,
  spacing: { after: 120, line: 300 }, children: runs(t) });
const notePara = (t) => new Paragraph({ numbering: { reference: "bullets", level: 0 },
  spacing: { after: 40 }, children: [new TextRun({ text: t, font: "Calibri", size: 21, color: TEAL })] });
const label = (t) => new Paragraph({ spacing: { before: 60, after: 60 },
  children: [new TextRun({ text: t, font: "Calibri", size: 21, bold: true, color: TEAL })] });

// ---- table helpers ----
const bd = { style: BorderStyle.SINGLE, size: 2, color: "C7CEDB" };
const borders = { top: bd, bottom: bd, left: bd, right: bd };
function cell(t, w, opts = {}) {
  return new TableCell({ borders, width: { size: w, type: WidthType.DXA },
    shading: opts.head ? { fill: "E8EDF7", type: ShadingType.CLEAR } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({ children: [new TextRun({ text: t, font: "Calibri", size: 21,
      bold: !!opts.head, color: opts.head ? NAVY : INK })] })] });
}

// ================= CONTENT =================
const SLIDES = [
  { n: 1, title: "Title slide", dur: "0:20", cum: "0:20",
    script: ["Good morning, members of the committee. My name is Duy Khanh Mac. Today I will defend my diploma thesis: **Real-Time Vision-Language-Action Inference for Reactive Robotics**. It studies VLASH, a method that lets a robot **think and move at the same time**. Let me start with the problem."],
    notes: ["Đứng thẳng, nhìn hội đồng, cười nhẹ. KHÔNG nhìn slide ở slide này.",
            "Nói chậm và rõ câu tên đề tài — đây là câu hội đồng nghe kỹ nhất.",
            "Dừng nửa giây sau “at the same time” rồi mới chuyển."] },
  { n: 2, title: "The problem", dur: "0:50", cum: "1:10",
    script: ["A VLA model takes camera images and a language command, and outputs robot actions in short chunks. The problem is speed: one inference takes about **one hundred milliseconds**, even on a strong GPU. During that time the robot moves **one to four control steps**.",
      "So we have two bad options. **Synchronous** inference: the robot freezes while the model thinks, so motion becomes stop–run–stop. Or **naive asynchronous** inference: the robot keeps moving, but the plan was made for a state the robot has already left. This error is called **prediction–execution misalignment**, epsilon. This misalignment is the core problem of my thesis."],
    notes: ["Chỉ tay vào 2 ô số lớn khi đọc “103 ms” và “1–4”.",
            "Nhấn mạnh từ “misalignment” — từ khoá của cả buổi, nói chậm: mis-ơ-LAIN-mờnt.",
            "Câu cuối là câu chốt vấn đề: hạ giọng, chậm lại."] },
  { n: 3, title: "VLASH method", dur: "0:50", cum: "2:00",
    script: ["VLASH solves it with one simple idea, shown in this equation. Robot actions are **deltas** — small position changes. The pending actions are already known, so we can compute the future state **exactly**: current state plus the sum of pending deltas. This is **state rollforward**, and it costs nothing — just a vector sum. The policy is then conditioned on the future state instead of the stale one.",
      "Two components support this. **Temporal-offset augmentation** teaches the model, during training, to actually use the state input. And the **shared-observation pass** encodes the observation once for all offsets, which makes training **3.26 times faster**."],
    notes: ["Chỉ vào công thức xanh navy khi đọc “current state plus the sum of pending deltas”.",
            "Ba thành phần bên phải: đọc theo thứ tự 1-2-3, mỗi ý dừng nửa nhịp.",
            "Số “3.26” đọc là three-point-two-six."] },
  { n: 4, title: "My testbed (own work)", dur: "0:50", cum: "2:50",
    script: ["My own contribution is a controlled simulation testbed. The goal is to **isolate the misalignment mechanism**, with everything else stripped away. The task is two-dimensional reaching with a target that jumps and then holds. Three controllers — synchronous, naive asynchronous, and VLASH — share **exactly the same planner**, so any difference comes only from the inference scheme.",
      "I inject a delay of zero to four steps and run **fifty seeded trials** per setting; everything reproduces from one seed. This plot already shows the story: after each target jump the naive controller **overshoots**, while VLASH settles cleanly."],
    notes: ["Đổi giọng tự tin hơn — từ đây là phần CỦA KHANH.",
            "Nhấn “same planner”: chặn trước câu hỏi “so sánh có công bằng không?”.",
            "Chỉ vào hình bên phải đúng lúc nói “overshoots”."] },
  { n: 5, title: "Result 1 — mechanism", dur: "0:35", cum: "3:25",
    script: ["First result: the mechanism itself. I measure the misalignment epsilon directly. For the naive controller it **grows with delay**, from 0.005 to 0.036. For VLASH it is **exactly zero at every delay** — the conditioning state lands exactly where execution starts. So rollforward does not correct the error afterwards; it **removes the error at its source**."],
    notes: ["Slide ngắn, đừng vội — 35 giây là đủ.",
            "Nhấn “exactly zero”, tay chỉ vào đường VLASH nằm phẳng dưới cùng của biểu đồ."] },
  { n: 6, title: "Result 2 — accuracy", dur: "0:45", cum: "4:10",
    script: ["And accuracy follows. At the largest delay, the synchronous ceiling is **73.8 percent** success. The naive baseline collapses to **35.4**. VLASH holds **69.5** — about **double** the naive accuracy — while never stalling. The error bars are one standard deviation over fifty trials, so this separation is stable, not a lucky seed. «Smoothness shows the same picture: VLASH moves as smoothly as synchronous control.»"],
    notes: ["Đọc 3 con số theo đúng thứ tự 3 card từ trên xuống, chỉ tay theo.",
            "Nhấn “double” — con số dễ nhớ nhất cho hội đồng.",
            "Câu xám nghiêng có thể BỎ nếu thiếu giờ."] },
  { n: 7, title: "Result 3 — robustness", dur: "0:40", cum: "4:50",
    script: ["Third result: robustness. I sweep how far the target jumps — how **dynamic** the environment is. The naive controller falls from 71 to **40 percent**; VLASH stays within a few points of the synchronous ceiling across the whole range. The lead grows from about **5 points to about 30**. The more reactive the task, the more this method matters — which mirrors the Kinetix result from the paper."],
    notes: ["Kể như câu chuyện tăng dần: càng động → naive càng sụp.",
            "Nhấn cặp số “5 → 30”, chỉ vào ô +4.7 → +30.4 pts."] },
  { n: 8, title: "Result 4 — assumption stress-tests (QUAN TRỌNG NHẤT)", dur: "1:00", cum: "5:50",
    script: ["This slide shows my **two new experiments**. They test assumptions the original paper does not examine. Rollforward assumes two things: actions execute **exactly**, and the delay is **known**.",
      "On the left, I add Gaussian noise to every executed action — noise the rollforward cannot see. The VLASH margin survives up to about **ten percent of the actuator step**, and it closes only when the noise dominates every controller, including synchronous. On the right, I let the controller misestimate the delay. A **one-step** error costs about **one point** of success; even two steps still clearly beats the naive baseline. So neither assumption is fragile — in practice, a **moving average of recent latencies is enough**."],
    notes: ["Slide đắt giá nhất — đây là đóng góp mới paper KHÔNG có. Dành trọn 1 phút.",
            "Nói chậm lại một nhịp so với các slide trước; chỉ hình trái trước, phải sau.",
            "Gaussian đọc là GAO-xi-ờn. Nếu hội đồng ghi chép ở slide này — đó là dấu hiệu tốt."] },
  { n: 9, title: "Corroboration & limitations", dur: "0:40", cum: "6:30",
    script: ["At full scale, the published results agree with my findings on every qualitative point: near-synchronous accuracy on LIBERO with real speed-ups, a gain of **over thirty points** on the fast-physics benchmark, the best score on real robots, and large cuts in reaction latency. But I state the limits plainly: rollforward fixes the robot state, **not the visual scene**, so a small gap to synchronous remains. «And my testbed is a kinematic abstraction — it validates the mechanism, not absolute success rates.»"],
    notes: ["Phần limitations: giọng bình thản, trung thực — hội đồng chấm cao sự tự phê.",
            "Không xin lỗi, không nói “unfortunately” — limitations là scope, không phải lỗi.",
            "Câu xám nghiêng có thể BỎ nếu thiếu giờ."] },
  { n: 10, title: "Conclusion", dur: "0:35", cum: "7:05",
    script: ["To conclude. The real obstacle to real-time VLA control is not model speed — it is the **misalignment** that asynchrony creates, and a **zero-cost vector sum removes it**. My thesis analysed this mechanism, quantified it in an original, reproducible testbed, and contributed two new stress-tests showing the method is robust to actuation noise and to delay misestimation. Future work includes predicting the visual scene and a real QLoRA fine-tune on my own GPU. **Thank you — I welcome your questions.**"],
    notes: ["Kết mạnh và chậm. Câu cuối NHÌN HỘI ĐỒNG, không nhìn slide.",
            "Không nói “that’s all” hay “xong rồi ạ” — dừng ở “questions” rồi im, chờ.",
            "Nếu quá giờ ở slide 8, bỏ 2 câu xám ở slide 6 và 9 là về đúng 7:00."] },
];

const PRON = [
  ["misalignment", "mis-ơ-LAIN-mờnt (trọng âm LAIN)"],
  ["asynchronous", "ây-SIN-krơ-nớs (trọng âm SIN)"],
  ["synchronous", "SIN-krơ-nớs"],
  ["rollforward", "RÔL-pho-uốt"],
  ["epsilon (ε)", "EP-xi-lon"],
  ["Gaussian", "GAO-xi-ờn"],
  ["actuator / actuation", "AK-chu-ây-tơ / ak-chu-Ê-sờn"],
  ["latency", "LÊY-tờn-xi"],
  ["kinematic", "ki-nơ-MA-tik"],
  ["LIBERO / Kinetix", "li-BE-rô / ki-NE-tiks"],
];

// ================= DOCUMENT =================
const children = [];
children.push(new Paragraph({ heading: HeadingLevel.HEADING_1,
  children: [new TextRun("Kịch bản nói 7 phút — Bảo vệ thesis VLASH")] }));
children.push(new Paragraph({ spacing: { after: 200 },
  children: [new TextRun({ text: "Khớp với Defense_Slides_VLASH.pptx (10 slide, tiếng Anh) · ~975 từ · tốc độ chuẩn ~140 từ/phút · tổng ≈ 7:00", font: "Calibri", size: 21, color: GRAY, italics: true })] }));

children.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("Mẹo chung trước khi tập")] }));
[
  "In trang này ra, tập nói 3 lần có bấm giờ. Lần 1 đọc nguyên văn; lần 2 chỉ nhìn từ khoá in đậm; lần 3 không cầm giấy.",
  "Chữ in đậm = từ cần NHẤN GIỌNG. Câu xám nghiêng = có thể bỏ nếu thiếu giờ (tổng tiết kiệm ~20 giây).",
  "Mỗi lần chuyển slide: im lặng 1 giây, nhìn slide mới, rồi mới nói. Khoảng lặng này đã tính trong 7 phút.",
  "Nói chậm hơn mức khanh nghĩ là chậm — người nghe cần thời gian đọc biểu đồ.",
  "Nếu quên câu: nhìn từ khoá trên slide, diễn đạt lại theo ý mình. Hội đồng chấm sự hiểu, không chấm thuộc lòng.",
].forEach(t => children.push(notePara(t)));

children.push(new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 200 }, children: [new TextRun("Bảng phân bổ thời gian")] }));
children.push(new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: [800, 4826, 1700, 1700],
  rows: [ new TableRow({ children: [cell("Slide", 800, {head:1}), cell("Nội dung", 4826, {head:1}), cell("Thời lượng", 1700, {head:1}), cell("Cộng dồn", 1700, {head:1})] }),
    ...SLIDES.map(s => new TableRow({ children: [cell(String(s.n), 800), cell(s.title, 4826), cell(s.dur, 1700), cell(s.cum, 1700)] })) ] }));

children.push(new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 200 }, children: [new TextRun("Cách đọc các từ khó (gần đúng)")] }));
children.push(new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: [3200, 5826],
  rows: [ new TableRow({ children: [cell("Từ", 3200, {head:1}), cell("Cách đọc", 5826, {head:1})] }),
    ...PRON.map(r => new TableRow({ children: [cell(r[0], 3200), cell(r[1], 5826)] })) ] }));

SLIDES.forEach(s => {
  children.push(new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 280 },
    children: [new TextRun(`Slide ${s.n} — ${s.title}`),
      new TextRun({ text: `   (${s.dur} · cộng dồn ${s.cum})`, color: GRAY, size: 22, bold: false })] }));
  children.push(label("Nói (tiếng Anh):"));
  s.script.forEach(t => children.push(scriptPara(t)));
  children.push(label("Cách nói & cử chỉ:"));
  s.notes.forEach(t => children.push(notePara(t)));
});

const doc = new Document({
  styles: { default: { document: { run: { font: "Calibri", size: 24 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 34, bold: true, font: "Calibri", color: NAVY },
        paragraph: { spacing: { before: 0, after: 120 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Calibri", color: NAVY },
        paragraph: { spacing: { before: 160, after: 100 }, outlineLevel: 1 } },
    ] },
  numbering: { config: [ { reference: "bullets",
      levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] } ] },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 },
      margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], font: "Calibri", size: 20, color: GRAY })] })] }) },
    children }],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync(__dirname + "/Defense_Speech_7min.docx", b); console.log("saved speech doc"); });
