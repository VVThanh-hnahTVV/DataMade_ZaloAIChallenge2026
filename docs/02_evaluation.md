# 02. Đánh giá (bản dịch tiếng Việt)

## Chấm từng câu
Mỗi câu được chấm **đúng / sai / abstain**. Đáp án type `abstain` (hoặc thiếu đáp án) = abstain. Đáp án khác chỉ
đúng khi **type trùng type tham chiếu VÀ giá trị khớp** theo bảng dưới; ngược lại là sai. Không có điểm từng phần.

| Type | Nội dung | Ví dụ | Quy tắc khớp |
|---|---|---|---|
| `number` | Giá trị số (tiền VND, số đếm, số lượng) | `48250000` | Khớp chính xác. Giá trị tham chiếu là số nguyên (VND, đếm, số lượng) hoặc làm tròn 2 chữ số thập phân. |
| `percent` | Giá trị phần trăm | `-12.45` | Khớp chính xác sau khi làm tròn 2 chữ số thập phân; **dấu phải đúng**. |
| `string` | Tên (sản phẩm, khách hàng, chi nhánh, thứ trong tuần...) | `"Sting dâu 330ml"` | Cả đáp án và từng dạng chấp nhận được chuẩn hóa rồi so sánh bằng. Chuẩn hóa: (1) Unicode NFC; (2) chữ thường; (3) mọi ký tự không phải chữ/số/khoảng trắng thành khoảng trắng; (4) cắt khoảng trắng đầu/cuối, gộp chuỗi khoảng trắng thành một. **Không bỏ dấu tiếng Việt.** Mỗi tham chiếu liệt kê các dạng chấp nhận (alias): mọi cách viết của tên xuất hiện trong dữ liệu của doanh nghiệp đó, cộng mã (vd `sp0042`). |
| `date` | Ngày ISO | `"2026-08-15"`, `"2025-09"` | Khớp chính xác. `yyyy-mm-dd`; câu hỏi về tháng: `yyyy-mm`. |
| `boolean` | true/false | `true` | Khớp chính xác. |
| `list` | Danh sách có thứ tự (tên hoặc số) | `["Cà phê sữa","Bạc xỉu","Trà đào"]` | **Luôn có thứ tự**, khớp theo vị trí. Thứ tự là thứ câu hỏi yêu cầu, hoặc mặc định rulebook khi câu hỏi không nêu. Phần tử khớp theo quy tắc `string` hoặc `number`. |
| `table` | Bảng nhỏ: tên cột + hàng | `{"columns":[...],"rows":[[...]]}` | Cột khớp theo tên đã chuẩn hóa; nếu tên không khớp thì khớp theo vị trí. Hàng khớp như **tập hợp**; ô tên theo quy tắc `string`, ô số theo quy tắc `number`. |
| `unanswerable` | Dữ liệu không có thứ cần để trả lời | — | Đúng khi và chỉ khi tham chiếu là unanswerable. |
| `abstain` | Agent chọn không trả lời | — | Tính là abstain bất kể tham chiếu. |

## Câu hỏi xếp hạng
Xếp hạng dùng tiêu chí nêu trong câu hỏi, hoặc **mặc định của rulebook** nếu câu hỏi không nêu, theo thứ tự giảm
dần của tiêu chí, chỉ trên các đơn hợp lệ. Phần tử bằng giá trị thì **xếp theo mã tăng dần**. Câu có hòa ở ranh
giới top-k (hoặc ở hạng 1 với câu "... nhất") bị loại khỏi bộ test. Nếu ít hơn k ứng viên, đáp án là tất cả.

## Điểm: Penalized Accuracy (PA)
Trên N câu của một bộ test: **đúng +1, abstain 0, sai −1**, PA = (tổng điểm)/N. Mọi đáp án đưa ra cho câu
unanswerable đều tính là sai. Mọi câu cùng trọng số. Đồng điểm: xếp theo tổng thời gian inference trong lần
chạy lại của BTC, rồi đến nộp sớm hơn.

=> Chỉ trả lời khi P(đúng) > 0.5; còn lại abstain. Câu unanswerable mà trả lời giá trị = −1.
