# DataMate: Zalo AI Challenge 2026

## Mục tiêu
Agent trả lời câu hỏi tiếng Việt trên dữ liệu bảng (CSV/XLSX/SQLite) của
doanh nghiệp nhỏ. Output: submission.jsonl, mỗi dòng {id, type, answer}.
Type: number | percent | string | date | boolean | list | table |
unanswerable | abstain.
Input mỗi câu: id, business_id, question, as_of_date. Mỗi business có data
files + README.md (chất lượng không đều); mỗi split có rulebook.md + calendar.csv.

## Luật cứng (vi phạm là bị loại)
- Inference offline hoàn toàn, không API ngoài, không mạng, không tải về.
- Tổng tham số mọi model (LLM, embedding, reranker, classifier) ≤ 15B (tính cả
  MoE), weights công bố trước 26/10/2026, license cho phép. Khai báo trong README.
- Cấm hard-code đáp án hoặc logic theo question id / business_id. Không người
  trong vòng lặp.
- Không dùng public/private test để train hoặc thu thập đáp án.
- /data chỉ đọc. Ghi tạm ở /tmp, kết quả ở /result.
- Toàn bộ private test (~500 câu) chạy trong 6h trên 2×RTX 5090, gồm cả nạp model.
  Hết giờ chỉ tính các dòng đã ghi, còn lại là abstain.
- Re-run phải khớp bản nộp (|ΔPA| ≤ 0.03): temperature=0, seed cố định. Batch GPU
  có thể làm đổi output dù greedy: chạy 2 lần để kiểm. Lệch không giải thích được = loại.
- Private test có loại hình doanh nghiệp chưa thấy ở train: không nhúng cứng schema theo ngành.

## Chấm điểm
PA: đúng +1, abstain 0, sai −1. Sai kiểu = sai. Unanswerable mà sai = −1.
=> chỉ trả lời khi P(đúng) > 0.5. Chi tiết: @docs/02_evaluation.md
Điểm cần nhớ: percent làm tròn 2 số lẻ, dấu phải đúng; string chuẩn hóa NFC +
lowercase + ký tự lạ thành space, KHÔNG bỏ dấu, chấp nhận alias (cách viết trong
dữ liệu + mã); list khớp theo vị trí; table khớp cột theo tên (hoặc vị trí), hàng
như tập hợp.

## Quy ước kỹ thuật
- Đọc rulebook.md của split đang chạy, KHÔNG nhúng cứng bản train.
- as_of_date + calendar.csv để quy đổi thời gian tương đối.
- Ghi submission.jsonl tăng dần (flush từng dòng).
- Log từng câu ở /result/logs/ (một record/câu), BẮT BUỘC: id, answer,
  elapsed_ms (int ≥ 0), thinking (nguyên văn, không tóm tắt; list nếu nhiều lần
  gọi; null nếu không có). Câu giải bằng code: thêm code (code thật đã chạy, hoặc
  file::hàm + inputs) và output.
- String answer giữ nguyên dấu, dùng đúng cách viết có trong dữ liệu hoặc mã.
- Tie-break xếp hạng: theo mã tăng dần. Câu list/ranking dùng tiêu chí trong
  câu hỏi, không có thì mặc định rulebook.

## Đóng gói Docker (hạn nộp 16/11 23:59; chi tiết @docs/04_rules.md)
- Base: vllm/vllm-openai:v0.10.1.1, ENTRYPOINT [], NCCL_P2P_DISABLE=1,
  nvidia-nccl-cu12==2.27.7, HF_HUB_OFFLINE=1, TRANSFORMERS_OFFLINE=1.
- Entry: `bash /code/predict.sh` không tham số; đọc /data, ghi /result.
  Layout: /code/{predict.sh,README.md,requirements.txt,src/,models/,training_code/}.
- Weights inference phải nằm trong image (base + adapter hoặc merged).
- Test bằng đúng lệnh chấm: --gpus '"device=0,1"' --network none --shm-size=16g
  --entrypoint bash -v public_test:/data:ro -v out:/result.
- Image tag: zaic2026_datamate_<team_name>:final, linux/amd64, .tar ≤ 100GB.

## Tài liệu chi tiết (bản dịch tiếng Việt của đề)
@docs/01_overview.md
@docs/02_evaluation.md
@docs/03_data.md
@docs/04_rules.md
@docs/05_plan.md

## Cách làm việc
- Chia tập theo business_id, không chia theo câu hỏi.
- Mọi thay đổi pipeline phải chạy lại bộ chấm cục bộ (scripts/score.py).
- Có test cho resolve_period() và các helper rulebook.
