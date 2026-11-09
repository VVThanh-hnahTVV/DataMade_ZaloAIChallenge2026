# 04. Luật thi và yêu cầu kỹ thuật (bản dịch tiếng Việt)

## Các vòng
1. **Public test**: tự phát triển, nộp `submission.jsonl`, điểm chỉ để tham khảo.
2. **Nộp giải pháp cuối**: gói Docker theo hướng dẫn riêng của BTC; BTC mount test set vào `/data` và thu `/result/submission.jsonl`.
3. **Private test**: BTC công bố private set, đội chạy giải pháp đã đóng băng và nộp kết quả. **Xếp hạng cuối dựa trên lần chạy lại image Docker của BTC (Luật 8).**

## Yêu cầu kỹ thuật (vi phạm là bị loại)
1. Đội và điều kiện tham gia theo quy chế chung Zalo AI Challenge 2026.
2. **Model**: dùng bất kỳ model có weights công bố công khai **trước 26/10/2026** với giấy phép cho phép; được fine-tune.
   Tổng tham số mọi model dùng lúc inference (LLM, embedding, reranker, classifier), dù nạp cùng lúc hay không,
   **≤ 15B**, tính toàn bộ tham số MoE. Cho phép mọi kiểu quantization. Model dùng phải khai báo trong README.
3. **Không dịch vụ ngoài**: inference chạy hoàn toàn offline trong image: không API LLM thương mại, không tải về, không mạng. Image chạy với mạng tắt.
4. **Không có người trong vòng lặp**. Cấm hard-code đáp án hoặc logic gắn với question id / business id.
5. **Thực thi code**: agent được sinh và chạy code trong container (khuyến khích, không bắt buộc). Thư mục dữ liệu mount chỉ đọc; file tạm ghi chỗ khác (`/tmp`).
6. **Dữ liệu**: được dùng dữ liệu train được cấp, dữ liệu tự tổng hợp, dataset/model công khai. **Cấm dùng public/private test để train, cấm thu thập đáp án test bằng bất cứ cách nào.**
7. **Tài nguyên tham chiếu**: máy 2 × RTX 5090 (32 GB VRAM mỗi card, 64 GB tổng), RAM 512 GB. Toàn bộ private test phải xong trong **6 giờ**, tính cả nạp model. Blackwell cần CUDA ≥ 12.8 và PyTorch/vLLM tương ứng.
8. **Điểm cuối và tái lập**: điểm lần chạy lại của BTC là điểm cuối. `submission.jsonl` nộp ở private test chỉ quyết định leaderboard tạm thời và đội nào được chạy lại. Tái lập được nếu **|PA(đã nộp) − PA(chạy lại)| ≤ 0.03**. Nếu lệch hơn, BTC xem log, có thể chạy lại lần nữa, hỏi thêm thông tin; không giải thích được thì **loại**. Nếu chạy lại vượt thời gian hoặc dừng sớm, chỉ tính các đáp án đã ghi vào `/result/submission.jsonl` trước khi dừng, phần còn lại là abstain.

---
# Hướng dẫn nộp Docker (tóm tắt, dịch từ `zac2026_DataMate_docker_guideline_final.pdf`)

## Máy test
| Mục | Giá trị |
|---|---|
| GPU | 2 × RTX 5090, 32 GB mỗi card |
| RAM | 512 GB |
| CUDA | ≥ 12.8, PyTorch/vLLM có hỗ trợ Blackwell |
| Base image khuyến nghị | `vllm/vllm-openai:v0.10.1.1` (PyTorch 2.7.1+cu128, vLLM 0.10.1.1). Phương án khác phải hỗ trợ compute capability 12.0 |
| Mạng | Tắt khi inference |
| `/data` | Chỉ đọc; ghi tạm ở `/tmp` |
| Thời gian | 6 giờ cho toàn bộ private test, gồm nạp model |
| Tổng tham số model | ≤ 15B (kể cả mọi tham số MoE) |
| Kích thước image | ≤ 100 GB cho file `docker save` .tar chưa nén |
Tham khảo: Qwen3-14B khởi tạo ~2 phút (kể cả compile và CUDA graphs).

## Input/Output
- `/data/` có `data/<business_id>/…`, `rulebook.md`, `calendar.csv`, `questions.jsonl` (id, business_id, question, as_of_date).
- `/result/submission.jsonl`: mỗi dòng id, type, answer. **Ghi đáp án ngay khi có** (dừng sớm/quá giờ thì chỉ phần đã ghi được chấm).
- `/result/logs/`: một bản ghi log mỗi câu, định dạng tùy ý. Trường **bắt buộc**:
  - `id`: id câu hỏi.
  - `answer`: đáp án cuối (vd `{"type":"number","answer":48250000}`).
  - `elapsed_ms`: số nguyên không âm, mili giây từ lúc bắt đầu câu đến khi có đáp án cuối (gồm đọc dữ liệu, suy luận, chạy code; với batching tính từ lúc câu vào batch).
  - `thinking`: suy luận của model **đúng như sinh ra**, không tóm tắt/cắt (vd nội dung `<think>…</think>` hoặc `reasoning_content`); nhiều lần gọi model thì ghi list string theo thứ tự; `null` nếu không có suy luận.
  - Với câu giải bằng code: `code` (code thực sự đã chạy, hoặc `file::hàm` + `inputs` thực tế) và `output` (giá trị trả về/kết quả).

## Cấu trúc thư mục trong image (`/code/predict.sh` và đường dẫn `/data`, `/result` là cố định)
```
/code/
├── predict.sh        # điểm vào
├── README.md
├── requirements.txt
├── src/              # code inference
├── models/           # weights
└── training_code/
    ├── README.md, requirements.txt, train.sh (nếu có train)
    ├── configs/, src/, data_generation/, data/, logs/, checkpoints/
    └── data_manifest.json   # đường dẫn local, SHA-256; URL public của base model
```
Phải đóng gói đủ weights cho inference (base + adapter, hoặc checkpoint đã merge); link công khai tới base model
không thay thế cho weights inference. Chỉ checkpoint base mã nguồn mở **chỉ dùng cho training** mới được để dạng link.

## Quy tắc predict.sh
1. `bash /code/predict.sh` chạy không tham số.
2. Đọc `/data`; ghi `submission.jsonl` và log mỗi câu dưới `/result` (tự tạo thư mục thiếu).
3. Cố định mặc định cho model, seed, temperature, batch size...; BTC không sửa.
4. Không can thiệp thủ công, không hard-code đáp án/logic theo question/business id.
5. Agent được sinh và chạy code trong container.

## Tái lập
Cần |PA(upload) − PA(re-run)| ≤ 0.03. Dùng seed cố định hoặc greedy decoding. **Batch GPU có thể làm đổi output
giữa các lần chạy dù greedy** -> trước khi nộp, chạy image 2 lần trên cùng input và so sánh, hoặc tính PA trên
train (có answers.jsonl).

## Thời gian
Toàn bộ private test trong 6 giờ thực (gồm nạp/khởi tạo). Hết giờ BTC dừng container; đáp án chưa ghi = abstain.
Tie-break: tổng thời gian inference thấp hơn, rồi nộp sớm hơn.

## README (`/code/README.md`) phải có
- **Approach**: cách đọc dữ liệu, sinh/chạy code, chọn đáp án.
- **Models**: tên, nguồn công khai, revision cố định, ngày phát hành gốc (< 26/10/2026), giấy phép, số tham số. Fine-tune được; tổng ≤ 15B.
- **Data**: nguồn/phiên bản, cách sinh/tiền xử lý, số mẫu train/val.
- Được dùng: dữ liệu được cấp, tự sinh, dataset/model công khai. Không bao giờ train trên public/private test hay thu thập đáp án test.
- `training_code/` đủ để tái lập: code, config, prompt/template, dependency pin, seed, dữ liệu train/val, log, README lệnh chạy chính xác, `data_manifest.json`. Ghi rõ nếu **không** train hay sinh dữ liệu.

## Build image
```bash
docker pull vllm/vllm-openai:v0.10.1.1
docker build --platform linux/amd64 -t zaic2026_datamate_<team_name>:final .
docker image inspect -f '{{.Os}}/{{.Architecture}} {{.Size}}' zaic2026_datamate_<team_name>:final
docker run --rm --network none --entrypoint "" zaic2026_datamate_<team_name>:final find /code -maxdepth 2
```
Dockerfile tham chiếu:
```dockerfile
FROM vllm/vllm-openai:v0.10.1.1
ENTRYPOINT []
ENV HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PIP_NO_CACHE_DIR=1 NCCL_P2P_DISABLE=1
WORKDIR /code
COPY requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r /code/requirements.txt
RUN pip install --no-cache-dir --no-deps nvidia-nccl-cu12==2.27.7
COPY models/ /code/models/
COPY training_code/ /code/training_code/
COPY predict.sh README.md /code/
COPY src/ /code/src/
RUN chmod +x /code/predict.sh
CMD ["bash", "/code/predict.sh"]
```
Lưu ý: reset `ENTRYPOINT []`; nâng NCCL lên 2.27.7 để tránh treo khởi tạo 2 GPU; `NCCL_P2P_DISABLE=1` vì cặp GPU test không có P2P;
`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`; `.dockerignore` không được loại training data. Tên image: `zaic2026_datamate_<team_name>:final` (team_name chữ thường).

## Kiểm tra trước khi nộp (lệnh chấm thật)
```bash
docker run --rm --gpus '"device=0,1"' --network none --shm-size=16g \
  --entrypoint bash \
  -v /path/to/public_test:/data:ro \
  -v /path/to/output:/result \
  zaic2026_datamate_<team_name>:final /code/predict.sh
```
`--shm-size=16g` là bắt buộc (mặc định 64 MiB làm NCCL lỗi cấp phát). Không có privileged, Docker socket, credential hay dịch vụ host.
Checklist: chạy hết không lỗi, không mạng; submission phủ mọi câu; mỗi câu có log (id, answer, elapsed_ms, thinking);
ước tính thời gian = nạp model + (thời gian TB/câu × 500) < 6h; hai lần chạy cho cùng đáp án (hoặc PA train lệch ≤ 0.03);
mọi tài liệu training/bằng chứng đã đóng gói; xuất một image linux/amd64, .tar chưa nén ≤ 100 GB.

## Nộp image
```bash
set -o pipefail
docker save zaic2026_datamate_<team_name>:final | gzip > zaic2026_datamate_<team_name>.tar.gz
gzip -dc zaic2026_datamate_<team_name>.tar.gz | wc -c      # kích thước .tar chưa nén (byte)
md5sum zaic2026_datamate_<team_name>.tar.gz > zaic2026_datamate_<team_name>.tar.gz.md5
```
(`pigz -p 8` nhanh hơn gzip.) Upload `.tar.gz`, gửi link + file `.md5` (hoặc một dòng của nó) + kích thước .tar chưa nén.
Không đổi tên archive sau khi tạo `.md5`; tải thử về máy khác và `md5sum -c` trước khi gửi. Manifest phải nằm trong image.
Sau hạn nộp, không được đổi image, code, config, model, dữ liệu training, hay revision/checksum base checkpoint đã khai.
