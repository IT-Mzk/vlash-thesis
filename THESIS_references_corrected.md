# Bibliography đã kiểm chứng & sửa (cho thesis VLASH)

> Định dạng tạm theo kiểu IEEE đánh số `[n]`. Thứ tự cuối (alphabet theo họ vs theo thứ tự xuất hiện) **cần xác nhận với supervisor** — rule trường có ghi cả hai chỗ khác nhau.

## ⚠️ Các lỗi trích dẫn đã phát hiện & sửa

| Ref | Lỗi trong thesis hiện tại | Sửa đúng |
|---|---|---|
| **[1] VLASH** | Tác giả ghi sai: *"Y. Tang, J. Guo, Z. Liu, and S. Levine"* — J. Guo & S. Levine **không** thuộc nhóm tác giả | **J. Tang, Y. Sun, Y. Zhao, S. Yang, Y. Lin, Z. Zhang, J. Hou, Y. Lu, Z. Liu, S. Han** (MIT/NVIDIA), arXiv:2512.01031 |
| **[3] π0.5** | Ghi "Physical Intelligence Technical Report" | Là bài arXiv:**2504.16054** (2025), *"π0.5: a Vision-Language-Action Model with Open-World Generalization"* |
| **[4] SmolVLA** | Tựa & tác giả sai: *"A Small yet Efficient... M. Shukor, A. Cord, and M. Cord"* | **M. Shukor, D. Aubakirova, F. Capuano, ... R. Cadene**, *"SmolVLA: A Vision-Language-Action Model for Affordable and Efficient Robotics,"* arXiv:**2506.01844** |
| **[5] RTC** | Tựa sai: *"Real-Time Chunking for Asynchronous VLA Models"* | **K. Black, M. Y. Galliker, S. Levine**, *"Real-Time Execution of Action Chunking Flow Policies,"* arXiv:**2506.07339**, NeurIPS 2025 |
| **A2C2** | Tác giả **bịa**: *"Šílený et al."* | *"Leave No Observation Behind: Real-Time Correction for VLA Action Chunks,"* arXiv:**2509.23224** (2025). **Lưu ý nội dung:** A2C2 là correction head gắn ngoài, **không cần retrain base policy** → câu trong Ch1 nói A2C2 "incompatible with off-the-shelf checkpoints / requires retraining from scratch" **cần sửa lại cho đúng** (nó vẫn thêm overhead per-step + 1 module huấn luyện riêng, nhưng không retrain base). |
| **[14] GR00T** | Tựa **sai/đùa**: *"Groot: Learning to Move Like Groot"* | **NVIDIA**, *"GR00T N1: An Open Foundation Model for Generalist Humanoid Robots,"* arXiv:**2503.14734** (2025) |

## Danh sách reference đã chuẩn hoá

1. J. Tang, Y. Sun, Y. Zhao, S. Yang, Y. Lin, Z. Zhang, J. Hou, Y. Lu, Z. Liu, and S. Han, "VLASH: Real-Time VLAs via Future-State-Aware Asynchronous Inference," arXiv:2512.01031, 2025.
2. K. Black, N. Brown, D. Driess, et al. (Physical Intelligence), "π0: A Vision-Language-Action Flow Model for General Robot Control," arXiv:2410.24164, 2024.
3. Physical Intelligence (K. Black et al.), "π0.5: a Vision-Language-Action Model with Open-World Generalization," arXiv:2504.16054, 2025.
4. M. Shukor, D. Aubakirova, F. Capuano, P. Kooijmans, S. Palma, A. Zouitine, M. Aractingi, C. Pascal, M. Russi, A. Marafioti, S. Alibert, M. Cord, T. Wolf, and R. Cadene, "SmolVLA: A Vision-Language-Action Model for Affordable and Efficient Robotics," arXiv:2506.01844, 2025.
5. K. Black, M. Y. Galliker, and S. Levine, "Real-Time Execution of Action Chunking Flow Policies," arXiv:2506.07339; NeurIPS 2025.
6. (A2C2) "Leave No Observation Behind: Real-Time Correction for VLA Action Chunks," arXiv:2509.23224, 2025.
7. B. Liu, Y. Zhu, C. Gao, Y. Feng, Q. Liu, Y. Zhu, and P. Stone, "LIBERO: Benchmarking Knowledge Transfer for Lifelong Robot Learning," NeurIPS, vol. 36, 2023.
8. T. Z. Zhao, V. Kumar, S. Levine, and C. Finn, "Learning Fine-Grained Bimanual Manipulation with Low-Cost Hardware" (ACT), RSS, 2023.
9. M. Matthews, M. Beukman, et al., "Kinetix: Investigating the Training of General Agents through Open-Ended Physics-Based Control Tasks," arXiv:2410.23208, 2025 (ICLR 2025).
10. E. J. Hu, Y. Shen, P. Wallis, Z. Allen-Zhu, Y. Li, S. Wang, L. Wang, and W. Chen, "LoRA: Low-Rank Adaptation of Large Language Models," ICLR, 2022.
11. Y. Lipman, R. T. Q. Chen, H. Ben-Hamu, M. Nickel, and M. Le, "Flow Matching for Generative Modeling," ICLR, 2023.
12. A. Brohan, N. Brown, et al., "RT-2: Vision-Language-Action Models Transfer Web Knowledge to Robotic Control," CoRL, 2023.
13. L. Beyer, A. Steiner, A. S. Pinto, et al., "PaliGemma: A Versatile 3B VLM for Transfer," arXiv:2407.07519, 2024.
14. X. Zhai, B. Mustafa, A. Kolesnikov, and L. Beyer, "Sigmoid Loss for Language Image Pre-Training" (SigLIP), ICCV, 2023.
15. NVIDIA, "GR00T N1: An Open Foundation Model for Generalist Humanoid Robots," arXiv:2503.14734, 2025.
16. M. J. Kim, K. Pertsch, S. Karamcheti, et al., "OpenVLA: An Open-Source Vision-Language-Action Model," arXiv:2406.09246, 2024.  *(dùng cho Future Work)*

> Cần bổ sung thêm nếu dùng tới: Gemini Robotics (Google DeepMind, 2025); MuJoCo (Todorov et al., IROS 2012) cho mô tả LIBERO.
