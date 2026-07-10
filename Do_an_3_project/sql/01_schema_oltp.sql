/* =====================================================================
   ĐỒ ÁN 3 - CHỦ ĐỀ 2 | Bước 1a: Tạo CSDL OLTP (mô phỏng app cà phê)
   Chạy file này TRƯỚC trong SSMS (mở New Query -> dán -> Execute / F5)
   ===================================================================== */

-- 1) Tạo database nguồn (nếu đã có thì xóa tạo lại)
IF DB_ID('coffeeshop_oltp') IS NOT NULL
BEGIN
    ALTER DATABASE coffeeshop_oltp SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE coffeeshop_oltp;
END
GO
CREATE DATABASE coffeeshop_oltp;
GO
USE coffeeshop_oltp;
GO

-- 2) Bảng chi nhánh
CREATE TABLE stores (
    store_id   INT PRIMARY KEY,
    store_name NVARCHAR(100),
    location   NVARCHAR(100)
);

-- 3) Bảng sản phẩm
CREATE TABLE products (
    product_id       INT PRIMARY KEY,
    product_category NVARCHAR(50),
    product_type     NVARCHAR(50),
    product_detail   NVARCHAR(100),
    unit_price       DECIMAL(10,2)
);

-- 4) Bảng hóa đơn (phần "đầu" của giao dịch)
CREATE TABLE transactions (
    transaction_id   INT PRIMARY KEY,
    transaction_date DATE,
    transaction_time TIME,
    store_id INT FOREIGN KEY REFERENCES stores(store_id)
);

-- 5) Bảng dòng sản phẩm trong hóa đơn
CREATE TABLE transaction_items (
    item_id        INT IDENTITY(1,1) PRIMARY KEY,
    transaction_id INT FOREIGN KEY REFERENCES transactions(transaction_id),
    product_id     INT FOREIGN KEY REFERENCES products(product_id),
    quantity       INT
);
GO

PRINT 'OK: Da tao database coffeeshop_oltp va 4 bang. Tiep theo chay load_oltp.py de nap du lieu.';
GO
