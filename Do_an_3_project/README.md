# Đồ án 3 — Chủ đề 2: Data & Analytics (Chuỗi quán cà phê)

Bộ code chạy được cho 3 bước: Data Warehouse (SQL Server) · ETL (Python) · Power BI.

## Chạy theo đúng thứ tự
1. **SSMS** → chạy `sql/01_schema_oltp.sql` rồi `sql/02_schema_dw.sql`
2. Sửa tên SERVER trong `src/db.py` (nếu cần) → `pip install -r requirements.txt`
3. `cd src` → `python load_oltp.py`  (nạp CSV vào OLTP)
4. `python etl.py`  (ETL: OLTP → DW, có log + incremental)
5. **Power BI** → kết nối `coffeeshop_dw` → dán measures từ `dax_measures.txt` → dựng dashboard

👉 Xem chi tiết từng bước trong file **Huong_dan_cai_dat_va_chay.docx**.

## Cấu trúc
```
data/coffee_shop_sales.csv   Dữ liệu mẫu (~18.000 dòng)
sql/01_schema_oltp.sql       Tạo DB OLTP + 4 bảng
sql/02_schema_dw.sql         Tạo DW + 5 bảng (Star Schema) + DimDate/DimTime
src/db.py                    Cấu hình kết nối SQL Server
src/load_oltp.py             Nạp CSV vào OLTP
src/etl.py                   ETL OLTP → DW
dax_measures.txt             6+ công thức DAX cho Power BI
```
