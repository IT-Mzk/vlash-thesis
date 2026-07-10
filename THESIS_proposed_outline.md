# Bố cục đề xuất — tích hợp simulation thành đóng góp thực hành chính

> Mục tiêu: biến **simulation testbed của khanh** thành "practical part" (thỏa 2 critical element: *practical nature* + *substantive*), giữ kết quả paper làm **đối chứng quy mô lớn**. Bố cục này khớp đúng các objective khanh đã ghi ở Introduction ("design a simple simulation system that illustrates and compares 3 inference mechanisms" + "evaluate and discuss the results obtained from the simulation").

---

## Chương 1 — Background and Related Work  *(giữ nguyên ~90%, chỉ sửa)*
- 1.1 Robotics and Real-Time Control
- 1.2 Vision-Language Models → VLAs (π0.5)
- 1.3 Action Chunking and Inference Delay
- 1.4 Asynchronous Inference: Naive, RTC, **A2C2 (sửa lại mô tả cho đúng)**
- 1.5 Limitations of Existing Approaches / Research Gap
- 1.6 Summary

**Sửa:** đoạn A2C2 (không retrain base); toàn bộ `[cite:]` → `[n]`; thuật ngữ.

---

## Chương 2 — System Design and Methodology  *(tái cấu trúc rõ "method được nghiên cứu" ↔ "hệ thống của mình")*

- **2.1 Overview & Objectives** — nêu rõ: thesis xây một **simulation testbed** so sánh 3 cơ chế inference; phạm vi & giả định.
- **2.2 The VLASH Method (đối tượng nghiên cứu — phần lý thuyết)** — gộp gọn: state rollforward, temporal-offset augmentation, shared-observation, action quantization. *(Lấy từ 2.5 hiện tại, rút gọn.)*
- **2.3 Design of the Simulation Testbed (CỦA MÌNH — methodology)**
  - 2.3.1 Task: 2-D staircase reaching (jump-and-hold) + lý do chọn (khử confound)
  - 2.3.2 State & delta-action representation; inference-delay model Δ
  - 2.3.3 Ba controller + **Algorithm 1/2/3** (Sync / Naive-Async / VLASH-rollforward)
  - 2.3.4 Evaluation metrics: misalignment ε, success rate, tracking error, smoothness
- **2.4 Implementation (CỦA MÌNH)** — Python + NumPy + Matplotlib; tham số (K, MAX_STEP, JUMP…); seed/khả năng tái lập; **Tools and Libraries**; ánh xạ tới `vlash_simulation.py`.
- **2.5 Reference Implementation Context** — codebase VLASH thật, π0.5, LIBERO mà simulation trừu tượng hoá; cấu hình RTX 3050 6GB (QLoRA) — định hướng cho Future Work.
- **2.6 Summary**

---

## Chương 3 — Experiments and Results  *(kết quả của mình là CHÍNH, paper là đối chứng)*

- **3.1 Experimental Setup** — simulation: quét Δ=0…4, 50 trial/Δ, seed, máy chạy; + tóm tắt setup quy mô lớn của paper (để 3.4).
- **3.2 Evaluation Metrics** — định nghĩa 4 metric của mình.
- **3.3 Simulation Study Results (CỦA MÌNH — phần chính)**
  - 3.3.1 Misalignment vs delay → `fig_misalignment` (ε: Naive 0→0.036; VLASH=0)
  - 3.3.2 Success rate & tracking accuracy → `fig_success`, `fig_tracking_error`
  - 3.3.3 Motion smoothness → `fig_smoothness`
  - 3.3.4 Qualitative trajectories → `fig_trajectory`
- **3.4 Corroboration with Large-Scale VLASH Results** — **số liệu paper ĐÃ SỬA**: LIBERO (Table 1 đúng, gồm Sync-no-state = 97.7% > Sync 96.8%, diễn giải lại), Kinetix (81.7 vs 51.2), real-world, SmolVLA. Khung: "kết quả quy mô lớn xác nhận cùng xu hướng với simulation."
- **3.5 Discussion** — vì sao VLASH hiệu quả; đối chiếu kết quả mình ↔ paper; **khoảng cách dư VLASH↔Sync = visual staleness** (đúng limitation); hạn chế của abstraction; so RTC/A2C2.
- **3.6 Summary**

---

## Chương 4 — Conclusion and Future Work  *(thêm phần rubric yêu cầu)*
- **4.0 Conclusion** — nêu rõ **mức đạt mục tiêu** (rubric đòi "assess degree to which objective achieved") + **so sánh giải pháp với hiện có, ưu/nhược** (rubric đòi).
- **4.1 Future Work** — chạy fine-tune thật trên RTX 3050 (bước tiếp theo tự nhiên), visual rollforward, adaptive scheduling, learned quantization.

---

## Việc cần khanh hỏi supervisor (đã nhắc, nhắc lại):
1. Bibliography sắp theo **alphabet** hay **thứ tự xuất hiện [n]**?
2. Mức **GenAI** được phép (để khai báo đúng — mình đã chèn sẵn ghi chú trong code & README).
3. Có cần **abstract tiếng Ba Lan (Streszczenie)** không.

## Thứ tự mình sẽ làm (review giữa chừng theo yêu cầu của khanh):
- **Bước A:** Viết nội dung Ch2 mới (2.3–2.5) + Ch3 mục 3.3 (simulation) → khanh review.
- **Bước B:** Sửa số liệu paper ở 3.4 + chuyển citations [n] + sửa A2C2 ở Ch1 → khanh review.
- **Bước C:** Vẽ thêm hình khái niệm (timeline 3 cơ chế, kiến trúc π0.5, rollforward) + nhúng tất cả hình.
- **Bước D:** Format chuẩn trường + Abstract/Summary + TOC + xuất PDF → review cuối.
