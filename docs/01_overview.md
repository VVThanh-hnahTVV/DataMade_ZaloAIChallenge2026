# 01. Tổng quan đề bài DataMate (bản dịch tiếng Việt)

## Mô tả
Bảng tính và cơ sở dữ liệu đơn giản là hệ thống dữ liệu được dùng nhiều nhất thế giới. Chủ tiệm lưu bán hàng
và tồn kho bằng Excel; giáo viên lưu điểm và chuyên cần; phòng khám lưu lượt khám và lô thuốc; cán bộ nhân sự
lưu bảng chấm công; hợp tác xã lưu năng suất và chi phí đầu vào; UBND xã lưu thống kê hộ gia đình; nhà báo tải
dữ liệu mở của Tổng cục Thống kê; nhân viên tập đoàn muốn lấy một con số từ data warehouse mà không phải chờ
đội dữ liệu. Ai cũng có dữ liệu, gần như không ai biết viết truy vấn. Họ muốn hỏi bằng tiếng Việt đời thường:
"Tháng này bán chạy nhất mặt hàng gì?", "Tuần rồi bán được bao nhiêu ly trà sữa?", "Còn ai nợ tiền chưa trả?",
"Thuốc nào sắp hết hạn trong kho?" và nhận được câu trả lời đúng.

**DataMate** yêu cầu xây một AI agent trả lời câu hỏi tiếng Việt tự nhiên trực tiếp trên dữ liệu có cấu trúc
(CSV, Excel, SQLite): nhận file thô và câu hỏi, agent trả về đáp án đúng, **hoặc từ chối trả lời khi dữ liệu
không đủ để trả lời**. Dữ liệu cuộc thi xoay quanh doanh nghiệp nhỏ Việt Nam (nhóm dùng bảng tính đông nhất,
dữ liệu thực tế phong phú và "bẩn" nhất), nhưng năng lực cần xây là tổng quát: hỏi đáp ngôn ngữ tự nhiên trên dữ liệu bảng.

## Input
- Gói dữ liệu của một doanh nghiệp: một hoặc nhiều file (`.csv`, `.xlsx`, `.sqlite`) + `README.md` mô tả doanh nghiệp.
- Một câu hỏi tiếng Việt đời thường.
- `as_of_date`: "hôm nay" dùng để quy đổi thời gian tương đối ("tháng này", "tuần rồi", "cùng kỳ năm ngoái").
- Rulebook và lịch âm–dương dùng chung cho mọi doanh nghiệp trong một split.

## Output
Một đáp án thuộc một trong các type: giá trị (number, percent, string, date, boolean, list, table),
`unanswerable` (dữ liệu không đủ), hoặc `abstain` (agent chọn không trả lời).

## Ví dụ
Input (một dòng `questions.jsonl`):
```json
{"id": "q_06de33fa21cc", "business_id": "biz_118", "question": "sp bán dc nhiều nhất tuần rồi là gì", "as_of_date": "2026-03-04"}
```
Output (một dòng `submission.jsonl`):
```json
{"id": "q_06de33fa21cc", "type": "string", "answer": "Xi măng Hà Tiên PCB40 bao 50kg"}
```

## Lịch thi
**Vòng Public test (26/10 – 16/11):**
- Đội tự phát triển, chạy trên public test, nộp `submission.jsonl` qua mục Submission của cổng Zalo AI Challenge.
  Tối đa 5 lượt nộp/ngày (reset cuối ngày). Điểm hiển thị trên public leaderboard, chỉ để tham khảo.
- **16/11**: nộp giải pháp hoàn chỉnh (code train, code inference, dữ liệu) dạng gói Docker qua form "Solution
  Submission". File lớn nên cần checksum + link Google Drive công khai. Tối đa 2 lượt nộp, chỉ chấm lượt cuối.
  Hạn 23:59 (GMT+7).

**Vòng Private test (20/11 – 23/11):**
- 9:00 sáng 20/11: BTC công bố private test. Đội chạy giải pháp đã đóng băng và nộp `submission.jsonl`,
  hạn 23:59 (GMT+7) ngày 23/11. Private leaderboard xếp theo thứ tự thời gian nộp.
- BTC kiểm tra lại giải pháp, review mã nguồn, phát hiện gian lận. **Công bố top 2 vào 2/12.**
