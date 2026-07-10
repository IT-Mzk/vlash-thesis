# Thesis VLASH — Roadmap hoàn thiện & Báo cáo lỗi chi tiết

> Tài liệu nội bộ cho khanh. Đối chiếu: `update3_formatted (2).docx` (thesis đang làm) ↔ `thesis_mau.docx` (mẫu supervisor) ↔ `cach_viet_thesis.docx` (rule trường) ↔ `vla1.md` (paper gốc VLASH).
> Loại thesis: **First-cycle / IT Project (Computer Science – Programming), UITM Rzeszów**.

---

## 0. Tiêu chí chấm điểm (trích rule – để mọi việc bám vào đây)

Thesis được chấm bởi **supervisor + 1 reviewer**, điểm cuối = trung bình cộng. Phiếu đánh giá gồm 6 mục, trong đó **2 mục có dấu (*) là "critical element"** — nếu bị điểm âm ở 1 trong số đó thì **toàn bộ thesis không thể đạt điểm dương**:

| # | Tiêu chí | Critical? |
|---|----------|-----------|
| 1 | Nội dung có khớp với tên đề tài không | |
| 2 | **Đánh giá tính THỰC HÀNH (practical nature) của thesis** | ⭐ Critical |
| 3 | **Đánh giá NỘI DUNG chuyên môn (substantive)** | ⭐ Critical |
| 4 | Cấu trúc, kỹ thuật viết, văn phong, ngữ pháp | |
| 5 | Lựa chọn & sử dụng nguồn tài liệu | |
| 6 | Đánh giá tổng kết | |

Ràng buộc khác: IT thesis **≥ 20 trang**; phải là **"non-trivial practical IT undertaking, original whole"**, **"cannot be merely descriptive"**, dựa trên **"quantified real data obtained by the author"**; **Similarity Score > 30% → bị gắn cờ**; **bắt buộc khai báo dùng GenAI** ở mức supervisor cho phép; nộp file **PDF**.

---

## 1. Ba vấn đề CHIẾN LƯỢC (xử lý trước khi sửa lặt vặt)

### 1.1 ⭐ Thiếu "công trình của chính mình" (đụng 2 critical element)
Chương 3 mở đầu: *"All results reported in this chapter are drawn from Tang et al."* → hiện tại thesis = **giải thích lại paper người khác**, chưa có đóng góp gốc. Đây là rủi ro lớn nhất vì đụng trực tiếp tiêu chí **#2 (practical nature)** và **#3 (substantive)** — cả hai đều critical.
→ **Quyết định cần chốt (mục 4 bên dưới).** Khuyến nghị: tự build simulation nhẹ + tự chạy → tạo số liệu của chính mình.

### 1.2 Số liệu Chương 3 mâu thuẫn với paper gốc — ĐÃ CHỐT: sửa cho khớp paper
- **Sai nghiêm trọng (đảo ngược phát hiện):** Paper Table 1 → **Sync no-state = 97.7% > Sync có state = 96.8%** (VLA *under-utilize* state, đây là lý do cần temporal-offset augmentation). Thesis ghi ngược: **91.6% < 95.9%** + diễn giải sai ("state input carries meaningful information... validating the premise"). Reviewer đọc paper sẽ bắt ngay.
- **Số per-column bịa:** trung bình khớp paper nhưng từng cột Spatial/Object/Goal/LIBERO-10 không khớp (paper VLASH Δ=1 = 98.8/99.2/96.7/94.4; thesis ghi 97.4/97.8/96.1/97.6).
- **Sync trung bình:** thesis 95.9% vs paper 96.8%.
- **Naive Async trên LIBERO** (75.1%, 83.2%...) **không có trong Table 1 của paper** → cần nguồn hoặc bỏ/ghi rõ là ước lượng.
- **Lỗi số học:** reaction latency 530/36 = **14.7×**, không phải 14.9×.
- **Mâu thuẫn nội bộ:** mục 2.6 [283] ghi *"2.67× additional throughput"* nhưng chỗ khác ghi **2.03×**.
- **Cần kiểm chứng:** SmolVLA Sync 78.96% / VLASH 79.06% — đối chiếu lại số thật của paper.

### 1.3 Citations & bibliography còn ở dạng nháp
- **~40+ placeholder `[cite: ...]`** rải khắp Ch1–Ch3, chưa chuyển sang số `[n]`.
- **Tác giả reference [1] SAI:** thesis ghi VLASH = *"Y. Tang, J. Guo, Z. Liu, and S. Levine"* — nhưng tác giả thật là **Jiaming Tang, Yufei Sun, Zhuoyang Zhang, ... Song Han et al. (MIT/NVIDIA)**. J. Guo và S. Levine **không** nằm trong nhóm tác giả.
- **Reference [14] SAI tên:** *"NVIDIA, 'Groot: Learning to Move Like Groot'"* — sai (đúng là **GR00T N1**, NVIDIA 2025).
- Thiếu thông tin đầy đủ cho: SmolVLA, RTC (Black 2025), A2C2, PaliGemma, OpenVLA, Gemini Robotics, MuJoCo, AdaRMS/RMSNorm.
- Rule cho phép 2 cách footnote (supervisor chọn); thesis đang dùng kiểu số `[n]` theo thứ tự xuất hiện → cần **xác nhận với supervisor** thứ tự bibliography (alphabet theo họ tác giả vs theo thứ tự xuất hiện — rule có chỗ ghi cả hai).

---

## 2. Lỗi cấu trúc (so với thesis mẫu & rule)

| Vấn đề | Mẫu / Rule yêu cầu | Thesis hiện tại |
|---|---|---|
| Chương riêng cho **methodology của CHÍNH mình** + **kết quả của chính mình** | Mẫu: Ch3 = Methodology (dataset, preprocessing, tools, metrics), Ch4 = Results & Analysis (thí nghiệm riêng) | Ch2 mô tả method của *paper*; Ch3 báo cáo số *paper*. Không có setup/tool/kết quả riêng. |
| Mục **"Tools and Libraries"** (môi trường, thư viện thật) | Mẫu có hẳn 3.6 Tools and Libraries | Chưa có. Engineering rule đòi "current IT tools, libraries, simulators". |
| **Heading levels** nhất quán | Heading 1→2→3 liên tục | Tiểu mục 2.5.x và 3.3.x dùng **Heading 4** (nhảy cóc, bỏ Heading 3) → TOC tự động sẽ lệch. |
| **List of Figures / List of Tables** | Có nội dung, auto-generate | **Rỗng** ("No table of figures entries found"). |
| **Hình minh hoạ** | Mẫu có nhiều Fig. | Thesis nhắc "Figure 1" nhiều lần nhưng **không có hình nào**. |
| **Bảng trong thân bài** | Bảng có số liệu ngay tại chỗ trích dẫn | Table 1/2/3 trong thân bài **rỗng**; số liệu nằm rời ở 4 bảng cuối file. |
| **Abstract / Summary** | Mẫu có trang Summary cuối | Trang "Summary" **trống**. (Kiểm tra có cần Streszczenie tiếng Ba Lan không.) |
| **Khai báo GenAI** | Rule bắt buộc (mục methodology + statement) | Chưa có. |
| **Conclusion so sánh với giải pháp hiện có** | Rule: "compared with existing solutions, positive & negative aspects" | Có đối chiếu RTC/A2C2 nhưng nên nêu rõ ưu/nhược **giải pháp của chính mình**. |

---

## 3. Lỗi ngữ pháp / chính tả / kỹ thuật viết (mẫu, sẽ rà full sau)

- **[48]** "VLA is **an** artificial intelligence **models**" → "VLA models **are a class of** artificial intelligence models" (sai số ít/nhiều).
- **[47]** chứa **ký tự ẩn / double-space** ("is ⟨zero-width⟩ this thesis") → cần làm sạch toàn văn (rule: *"Do not insert more than one space between words"*).
- **[52], [53]...** dùng dấu **' '** kiểu cong không nhất quán với *" "* — chuẩn hoá.
- Một số câu dài có thể tách cho dễ đọc; thuật ngữ (e.g., π0.5, AdaRMS, LoRA) cần in nghiêng/định dạng nhất quán lần xuất hiện đầu.
- Rule format chữ: **Times New Roman 12pt**, heading **14pt bold** (chương) / **12pt bold** (mục), **không chấm cuối tiêu đề**, **margin 2cm**, **line spacing 1.15**, **justify 2 bên**, **TOC tự động ở trang 2**, **số trang ở footer giữa**, caption **Fig./Tab.** đánh số Ả-rập + dòng **Source:** (TNR 10pt) phía dưới object, tham chiếu hình trong text dạng **(1)**.

---

## 4. Quyết định cần khanh chốt: hướng Chương 3

| Hướng | Khớp critical element #2/#3 | Khả thi RTX 3050 6GB | Rủi ro |
|---|---|---|---|
| **A. Tự chạy fine-tune π0.5 + eval LIBERO thật** | Rất mạnh | **Thấp/khó** — π0.5 (PaliGemma-2B) + QLoRA + render MuJoCo trên 6GB rất chật, chậm, dễ không kịp deadline | Cao (có thể không chạy xong) |
| **B. ⭐ Tự build SIMULATION nhẹ (Python) đo 3 cơ chế + trích paper đúng** | **Mạnh** (có công trình + số liệu riêng, đúng mục tiêu đã ghi ở Introduction) | **Cao** — chỉ cần CPU/GPU nhẹ | Thấp |
| **C. Giữ literature-based** | **Yếu** (dễ bị "merely descriptive" → âm điểm critical) | — | Cao về điểm |

**Khuyến nghị: Hướng B (có thể kèm A như "stretch" nếu còn thời gian).**
Vì: (1) đúng mục tiêu khanh đã tự đặt ở Introduction — *"design a simple simulation system that illustrates and compares 3 inference mechanisms"*; (2) tạo **số liệu & biểu đồ của chính khanh** → thỏa critical #2 và #3; (3) khả thi trên máy yếu; (4) cho phép Conclusion *"so sánh giải pháp của mình với hiện có"* như rule đòi.

**Thiết kế simulation đề xuất (B):** mô phỏng một cánh tay/điểm reaching đơn giản với **delta-action**, tham số hoá **inference delay Δ**, hiện thực 3 controller: **sync / naive-async / rollforward (VLASH)**; đo **misalignment error ε**, **success rate**, **reaction latency**, **độ giật (jerk/smoothness)**; quét Δ = 0..4 và xuất bảng + đồ thị. Kết quả kỳ vọng tái lập đúng xu hướng paper ở quy mô nhỏ → vừa là đóng góp gốc, vừa **validate** paper.

---

## 5. Roadmap thực thi (thứ tự ưu tiên)

1. **[CHỐT HƯỚNG]** Chọn A/B/C cho Chương 3 (khuyến nghị B).
2. **Sửa data Ch3 khớp paper** (đã đồng ý) + viết lại diễn giải Sync-no-state, sửa lỗi số học & mâu thuẫn nội bộ.
3. **Bibliography**: web-search bổ sung dữ liệu thật; sửa tác giả [1], [14]; chuyển `[cite:]` → `[n]`; chốt thứ tự với supervisor.
4. **(Nếu chọn B)** Viết code simulation → chạy → thu số liệu riêng → bổ sung mục Methodology + Results của chính mình; thêm "Tools & Libraries".
5. **Vẽ hình**: timeline 3 cơ chế, kiến trúc π0.5, state rollforward, shared-observation mask, biểu đồ kết quả → nhúng + điền List of Figures/Tables.
6. **Điền bảng thân bài** (LIBERO, Kinetix, real-world, SmolVLA) đúng số paper / số riêng.
7. **Format chuẩn trường** + Abstract/Summary + khai báo GenAI + TOC + sửa Heading levels → **xuất PDF**.
8. **Rà ngữ pháp/chính tả + verify cuối** (đối chiếu số liệu, citation, công thức, format, độ dài ≥20 trang).

---

## 6. Việc khanh nên hỏi supervisor
1. Chương 3 **bắt buộc** số liệu/thí nghiệm của chính mình, hay được phép trích paper? (quyết định A/B/C)
2. Thứ tự **bibliography**: theo alphabet họ tác giả hay theo thứ tự xuất hiện `[n]`?
3. Mức được phép **dùng GenAI** (để khai báo đúng trong statement).
4. Có cần **abstract tiếng Ba Lan (Streszczenie)** không.
