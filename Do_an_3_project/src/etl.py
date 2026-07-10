"""
etl.py - ETL chuyển dữ liệu từ OLTP (coffeeshop_oltp) sang DW (coffeeshop_dw).
============================================================================
Thực hiện đúng 3 bước Extract - Transform - Load + nạp incremental + ghi log.
Chạy SAU khi: (1) chạy 02_schema_dw.sql, (2) chạy load_oltp.py.

Cách chạy:   python etl.py
Lần đầu nạp toàn bộ; các lần sau chỉ nạp đơn hàng MỚI (theo watermark).
"""
import os
import logging
import pandas as pd
from db import get_engine

# ---------- Cấu hình logging: ghi ra cả màn hình lẫn file etl.log ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.FileHandler("etl.log", encoding="utf-8"),
              logging.StreamHandler()],
)

WM_FILE = os.path.join(os.path.dirname(__file__), "watermark.txt")


# ============================ EXTRACT ============================
def read_watermark() -> int:
    """Đọc mốc transaction_id đã nạp lần trước (0 nếu chạy lần đầu)."""
    if os.path.exists(WM_FILE):
        return int(open(WM_FILE).read().strip() or 0)
    return 0


def extract(src_engine, last_id: int) -> pd.DataFrame:
    """Đọc & JOIN dữ liệu MỚI (transaction_id > last_id) từ OLTP về 1 DataFrame."""
    query = f"""
        SELECT t.transaction_id, t.transaction_date, t.transaction_time,
               ti.quantity,
               s.store_id, s.store_name, s.location,
               p.product_id, p.product_category, p.product_type,
               p.product_detail, p.unit_price
        FROM transaction_items ti
        JOIN transactions t ON ti.transaction_id = t.transaction_id
        JOIN stores   s ON t.store_id   = s.store_id
        JOIN products p ON ti.product_id = p.product_id
        WHERE t.transaction_id > {last_id}
    """
    return pd.read_sql(query, src_engine)


# ============================ TRANSFORM ============================
def transform(df: pd.DataFrame) -> pd.DataFrame:
    """Làm sạch dữ liệu + tạo các cột khóa/đo cần cho Fact."""
    n0 = len(df)

    # 1) Chuẩn hóa kiểu dữ liệu
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    df["quantity"]   = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")

    # giờ trong ngày (xử lý cả kiểu time, chuỗi 'HH:MM:SS' hay timedelta)
    df["hour"] = df["transaction_time"].apply(_get_hour)

    # 2) Chuẩn hóa text (bỏ khoảng trắng thừa)
    for c in ["product_category", "product_type", "product_detail",
              "store_name", "location"]:
        df[c] = df[c].astype(str).str.strip()

    # 3) Xử lý NULL / giá trị thiếu
    df = df.dropna(subset=["transaction_id", "product_id", "store_id",
                           "transaction_date", "hour"])
    df["quantity"]   = df["quantity"].fillna(1)
    df["unit_price"] = df["unit_price"].fillna(0)

    # 4) Loại dòng vô lý & trùng lặp
    df = df[(df["quantity"] > 0) & (df["unit_price"] > 0)]
    df = df.drop_duplicates()

    # 5) Tạo khóa & số đo cho Fact
    df["date_key"]     = df["transaction_date"].dt.strftime("%Y%m%d").astype(int)
    df["time_key"]     = df["hour"].astype(int)          # khớp DimTime (0..23)
    df["total_amount"] = df["quantity"] * df["unit_price"]

    logging.info("Transform: vao %d dong -> sach con %d dong", n0, len(df))
    return df


def _get_hour(t):
    """Lấy giờ (0-23) từ nhiều kiểu giá trị thời gian khác nhau."""
    if pd.isna(t):
        return None
    if hasattr(t, "hour"):                 # datetime.time / Timestamp
        return t.hour
    s = str(t)
    if "days" in s:                        # timedelta '0 days 08:00:00'
        s = s.split("days")[-1]
    return int(s.strip().split(":")[0])


# ============================ LOAD ============================
def upsert_dimension(engine, table, key_col, new_df):
    """Chỉ thêm vào Dimension những bản ghi CHƯA có (so theo natural key)."""
    existing = pd.read_sql(f"SELECT {key_col} FROM {table}", engine)
    to_add = new_df[~new_df[key_col].isin(existing[key_col])]
    if len(to_add):
        to_add.to_sql(table, engine, if_exists="append", index=False)
    logging.info("%s: them %d ban ghi moi", table, len(to_add))


def build_fact(df, dim_product, dim_store) -> pd.DataFrame:
    """Gắn surrogate key vào dữ liệu rồi chọn đúng cột cho FactSales."""
    df = df.merge(dim_product, on="product_id", how="left")
    df = df.merge(dim_store,   on="store_id",   how="left")
    return df[["date_key", "time_key", "product_key", "store_key",
               "transaction_id", "quantity", "unit_price", "total_amount"]]


# ============================ MAIN ============================
def main():
    logging.info("===== BAT DAU ETL =====")
    src = get_engine("coffeeshop_oltp")
    dw  = get_engine("coffeeshop_dw")

    last_id = read_watermark()
    logging.info("Watermark hien tai: transaction_id > %d", last_id)

    df = extract(src, last_id)
    logging.info("Extract: %d dong moi tu OLTP", len(df))
    if df.empty:
        logging.info("Khong co du lieu moi. Ket thuc.")
        return

    df = transform(df)

    # Nạp Dimension sản phẩm & chi nhánh (chỉ thêm cái mới)
    dim_product_src = (df[["product_id", "product_category", "product_type",
                           "product_detail", "unit_price"]]
                       .drop_duplicates("product_id"))
    dim_store_src = (df[["store_id", "store_name", "location"]]
                     .drop_duplicates("store_id"))
    upsert_dimension(dw, "DimProduct", "product_id", dim_product_src)
    upsert_dimension(dw, "DimStore",   "store_id",   dim_store_src)

    # Đọc lại để lấy surrogate key
    dimp = pd.read_sql("SELECT product_key, product_id FROM DimProduct", dw)
    dims = pd.read_sql("SELECT store_key, store_id FROM DimStore", dw)

    fact = build_fact(df, dimp, dims)
    fact.to_sql("FactSales", dw, if_exists="append", index=False, chunksize=1000)
    logging.info("Load: %d dong vao FactSales", len(fact))

    # Cập nhật watermark = transaction_id lớn nhất vừa nạp
    new_wm = int(df["transaction_id"].max())
    open(WM_FILE, "w").write(str(new_wm))
    logging.info("Cap nhat watermark = %d", new_wm)
    logging.info("===== ETL HOAN TAT =====")


if __name__ == "__main__":
    main()
