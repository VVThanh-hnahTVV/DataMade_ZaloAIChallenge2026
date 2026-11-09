# 03. Dữ liệu (bản dịch tiếng Việt)

## Loại hình doanh nghiệp
Tạp hóa, quán cà phê/trà sữa, nhà hàng, nhà thuốc, cửa hàng vật liệu xây dựng, tiệm sửa xe máy, cửa hàng mẹ và
bé... **Private test có loại hình không xuất hiện ở train/public test** -> không được nhúng cứng schema/ngữ nghĩa
theo ngành. Mỗi doanh nghiệp có 12–30 tháng hoạt động, có tính mùa vụ (Tết, Trung thu, lễ, ngày lương, cuối tuần),
từ vài trăm đến ~300.000 dòng.

## Cấu trúc gói
```
<split>/
├── data/<business_id>/
│   ├── *.csv | *.xlsx | *.sqlite   # một hoặc nhiều file dữ liệu
│   └── README.md                   # mô tả doanh nghiệp và ghi chú
├── rulebook.md                     # quy tắc mặc định và từ vựng (RIÊNG cho từng split)
├── calendar.csv                    # lịch âm–dương (Tết)
├── questions.jsonl                 # mỗi dòng một câu: id, business_id, question, as_of_date
└── answers.jsonl                   # chỉ có ở train
```
`answers.jsonl` (train): cùng định dạng submission + trường `alias` (các dạng chấp nhận khác của đáp án tên,
gồm cả mã). Câu unanswerable có `"answer": null`. Nộp bài không cần trường `alias`.

```json
{"id": "q_06de33fa21cc", "type": "string", "answer": "Xi măng Hà Tiên PCB40 bao 50kg", "alias": ["SP0001"]}
```

Chất lượng README.md rất khác nhau: có nơi đầy đủ data dictionary, có nơi chỉ vài ghi chú, có nơi gần như trống
-> agent phải tự khảo sát schema/dữ liệu thực tế.

## Rulebook (mặc định diễn giải)
Mỗi split có `rulebook.md` riêng, cố định nghĩa mặc định của thuật ngữ khi câu hỏi không nói khác.
**Rulebook có thể khác giữa các split -> agent phải đọc và áp dụng rulebook của split đang chạy, không dùng bản train.**
Ví dụ: doanh thu = tổng thành tiền dòng sau giảm giá dòng (không trừ voucher cấp đơn), không VAT, không phí giao
hàng, loại đơn hủy và đơn có bất kỳ mặt hàng trả lại; "bán chạy" = theo số lượng; tuần = Thứ Hai–Chủ Nhật;
"tháng này" = tháng chứa as_of_date, tính đến hết ngày đó; giá vốn mặc định = bình quân gia quyền theo lô;
cửa sổ Tết = 23 tháng Chạp đến mùng 10 (âm lịch).

## Định dạng nộp bài
```json
{"id": "q_01234", "type": "string",  "answer": "Sting dâu 330ml"}
{"id": "q_01235", "type": "number",  "answer": 48250000}
{"id": "q_01236", "type": "percent", "answer": -12.45}
{"id": "q_01237", "type": "date",    "answer": "2026-08-15"}
{"id": "q_01238", "type": "boolean", "answer": true}
{"id": "q_01239", "type": "list",    "answer": ["Cà phê sữa", "Bạc xỉu", "Trà đào"]}
{"id": "q_01240", "type": "table",   "answer": {"columns": ["khach_hang", "so_tien_no"], "rows": [["Chị Lan", 3200000], ["Anh Tú", 1500000]]}}
{"id": "q_01241", "type": "unanswerable", "reason": "Dữ liệu không có giá vốn nên không tính được lợi nhuận"}
{"id": "q_01242", "type": "abstain"}
```
Câu thiếu trong file tính là abstain. Trường `reason` là tùy chọn.

## Trạng thái dữ liệu local (đã kiểm tra)
- `train/`: 31 business (`biz_1xx`), 3000 câu có đáp án. `public_test/`: 15 business (`dev_0xx`), 1000 câu, không đáp án.
- Phân bố type ở train: number 1884, percent 578, list 193, date 145, string 88, unanswerable 70, boolean 23, table 19.
- Private test dự kiến khoảng 500 câu (theo Docker guideline: "average time per question × 500").
