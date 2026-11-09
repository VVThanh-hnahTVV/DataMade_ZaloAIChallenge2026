"""Ngữ nghĩa rulebook.md, độc lập với schema từng shop.

Chỉ chứa các quy tắc 'mặc định diễn giải', không chứa logic đọc file.
"""
import calendar

import pandas as pd


def resolve_month(year, month):
    """Một tháng -> (đầu kỳ, cuối kỳ) gồm cả 2 mốc. VD (2026,2) -> 01..28/02."""
    start = pd.Timestamp(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end = pd.Timestamp(year, month, last_day)
    return start, end


# §1: đơn tính vào doanh thu = KHÔNG hủy & KHÔNG trả hàng; đơn 'đang giao' VẪN tính.
VALID_STATUS = {"Xong", "Đang giao"}


def valid_order_mask(df, status_col="status", order_col="order"):
    """Mask các dòng thuộc đơn hợp lệ theo §1.

    Luật §1: 'đơn có trả hàng, kể cả một phần, bỏ CẢ đơn' -> xét ở mức ĐƠN,
    không chỉ ở mức dòng. Lấy trạng thái đại diện của mỗi đơn rồi áp cho mọi dòng.
    """
    order_status = df.groupby(order_col)[status_col].transform("first")
    return order_status.isin(VALID_STATUS)
