"""Trả lời 1 câu cụ thể để minh họa pipeline (chạy: uv run python src/answer_q.py).

Q: "thang 2/2026 mat hang Thuoc la Vinataba thu ve bao nhieu tien"
business_id=biz_101, as_of_date=2026-08-24  ->  type=number (doanh thu §1).
"""
import json

from io_utils import load_flat_sales       # cùng thư mục src/
from rulebook import resolve_month, valid_order_mask

DATA = "train/data/biz_101/ban_hang.csv"   # đường dẫn tính từ gốc repo


def answer():
    df = load_flat_sales(DATA)

    # 1) kỳ: "tháng 2/2026"
    start, end = resolve_month(2026, 2)

    # 2) lọc theo rulebook §1: chỉ giữ dòng thuộc đơn hợp lệ
    df = df[valid_order_mask(df)]

    # 3) lọc đúng mặt hàng + đúng kỳ, rồi cộng thành tiền từng dòng
    mask = (
        (df["item"] == "Thuốc lá Vinataba")
        & (df["date"] >= start)
        & (df["date"] <= end)
    )
    total = int(df.loc[mask, "amount"].sum())
    return {"type": "number", "answer": total}


if __name__ == "__main__":
    print(json.dumps(answer(), ensure_ascii=False))
