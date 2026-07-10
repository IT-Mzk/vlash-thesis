"""
load_oltp.py - Nạp dữ liệu mẫu (CSV phẳng) vào database OLTP coffeeshop_oltp.
============================================================================
Đây là bước MÔ PHỎNG "app cà phê ghi dữ liệu vào database của nó".
Chạy SAU khi đã chạy sql/01_schema_oltp.sql trong SSMS.

Cách chạy:   python load_oltp.py
"""
import os
import logging
import pandas as pd
from db import get_engine

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(levelname)s | %(message)s")

# Đường dẫn file CSV (mặc định: ../data/coffee_shop_sales.csv)
CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "coffee_shop_sales.csv")


def build_oltp_frames(df: pd.DataFrame):
    """Tách bảng phẳng thành 4 bảng chuẩn hóa của OLTP.
    Trả về (stores, products, transactions, transaction_items)."""
    # 1) stores: mỗi chi nhánh 1 dòng
    stores = (df[["store_id", "store_location"]]
              .drop_duplicates("store_id")
              .rename(columns={"store_location": "store_name"}))
    stores["location"] = stores["store_name"]
    stores = stores[["store_id", "store_name", "location"]]

    # 2) products: mỗi sản phẩm 1 dòng
    products = (df[["product_id", "product_category", "product_type",
                    "product_detail", "unit_price"]]
                .drop_duplicates("product_id"))

    # 3) transactions: phần đầu hóa đơn (mỗi transaction_id 1 dòng)
    transactions = (df[["transaction_id", "transaction_date",
                        "transaction_time", "store_id"]]
                    .drop_duplicates("transaction_id"))

    # 4) transaction_items: từng dòng sản phẩm (KHÔNG kèm item_id vì là IDENTITY)
    transaction_items = (df[["transaction_id", "product_id", "transaction_qty"]]
                         .rename(columns={"transaction_qty": "quantity"}))

    return stores, products, transactions, transaction_items


def main():
    logging.info("Doc file CSV: %s", os.path.abspath(CSV_PATH))
    df = pd.read_csv(CSV_PATH)
    logging.info("Doc duoc %s dong san pham", f"{len(df):,}")

    stores, products, transactions, transaction_items = build_oltp_frames(df)
    logging.info("stores=%d, products=%d, transactions=%d, items=%d",
                 len(stores), len(products), len(transactions), len(transaction_items))

    engine = get_engine("coffeeshop_oltp")
    # Nạp theo thứ tự khóa ngoại: stores & products -> transactions -> items
    stores.to_sql("stores", engine, if_exists="append", index=False)
    products.to_sql("products", engine, if_exists="append", index=False)
    transactions.to_sql("transactions", engine, if_exists="append", index=False)
    transaction_items.to_sql("transaction_items", engine, if_exists="append",
                             index=False, chunksize=1000)

    logging.info("HOAN TAT: da nap du lieu vao coffeeshop_oltp.")


if __name__ == "__main__":
    main()
