# Questions for the supervisor (ready to send)

> Each question pins the exact section/decision so the supervisor can answer concretely
> without re-reading the whole thesis. English = paste-ready; *(VN)* = ghi chú cho khanh.

**1. Scope of the practical part — MOST IMPORTANT.**
"My practical contribution is a Python simulation that reproduces the prediction–execution
misalignment and compares the three inference modes (Sections 2.3–3.3); Section 3.4 only
reports the VLASH paper's large-scale numbers as corroboration. Is this simulation sufficient
as the original 'IT project / own quantified data' for a first-cycle thesis, or do you require
me to additionally fine-tune and evaluate the real π0.5 model on my own hardware
(RTX 3050 6 GB, which would need QLoRA)?"
*(VN: quyết định có phải chạy fine-tune thật hay không → ảnh hưởng lớn nhất.)*

**2. Reusing the paper's tables vs similarity < 10%.**
"In Section 3.4 I reproduce Table 1 of Tang et al. (2025) as my Tab. 3, with citation. Given the
<10% similarity requirement, is reproducing the source paper's table (cited) acceptable, or
should 3.4 describe the trends in prose only, without the table?"
*(VN: nếu thầy nói bỏ bảng → mình chuyển 3.4 sang văn xuôi.)*

**3. Citation style.**
"The regulations allow either footnotes or numbered references. I use the numbered IEEE style
[n] throughout. Do you confirm this style is acceptable?"

**4. Title-page wording (page 1).**
"My title page reads 'Faculty of Information Technology, Field of Study: Information Technology'.
The regulation template shows 'Faculty of Applied Computer Science, Field: Computer Science'.
Which exact faculty/field wording should appear on my title page?"

**5. GenAI declaration (Section 2.4 / statement form).**
"I used a GenAI assistant to scaffold the simulation code and to help draft and format the text.
To what extent is GenAI use permitted, and where exactly should I declare it — in the
methodology (Section 2.4), as a footnote, or in the Virtual University statement form?"

**6. Target length & which part to expand.**
"The current draft is 25 pages (excluding appendices). Do you expect closer to 30, and if so
would you prefer I deepen the experimental study (more simulation ablations in Chapter 3)
or the literature review (Chapter 1)?"
*(VN: câu trả lời quyết định mình mở rộng Ch3 hay Ch1.)*

---

## Khi có câu trả lời → hướng mở rộng tương ứng (đã chuẩn bị sẵn để làm nhanh)

| Trả lời của thầy | Mình sẽ làm |
|---|---|
| Q1: cần chạy thật | Hướng dẫn setup QLoRA fine-tune trên RTX 3050 từng bước |
| Q1: simulation là đủ | Mở rộng simulation: action quantization (q=2/3) + ablation + thống kê (~3 trang) |
| Q6: ưu tiên Ch3 | Thêm thí nghiệm/biểu đồ vào Chương 3 |
| Q6: ưu tiên Ch1 | Thêm bảng so sánh họ VLA + bảng so sánh phương pháp async (~2 trang) |
| Q2: bỏ bảng paper | Chuyển 3.4 sang văn xuôi, giảm similarity |
| Q4 | Sửa tên Khoa ở trang bìa |
| Q5 | Chèn đúng câu khai báo GenAI vào chỗ thầy chỉ |
