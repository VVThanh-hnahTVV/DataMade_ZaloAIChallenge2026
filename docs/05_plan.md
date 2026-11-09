# 05. Kế hoạch và checklist

## Mốc thời gian
- 26/10 – 16/11: public test, tối đa 5 lượt nộp/ngày.
- **16/11 23:59 (GMT+7)**: nộp Docker (tối đa 2 lần, chấm lần cuối).
- 20/11 9:00: công bố private test; hạn nộp kết quả **23/11 23:59**.
- 2/12: công bố top 2.

## Hướng làm (đề xuất, chỉnh theo kết quả thực nghiệm)
1. Loader: đọc README + schema (CSV/XLSX/SQLite) của business; nạp rulebook của split đang chạy.
2. Agent sinh code (pandas/SQL) với helper đã đóng gói (`resolve_period()`, các hàm theo rulebook: doanh thu, giá vốn, nợ, tồn kho, xếp hạng...).
3. Bộ kiểm chứng đáp án: đúng type, đơn vị (percent là 12.4 chứ không phải 0.124), tie-break theo mã tăng dần.
4. Cổng abstain/unanswerable: chỉ trả lời khi tin cậy > 0.5; unanswerable khi thiếu cột/dữ liệu cần thiết.
5. Ghi `submission.jsonl` từng dòng (flush) + log `/result/logs/` (id, answer, elapsed_ms, thinking, code, output).
6. Đánh giá cục bộ bằng `scripts/score.py` trên train, chia theo business_id.

## Checklist trước khi đóng băng
- [ ] Tổng tham số model ≤ 15B, weights phát hành trước 26/10/2026, đã khai trong README.
- [ ] Offline hoàn toàn (HF_HUB_OFFLINE=1, TRANSFORMERS_OFFLINE=1), temperature=0, seed cố định.
- [ ] Chạy 2 lần cho kết quả khớp (|ΔPA| ≤ 0.03).
- [ ] Ước tính thời gian: nạp model + TB/câu × 500 < 6h (để dư an toàn).
- [ ] Không có logic theo question id / business_id; không dùng test để train.
- [ ] Test `resolve_period()` và helper rulebook.
- [ ] Đã chạy lệnh `docker run` chấm thật với `--shm-size=16g --network none`.
- [ ] `training_code/` + `data_manifest.json` + README đầy đủ.
