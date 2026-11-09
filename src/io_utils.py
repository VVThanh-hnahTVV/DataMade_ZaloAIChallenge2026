"""Đọc & làm sạch dữ liệu thô (bước I/O), tách khỏi logic nghiệp vụ.

Scope hiện tại: họ schema 'file phẳng mỗi dòng một dòng hàng' như biz_101.
"""
import re

import pandas as pd


def parse_money(x):
    """'560,000' -> 560000. Dấu phẩy là ngăn cách nghìn ở biz_101."""
    if pd.isna(x):
        return pd.NA
    s = str(x).replace(",", "").replace(" ", "")
    if s in ("", "-"):
        return pd.NA
    return int(round(float(s)))


_VN_DATE = re.compile(r"(\d{1,2})\s*thg\s*(\d{1,2})\s*(\d{4})")


def parse_vn_date(x):
    """'1 thg 6 2025' -> Timestamp(2025-06-01); NaT nếu không khớp."""
    m = _VN_DATE.match(str(x).strip())
    if not m:
        return pd.NaT
    d, mo, y = (int(g) for g in m.groups())
    return pd.Timestamp(y, mo, d)


def load_flat_sales(path):
    """Đọc file bán hàng phẳng, đổi tên cột cốt lõi + thêm cột đã chuẩn hóa.

    Cột chuẩn hóa thêm: amount (số), date (Timestamp).
    Cột đổi tên: Nội dung->item, Kết quả->status, Mã hóa đơn->order.
    """
    df = pd.read_csv(path)
    df["amount"] = df["Thanh tien"].map(parse_money)
    df["date"] = df["Ngày tháng"].map(parse_vn_date)
    return df.rename(columns={
        "Nội dung": "item",
        "Kết quả": "status",
        "Mã hóa đơn": "order",
    })
