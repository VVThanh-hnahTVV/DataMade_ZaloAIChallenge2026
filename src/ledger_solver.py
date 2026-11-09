"""Solver cho họ schema 'Sổ chi tiết bán hàng' (mỗi dòng một dòng hàng).

Luật lấy từ rulebook.md: đơn tính doanh thu = không hủy, không trả hàng; kỳ theo ngày đặt;
tuần bắt đầu thứ Hai; tháng này = ngày 1 đến hết hôm nay; ...
Trả về dict {"type":..., "answer":...} hoặc {"type":"abstain"}.
"""
import calendar
import math
import re
import unicodedata
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

import pandas as pd

ABSTAIN = {"type": "abstain"}


def strip_acc(s: str) -> str:
    s = unicodedata.normalize("NFD", str(s).lower().replace("đ", "d"))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9/%.,\- ]+", " ", s)


def norm_name(s: str) -> str:
    s = unicodedata.normalize("NFC", str(s)).lower()
    s = "".join(c if (c.isalnum() or c.isspace()) else " " for c in s)
    return " ".join(s.split())


def rnd(x, nd=0):
    q = Decimal(1).scaleb(-nd)
    return Decimal(repr(float(x))).quantize(q, rounding=ROUND_HALF_UP)


def num_out(x, nd=0):
    v = rnd(x, nd)
    return int(v) if nd == 0 else float(v)


# ----------------------------------------------------------------- loading
DONE, CANCEL, RETURN, SHIP = {"done"}, {"cancel"}, {"return"}, {"ship"}


def canon_status(x):
    t = strip_acc(x) if isinstance(x, str) else ""
    if "huy" in t:
        return "cancel"
    if "hoan hang" in t or "tra ve" in t or "tra hang" in t:
        return "return"
    if "giao" in t:
        return "ship"
    if "hoan thanh" in t or "xong" in t:
        return "done"
    return "other:" + t
GUEST = {"khach le", "kl", "le"}


class Ledger:
    def __init__(self, folder):
        parts = []
        for _, raw in pd.read_excel(f"{folder}/So_chi_tiet_ban_hang.xlsx", sheet_name=None, header=None, dtype=str).items():
            hit = raw.index[raw.apply(lambda r: "Mã đơn hàng" in r.values, axis=1)]
            if not len(hit):
                continue
            hdr = int(hit[0])
            part = raw.iloc[hdr + 1:].copy()
            part.columns = raw.iloc[hdr].tolist()
            parts.append(part)
        sales = pd.concat(parts, ignore_index=True)
        sales = sales[sales["Mã đơn hàng"].notna()].copy()
        sales["date"] = pd.to_datetime(sales["Ngày"], format="%d/%m/%Y").dt.date
        for src, dst in (("Thành tiền", "amount"), ("Số lượng quy đổi", "qty")):
            sales[dst] = pd.to_numeric(sales[src].str.replace(",", ""), errors="coerce")
        sales["st"] = sales["Trạng thái"].map(canon_status)
        sales = sales.rename(columns={"Mã đơn hàng": "order", "Tên hàng hóa": "item", "Khách hàng": "cust"})
        # lỗi xuất file: hai dòng giống hệt nhau trong cùng đơn tính một lần
        sales = sales.drop_duplicates(subset=["order", "item", "Đơn vị tính", "Số lượng", "Đơn giá",
                                              "Thành tiền", "Trạng thái", "Số lượng quy đổi", "cust"])
        cat = pd.read_excel(f"{folder}/Danh sách hàng hóa.xlsx", dtype=str)
        cat = cat.rename(columns={"Mã hàng hóa": "code", "Tên hàng hóa": "item", "Nhóm hàng hóa": "group",
                                  "Đơn vị tính": "base_unit"})
        self.cat = cat[["code", "item", "group", "base_unit"]]
        sales = sales.merge(self.cat, on="item", how="left")
        self.lines = sales
        o = sales.groupby("order").agg(date=("date", "first"), st=("st", "first"), cust=("cust", "first"),
                                       rev=("amount", "sum")).reset_index()
        o["cust_key"] = o["cust"].map(norm_name)
        o["is_guest"] = o["cust_key"].map(lambda k: strip_acc(k).strip() in GUEST)
        self.orders = o
        self.valid_orders = set(o.loc[o.st.isin(DONE | SHIP), "order"])
        self.vl = sales[sales["order"].isin(self.valid_orders)]
        self.vo = o[o.order.isin(self.valid_orders)]
        self.first, self.last = o["date"].min(), o["date"].max()
        self.items_norm = {norm_name(r.item): r for r in self.cat.itertuples()}
        self.groups = sorted({g for g in self.cat.group.dropna()}, key=len, reverse=True)

    # ---- aggregates
    def rev(self, a, b, lines=None):
        L = self.vl if lines is None else lines
        return float(L[(L.date >= a) & (L.date <= b)].amount.sum())

    def n_orders(self, a, b):
        return int(((self.vo.date >= a) & (self.vo.date <= b)).sum())

    def daily_rev(self, a, b):
        L = self.vl[(self.vl.date >= a) & (self.vl.date <= b)]
        return L.groupby("date").amount.sum()


# ----------------------------------------------------------------- date parsing
def month_end(y, m):
    return date(y, m, calendar.monthrange(y, m)[1])


def add_months(y, m, k):
    t = y * 12 + (m - 1) + k
    return t // 12, t % 12 + 1


def money(text):
    """'9.500.000d' '18 trieu' '190k' '3tr7' -> số"""
    m = re.search(r"(\d+)\s*tr\s*(\d+)?", text)
    if m and not re.search(r"\d\s*trong", text[m.start():m.end() + 6]):
        a, b = m.group(1), m.group(2)
        return int(a) * 1_000_000 + (int(b) * 10 ** (6 - len(b)) if b else 0)
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*trieu", text)
    if m:
        return float(m.group(1).replace(",", ".")) * 1_000_000
    m = re.search(r"(\d+)\s*k\b", text)
    if m:
        return int(m.group(1)) * 1000
    m = re.search(r"(\d{1,3}(?:[.,]\d{3})+)", text)
    if m:
        return int(re.sub(r"[.,]", "", m.group(1)))
    return None


MONTH_TOK = re.compile(r"(?:\b(?:thang|th|t)\s*)?\b(\d{1,2})\s*[/\-]\s*(\d{4}|\d{2})\b")


def parse_months(t):
    """Tìm các (năm, tháng) tường minh. Hỗ trợ '3/25', 'th2, th3, th4/2026', 'thang 5 nam 2026'."""
    t2 = re.sub(r"\b\d{1,2}\s*/\s*\d{1,2}\s*/\s*\d{4}\b", " ", t)  # bỏ dd/mm/yyyy
    out = []
    for m in re.finditer(r"(?:\b(?:thang|th|t)\s*)?\b(\d{1,2})\s*[/\-]\s*(\d{4}|\d{2})\b", t2):
        mo, y = int(m.group(1)), int(m.group(2))
        y = y + 2000 if y < 100 else y
        if 1 <= mo <= 12:
            out.append((y, mo))
    if out:
        # 'th2, th3, th4/2026': tháng không có năm đứng trước một token có năm
        pre = []
        for m in re.finditer(r"\b(?:thang|th|t)\s*(\d{1,2})\b(?!\s*[/\-]\s*\d)(?!\s*nam)", t2):
            pre.append(int(m.group(1)))
        if pre and len(out) == 1 and re.search(r"\bth\w*\s*\d{1,2}\s*,", t2):
            out = [(out[0][0], p) for p in pre] + out
        return out
    for m in re.finditer(r"\b(?:thang|th|t)\s*(\d{1,2})\s*(?:nam|/)\s*(\d{4})", t2):
        out.append((int(m.group(2)), int(m.group(1))))
    return out


def parse_period(t, asof):
    """Trả về (a, b, kind) cho MỘT kỳ, hoặc None. kind: day|week|month|ytd|quarter|range|mtd|lastn"""
    m = re.search(r"tu\s+(?:ngay\s+)?(\d{1,2})/(\d{1,2})/(\d{4}).{0,12}?(\d{1,2})/(\d{1,2})/(\d{4})", t)
    if m:
        d1, m1, y1, d2, m2, y2 = map(int, m.groups())
        return date(y1, m1, d1), date(y2, m2, d2), "range"
    m = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", t)
    if m and "ngay" in t[:m.start()][-12:]:
        d, mo, y = map(int, m.groups())
        return date(y, mo, d), date(y, mo, d), "day"
    m = re.search(r"quy\s*(\d)\s*(?:nam|/|-)?\s*(\d{4})", t)
    if m:
        q, y = int(m.group(1)), int(m.group(2))
        return date(y, 3 * q - 2, 1), month_end(y, 3 * q), "quarter"
    ms = parse_months(t)
    if ms:
        y, mo = ms[0]
        return date(y, mo, 1), month_end(y, mo), "month"
    m = re.search(r"\bthang\s*(\d{1,2})\s*nam\s*(\d{4})", t)
    if m:
        y, mo = int(m.group(2)), int(m.group(1))
        return date(y, mo, 1), month_end(y, mo), "month"
    m = re.search(r"(\d+)\s*ngay\s*(?:gan nhat|qua|vua qua)", t)
    if m:
        n = int(m.group(1))
        return asof - timedelta(days=n - 1), asof, "lastn"
    if re.search(r"tu\s*dau\s*nam|tu\s*1/1", t):
        return date(asof.year, 1, 1), asof, "ytd"
    if re.search(r"\b(hom qua|hqua|bua qua|bua hom qua)\b", t):
        d = asof - timedelta(days=1)
        return d, d, "day"
    if re.search(r"\b(hom nay|hnay|bua nay|hom ni|trong ngay)\b|ngay hom nay", t):
        return asof, asof, "day"
    if re.search(r"tuan\s*(truoc|roi|qua|vua roi)", t):
        mon = asof - timedelta(days=asof.weekday())
        return mon - timedelta(days=7), mon - timedelta(days=1), "week"
    if re.search(r"tuan\s*(nay|ni)", t):
        return asof - timedelta(days=asof.weekday()), asof, "week"
    if re.search(r"(?:thang\s*(?:nay|ni)|\bth\s*(?:nay|ni)|\bthang hien tai)|tu\s*dau\s*thang", t):
        return date(asof.year, asof.month, 1), asof, "mtd"
    return None


# ----------------------------------------------------------------- solver
def find_item(L: Ledger, t_norm: str):
    best = None
    for n, r in L.items_norm.items():
        if n in t_norm and (best is None or len(n) > len(best[0])):
            best = (n, r)
    return best[1] if best else None


def find_group(L: Ledger, t_norm: str):
    for g in L.groups:
        if norm_name(g) in t_norm:
            return g
    return None


def ranked(series: pd.Series, codes: pd.Series, k):
    df = pd.DataFrame({"v": series, "c": codes}).sort_values(["v", "c"], ascending=[False, True])
    return list(df.index[:k])


def solve(L: Ledger, question: str, asof: date):
    t = strip_acc(question)
    tn = norm_name(question)
    # ---- không trả lời được: dữ liệu không ghi
    if re.search(r"chat luong|dia chi|nha o duong|duong\s+[a-z]|gioi tinh|khach nu|khach nam|\bkenh\b|tai quay|dien thoai|"
                 r"giao tre|giao hang tre|ton kho|con lai|trong kho|con bao nhieu|gia nhap|gia von|loi nhuan|lai gop|"
                 r"nha cung cap|nhan vien|sdt|tuoi", t):
        return {"type": "unanswerable", "reason": "Dữ liệu sổ bán hàng không ghi thông tin này"}

    pct = bool(re.search(r"%|phan tram|\bpt\b", t))
    months = parse_months(t)
    nmonths = len(set(months))
    per = parse_period(t, asof)
    item = find_item(L, tn)
    group = find_group(L, tn) if re.search(r"nhom|hang\s", t) else None
    rev_kw = bool(re.search(r"doanh thu|dthu|dt\b|tien ban|thu ve|ban (?:duoc|ra) .*tien|bao nhieu tien|tong tien|nhieu tien|bao nhieu dong|"
                            r"bnhiu tien|tien hang", t))
    order_kw = bool(re.search(r"\bdon\b|\bdh\b|o dod|\bdon hang|order|hoa don", t))

    def lines_in(a, b, only_items=None, grp=None):
        X = L.vl[(L.vl.date >= a) & (L.vl.date <= b)]
        if only_items is not None:
            X = X[X["item"] == only_items]
        if grp is not None:
            X = X[X["group"] == grp]
        return X

    # ============ nhiều tháng
    if nmonths >= 2 or re.search(r"tu\s*\d{1,2}/\d{2,4}\s*(?:den|toi)\s*\d{1,2}/\d{2,4}", t):
        ms = months
        if re.search(r"(?:den|toi)", t) and len(ms) == 2 and not re.search(r"\b(?:va|,)\b", t):
            (y1, m1), (y2, m2) = ms
            ms = [add_months(y1, m1, k) for k in range((y2 * 12 + m2) - (y1 * 12 + m1) + 1)]
        ms = list(dict.fromkeys(ms))
        vals = [L.rev(date(y, m, 1), month_end(y, m)) for y, m in ms]
        if re.search(r"nao.*(?:cao|lon|nhieu).*nhat|(?:cao|lon|nhieu) nhat", t) and re.search(r"thang nao|thang", t) and not re.search(r"tang lien tuc|luon cao", t):
            i = max(range(len(vals)), key=lambda i: vals[i])
            return {"type": "date", "answer": f"{ms[i][0]}-{ms[i][1]:02d}"}
        if re.search(r"lien tuc|luon cao|thang sau .*hon|tang deu", t):
            return {"type": "boolean", "answer": all(vals[i] < vals[i + 1] for i in range(len(vals) - 1))}
        if rev_kw or re.search(r"lan luot|tung thang", t):
            return {"type": "list", "answer": [num_out(v) for v in vals]}
        return ABSTAIN

    # ============ tăng giá: so N ngày sau với N ngày trước
    m = re.search(r"(\d+)\s*ngay\s*(?:ke tu|tu)", t)
    if m and re.search(r"len gia|tang gia|doi gia", t) and item is not None:
        n = int(m.group(1))
        dm = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", t)
        if not dm:
            return ABSTAIN
        d0 = date(int(dm.group(3)), int(dm.group(2)), int(dm.group(1)))
        after = lines_in(d0, d0 + timedelta(days=n - 1), item.item).qty.sum()
        before = lines_in(d0 - timedelta(days=n), d0 - timedelta(days=1), item.item).qty.sum()
        if before == 0:
            return ABSTAIN
        return {"type": "percent", "answer": num_out((after - before) / before * 100, 2)}

    if per is None:
        return ABSTAIN
    a, b, kind = per
    if a > L.last or b < L.first:
        return {"type": "unanswerable", "reason": "Kỳ hỏi nằm ngoài khoảng ngày có dữ liệu"}

    # ============ so sánh % doanh thu
    if pct and re.search(r"so voi|so vs|hon hay kem|tang hay giam|thay doi|len hay xuong|tang|giam", t) and rev_kw and item is None and group is None:
        if kind == "mtd" or re.search(r"cung (?:ky|so ngay).*thang (?:truoc|trc)|cung ky th", t) and kind in ("mtd",):
            y, mo = add_months(a.year, a.month, -1)
            ndays = (b - a).days + 1
            pa, pb = date(y, mo, 1), min(date(y, mo, 1) + timedelta(days=ndays - 1), month_end(y, mo))
        elif re.search(r"cung ky nam (?:ngoai|truoc)|so voi.*nam truoc|cung ky.*nam", t):
            pa, pb = date(a.year - 1, a.month, 1), month_end(a.year - 1, a.month)
        elif kind == "month":
            y, mo = add_months(a.year, a.month, -1)
            pa, pb = date(y, mo, 1), month_end(y, mo)
        else:
            return ABSTAIN
        cur, prev = L.rev(a, b), L.rev(pa, pb)
        if prev == 0:
            return ABSTAIN
        return {"type": "percent", "answer": num_out((cur - prev) / prev * 100, 2)}

    # ============ hủy đơn
    if re.search(r"\bhuy\b|bi huy|da huy", t):
        mask = (L.orders.date >= a) & (L.orders.date <= b)
        allo = L.orders[mask]
        canc = int(allo.st.isin(CANCEL).sum())
        if pct and len(allo):
            return {"type": "percent", "answer": num_out(canc / len(allo) * 100, 2)}
        return {"type": "number", "answer": canc}

    # ============ ngày doanh thu cao nhất / số ngày đạt ngưỡng
    if re.search(r"ngay nao|hom nao|bua nao", t) and re.search(r"nhat|cao|dat|nhieu", t) and kind == "month":
        s = L.daily_rev(a, b)
        return {"type": "date", "answer": str(s.idxmax())} if len(s) else ABSTAIN
    thr = money(t)
    if re.search(r"may ngay|bao nhieu ngay|dem so ngay|may bua|co bnhiu ngay", t) and thr and kind in ("month",) and rev_kw:
        s = L.daily_rev(a, b)
        return {"type": "number", "answer": int((s >= thr).sum())}

    # ============ đếm khách / mặt hàng theo ngưỡng số đơn
    mN = re.search(r"(?:tu|it nhat|>=|≥)\s*(\d+)\s*(?:don|dh|dơn)", t)
    vo = L.vo[(L.vo.date >= a) & (L.vo.date <= b)]
    if mN and re.search(r"khach", t):
        n = int(mN.group(1))
        cnt = vo[~vo.is_guest].groupby("cust_key").size()
        if pct:
            return {"type": "percent", "answer": num_out((cnt >= n).sum() / len(cnt) * 100, 2)}
        return {"type": "number", "answer": int((cnt >= n).sum())}
    mN = re.search(r"(?:tu|it nhat|>=|≥|o)\s*(\d+)\s*don", t)
    if mN and re.search(r"mat hang|\bsp\b|san pham", t):
        n = int(mN.group(1))
        X = L.vl[(L.vl.date >= a) & (L.vl.date <= b)]
        cnt = X.groupby("item")["order"].nunique()
        return {"type": "number", "answer": int((cnt >= n).sum())}

    # ============ khách top
    if re.search(r"\bkhach\b|ai (?:la|mua)|ai\b", t) and re.search(r"nhat|top|\b\d+ khach", t) and item is None:
        X = vo[~vo.is_guest]
        by_rev = bool(re.search(r"tien|chi tieu|chi nhieu|gia tri", t))
        ser = X.groupby("cust_key").rev.sum() if by_rev else X.groupby("cust_key").size()
        if not len(ser):
            return ABSTAIN
        km = re.search(r"top\s*(\d+)|(\d+)\s*khach", t)
        k = int(next(g for g in km.groups() if g)) if km else 1
        spell = X.groupby("cust_key").cust.agg(lambda s: s.value_counts().index[0])
        top = ranked(ser, pd.Series(ser.index, index=ser.index), k)
        names = [spell[x] for x in top]
        return {"type": "string", "answer": names[0]} if k == 1 else {"type": "list", "answer": names}

    # ============ mặt hàng top
    if re.search(r"ban chay|ban nhieu nhat|ban duoc nhieu nhat|hot nhat|chay nhat|mat hang nao|sp nao|\bsp\b.*nhat", t) and item is None:
        X = lines_in(a, b, None, group)
        by_rev = bool(re.search(r"doanh thu|dthu|tien|thu ve", t))
        ser = X.groupby("item").amount.sum() if by_rev else X.groupby("item").qty.sum()
        codes = X.groupby("item").code.first()
        km = re.search(r"top\s*(\d+)|(\d+)\s*(?:mat hang|san pham|sp|mon)", t)
        k = int(next(g for g in km.groups() if g)) if km else 1
        top = ranked(ser, codes.reindex(ser.index), k)
        return {"type": "string", "answer": top[0]} if k == 1 else {"type": "list", "answer": top}

    # ============ số lượng theo đơn vị cơ bản (tất cả mặt hàng tính theo X)
    mu = re.search(r"(?:tinh theo|theo)\s+(\w+)|(?:bao nhieu|may)\s+(goi|chai|lon|hop|cay|kg|bao|vi|cuc|qua|cai|bo|thung|lop|binh|m3|vien|cuon)\b", t)
    if mu and item is None and group is None and not rev_kw and re.search(r"tat ca|moi mat hang|tinh het|tong cong|tong|cong", t):
        unit = next(g for g in mu.groups() if g)
        X = lines_in(a, b)
        X = X[X.base_unit.map(lambda u: strip_acc(u).strip() == unit)]
        return {"type": "number", "answer": num_out(X.qty.sum(), 2 if X.qty.sum() % 1 else 0)}

    # ============ nhóm hàng
    if group is not None and item is None:
        tot = L.rev(a, b)
        if re.search(r"chiem|ti trong|ti le|dong gop", t) and pct:
            return {"type": "percent", "answer": num_out(L.rev(a, b, L.vl[L.vl.group == group]) / tot * 100, 2)}
        if order_kw and re.search(r"nhom", t) and not rev_kw:
            X = lines_in(a, b, None, group)
            return {"type": "number", "answer": int(X["order"].nunique())}
        if rev_kw:
            return {"type": "number", "answer": num_out(L.rev(a, b, L.vl[L.vl.group == group]))}

    # ============ một mặt hàng
    if item is not None:
        X = lines_in(a, b, item.item)
        if rev_kw:
            return {"type": "number", "answer": num_out(X.amount.sum())}
        if re.search(r"bao nhieu|may|bnhiu", t):
            q = X.qty.sum()
            return {"type": "number", "answer": num_out(q, 2 if q % 1 else 0)}

    # ============ trung bình mỗi đơn
    if re.search(r"trung binh|binh quan|moi don|mot don|1 don|\bmoi o\b|tb", t) and (order_kw or rev_kw) and item is None:
        n = L.n_orders(a, b)
        return {"type": "number", "answer": num_out(L.rev(a, b) / n)} if n else ABSTAIN

    # ============ ngưỡng giá trị đơn
    if thr and order_kw and re.search(r"tro len|tu\s", t) and item is None:
        return {"type": "number", "answer": int((vo[(vo.date >= a) & (vo.date <= b)].rev >= thr).sum())}

    # ============ số đơn
    if order_kw and re.search(r"bao nhieu|may|bnhiu|so don|tong|dem", t) and not rev_kw:
        return {"type": "number", "answer": L.n_orders(a, b)}

    # ============ doanh thu
    if rev_kw or (re.search(r"ban (?:duoc|ra)", t) and re.search(r"tien", t)):
        return {"type": "number", "answer": num_out(L.rev(a, b))}
    return ABSTAIN
