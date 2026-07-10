# Lộ trình làm việc trên Windows 11 — VLASH thesis

> Dành cho khanh, làm dần theo từng giai đoạn. Giai đoạn 1–3 mất khoảng 1 buổi tối.
> Giai đoạn 5 (fine-tune GPU) chỉ làm khi supervisor yêu cầu (câu hỏi Q1).

---

## 0. Claude trên Windows có "nhớ" những gì đã làm trên MacBook không?

**Không.** Các cuộc trò chuyện Claude không đồng bộ giữa máy — mỗi máy, mỗi phiên là bộ nhớ riêng.

**Nhưng không sao**, vì toàn bộ "trí nhớ dự án" đã được ghi vào file trong folder này:

| File | Vai trò |
|---|---|
| `CLAUDE.md` | Bộ não dự án. Claude **tự đọc file này** khi khanh chọn folder trong Cowork. Mục PROJECT STATUS ở đầu tóm tắt mọi thứ đã làm. |
| `WINDOWS_SETUP_ROADMAP.md` | Chính file này — lộ trình. |
| `THESIS_supervisor_questions.md` | 6 câu hỏi chờ supervisor + kế hoạch theo từng câu trả lời. |
| `build_thesis_v2.py`, `make_defense_slides.js`, `make_speech_doc.js` | Toàn bộ nội dung thesis/slides/speech nằm TRONG script — sửa script rồi build lại là ra file mới. |

**Cách bắt đầu chat với Claude trên Windows** (câu mở đầu gợi ý):

> "Đọc CLAUDE.md (mục PROJECT STATUS) và WINDOWS_SETUP_ROADMAP.md trong folder này trước, rồi giúp tôi [việc cần làm]."

---

## Giai đoạn 1 — Cài phần mềm nền (~30 phút)

Mở **PowerShell** (không cần Admin, winget có sẵn trên Win 11) và chạy từng dòng:

```powershell
winget install Git.Git
winget install Python.Python.3.12
winget install OpenJS.NodeJS.LTS
winget install Microsoft.VisualStudioCode
```

- **Claude Desktop (Cowork):** tải tại https://claude.ai/download → đăng nhập cùng tài khoản đang dùng trên Mac.
- **Tuỳ chọn:** LibreOffice (`winget install TheDocumentFoundation.LibreOffice`) — chỉ cần nếu muốn tự convert docx→PDF bằng lệnh. Nếu máy có sẵn MS Word/PowerPoint thì không cần.

Đóng rồi mở lại PowerShell, kiểm tra:

```powershell
git --version
python --version
node --version
```

Cả 3 lệnh in ra số phiên bản là đạt.

---

## Giai đoạn 2 — Đưa project sang Windows qua GitHub (~20 phút)

**Vấn đề hiện tại:** folder `vlash` trên Mac là bản clone từ repo gốc `mit-han-lab/vlash` — khanh **không có quyền push** lên đó, và toàn bộ file thesis **chưa được commit**. Cần chuyển sang repo GitHub của riêng khanh.

### 2a. Trên GitHub (trình duyệt)
1. Vào https://github.com/new
2. Repository name: `vlash-thesis` · chọn **Private** (thesis chưa nộp, không nên public)
3. KHÔNG tick "Add a README" (repo phải rỗng) → Create repository.

### 2b. Trên MacBook (Terminal, trong folder vlash) — làm MỘT lần

```bash
# đổi tên remote gốc thành upstream (giữ lại để sau này pull update từ tác giả)
git remote rename origin upstream

# thêm repo riêng của khanh làm origin (thay <username> bằng tên GitHub của khanh)
git remote add origin https://github.com/<username>/vlash-thesis.git

# commit toàn bộ công trình (thesis, slides, speech, simulation, scripts)
git add -A
git commit -m "thesis: 32-page manuscript, defense slides, speech script, simulation with ablations"

# đẩy lên GitHub (lần đầu sẽ mở trình duyệt để đăng nhập)
git push -u origin main
```

Giải thích: `remote` là "địa chỉ" repo trên mạng; `origin` = repo chính của mình, `upstream` = repo gốc của tác giả. `add -A` gom mọi file mới, `commit` chụp lại một phiên bản, `push` đẩy lên GitHub.

> Nếu nhánh tên `master` thay vì `main` (kiểm tra bằng `git branch`), thay `main` bằng `master` trong lệnh push.

### 2c. Trên Windows (PowerShell)

```powershell
cd $HOME\Documents
git clone https://github.com/<username>/vlash-thesis.git
code vlash-thesis   # mở bằng VS Code xem thử
```

Xong: mở **Claude Desktop → Cowork → chọn folder** `Documents\vlash-thesis`. Claude sẽ tự đọc `CLAUDE.md` và hiểu toàn bộ bối cảnh.

---

## Giai đoạn 3 — Tái lập simulation trên Windows (~10 phút, KHÔNG cần GPU)

Đây là phần thực hành của thesis — chạy lại để xác nhận máy Windows cho **kết quả giống hệt**:

```powershell
cd $HOME\Documents\vlash-thesis
python -m venv .venv
.venv\Scripts\activate
pip install numpy pandas matplotlib
python simulation\vlash_simulation.py
```

**Đối chiếu kết quả** — các số in ra phải khớp thesis (mọi randomness sinh từ một seed cố định `SEED0 = 20260615`, chạy CPU thuần nên máy nào cũng ra đúng một kết quả):

| Chỉ số | Giá trị phải thấy |
|---|---|
| Success @ Δ=4 | Sync 0.738 · VLASH 0.695 · Naive 0.354 (Tab. 4) |
| Robustness jump=0.4 | Naive 0.398 · VLASH 0.702 (Tab. 5) |
| Noise σ=0.005 | Sync 0.682 · VLASH 0.601 · Naive 0.370 (Tab. 6) |
| Mismatch e=0 / e=−1 | 0.718 / 0.710 (Tab. 7) |

Khớp hết = môi trường Windows chuẩn, khanh có thể tự tin nói trước hội đồng rằng kết quả tái lập được trên máy khác.

---

## Giai đoạn 4 — Build lại thesis / slides khi cần sửa nội dung

Có 2 cách, chọn theo tình huống:

**Cách A — nhờ Claude Cowork trên Windows (khuyên dùng):** mở folder, nói ví dụ "sửa mục 3.5 của thesis thêm ý X rồi build lại". Claude đọc CLAUDE.md sẽ biết quy trình 2-pass. Sandbox của Cowork có sẵn LibreOffice nên nó tự convert PDF được.

**Cách B — tự chạy tay:**

```powershell
pip install python-docx pypdf
npm install docx pptxgenjs          # chạy trong folder repo

# thesis (quy trình 2 lượt vì mục lục cần số trang thật):
python build_thesis_v2.py           # lượt 1
# → mở Thesis_VLASH_MacDuyKhanh.docx bằng Word → File → Save as PDF (cùng tên)
python detect_pages.py              # dò số trang từ PDF → pagemap.json
python build_thesis_v2.py           # lượt 2 (TOC nhận số trang đúng)
# → xuất PDF lần cuối bằng Word

# slides / speech:
node make_defense_slides.js
node make_speech_doc.js
```

Giải thích 2 lượt: mục lục là chữ tĩnh, phải biết mỗi mục nằm trang nào; lượt 1 tạo layout, `detect_pages.py` đọc PDF ghi lại số trang, lượt 2 điền vào TOC.

---

## Giai đoạn 5 — (TUỲ CHỌN — chờ supervisor trả lời Q1) Fine-tune π0.5 thật trên RTX 3050 6GB

> Chỉ bắt đầu khi supervisor xác nhận cần "own experiment trên model thật".
> Thời gian thực tế: 1 buổi setup + nhiều giờ đến vài ngày train. Cần ~40–50GB đĩa trống.

### 5a. Nền tảng — WSL2 (bắt buộc)
`bitsandbytes` (QLoRA 4-bit) hỗ trợ Linux tốt hơn Windows nhiều, nên train trong WSL2:

```powershell
wsl --install -d Ubuntu-24.04     # PowerShell Admin, xong khởi động lại máy
```

Cài driver NVIDIA **bản mới nhất cho Windows** (driver Windows tự expose GPU vào WSL — KHÔNG cài driver trong Ubuntu). Kiểm tra trong Ubuntu: `nvidia-smi` phải thấy RTX 3050.

### 5b. Môi trường train (trong Ubuntu/WSL)

```bash
sudo apt update && sudo apt install -y python3-venv python3-pip git
git clone https://github.com/<username>/vlash-thesis.git && cd vlash-thesis
python3 -m venv .venv && source .venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cu121
pip install -e .        # cài vlash + lerobot==0.4.1, peft, bitsandbytes theo pyproject
python -c "import torch; print(torch.cuda.get_device_name(0))"   # phải in RTX 3050
```

### 5c. Config cho 6GB VRAM (đã chuẩn bị sẵn trong CLAUDE.md)

```yaml
batch_size: 1
grad_accum_steps: 16      # batch hiệu dụng = 16
max_delay_steps: 4        # giảm từ 8
lora: { enable: true, r: 16, use_qlora: true }   # QLoRA bắt buộc với 6GB
policy: { state_cond: true }                      # BẮT BUỘC cho VLASH
shared_observation: true
wandb: { enable: false }
```

Điểm chết người cần nhớ: `state_cond: true` và `lora.extra_trainable_modules` (state_proj, action_in_proj, time_mlp_*) phải được train đầy đủ — thiếu là VLASH không học được cách dùng state.

### 5d. Chạy và đánh giá

```bash
vlash train examples/train/pi05/async.yaml        # train (theo dõi VRAM bằng nvidia-smi)
vlash benchmark examples/benchmarks/inference_latency.yaml   # đo latency, KHÔNG cần robot
```

Kỳ vọng trên RTX 3050: latency ~180–250ms → Δ ≈ 3–5 bước ở 20Hz. Sau đó eval sync / naive / VLASH ở Δ = 1–4 trên LIBERO subset — đúng kế hoạch đã viết ở mục 4.1 của thesis. Kết quả này (nếu có) sẽ thành mục mới trong Chương 3.

---

## Giai đoạn 6 — Quy trình làm việc 2 máy hằng ngày

```
Mở máy (bất kỳ máy nào):   git pull
Kết thúc buổi làm việc:    git add -A → git commit -m "mô tả ngắn" → git push
```

Quy tắc vàng: **push trước khi đổi máy**. Nếu quên và sửa cùng một file trên cả 2 máy, git sẽ báo "conflict" (xung đột) — lúc đó cứ nhờ Claude gỡ, đừng tự xoá gì.

---

## Tóm tắt thứ tự làm

- [ ] 1. Cài Git + Python + Node + VS Code + Claude Desktop (30')
- [ ] 2. Tạo repo GitHub riêng → push từ Mac → clone về Windows (20')
- [ ] 3. Chạy lại simulation, đối chiếu 4 dòng số (10')
- [ ] 4. Thử mở folder bằng Claude Cowork trên Windows, hỏi nó 1 câu về thesis để kiểm tra nó nắm bối cảnh
- [ ] 5. (Chờ supervisor) WSL2 + QLoRA fine-tune
- [ ] Luôn: pull khi mở máy, push khi xong việc
