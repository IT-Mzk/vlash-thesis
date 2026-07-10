/* =====================================================================
   ĐỒ ÁN 3 - CHỦ ĐỀ 2 | Bước 1b: Tạo Data Warehouse (Star Schema)
   Chạy file này SAU 01_schema_oltp.sql.
   - Tạo 5 bảng: DimDate, DimTime, DimProduct, DimStore, FactSales
   - Sinh sẵn dữ liệu cho DimDate (01-06/2023) và DimTime (0-23h)
   - DimProduct, DimStore, FactSales sẽ được etl.py nạp vào.
   ===================================================================== */

IF DB_ID('coffeeshop_dw') IS NOT NULL
BEGIN
    ALTER DATABASE coffeeshop_dw SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE coffeeshop_dw;
END
GO
CREATE DATABASE coffeeshop_dw;
GO
USE coffeeshop_dw;
GO

/* ---------- DIMENSION: NGÀY ---------- */
CREATE TABLE DimDate (
    date_key     INT PRIMARY KEY,      -- dạng yyyymmdd, vd 20230115
    full_date    DATE,
    day          INT,
    month        INT,
    month_name   NVARCHAR(20),
    quarter      INT,
    year         INT,
    day_of_week  INT,
    weekday_name NVARCHAR(20),
    is_weekend   BIT
);

/* ---------- DIMENSION: GIỜ ---------- */
CREATE TABLE DimTime (
    time_key  INT PRIMARY KEY,         -- = giờ 0..23
    hour      INT,
    day_part  NVARCHAR(20)             -- Sang / Trua / Chieu / Toi
);

/* ---------- DIMENSION: SẢN PHẨM (surrogate key) ---------- */
CREATE TABLE DimProduct (
    product_key      INT IDENTITY(1,1) PRIMARY KEY,
    product_id       INT,              -- natural key (mã gốc từ app)
    product_category NVARCHAR(50),
    product_type     NVARCHAR(50),
    product_detail   NVARCHAR(100),
    unit_price       DECIMAL(10,2)
);

/* ---------- DIMENSION: CHI NHÁNH (surrogate key) ---------- */
CREATE TABLE DimStore (
    store_key  INT IDENTITY(1,1) PRIMARY KEY,
    store_id   INT,                    -- natural key
    store_name NVARCHAR(100),
    location   NVARCHAR(100)
);

/* ---------- FACT: BÁN HÀNG ---------- */
CREATE TABLE FactSales (
    sales_key      BIGINT IDENTITY(1,1) PRIMARY KEY,
    date_key       INT FOREIGN KEY REFERENCES DimDate(date_key),
    time_key       INT FOREIGN KEY REFERENCES DimTime(time_key),
    product_key    INT FOREIGN KEY REFERENCES DimProduct(product_key),
    store_key      INT FOREIGN KEY REFERENCES DimStore(store_key),
    transaction_id INT,
    quantity       INT,
    unit_price     DECIMAL(10,2),
    total_amount   DECIMAL(12,2)       -- = quantity * unit_price
);
GO

/* ---------- Sinh dữ liệu DimTime (24 giờ) ---------- */
DECLARE @h INT = 0;
WHILE @h <= 23
BEGIN
    INSERT INTO DimTime(time_key, hour, day_part)
    VALUES (@h, @h,
        CASE WHEN @h BETWEEN 6 AND 10 THEN N'Sang'
             WHEN @h BETWEEN 11 AND 13 THEN N'Trua'
             WHEN @h BETWEEN 14 AND 16 THEN N'Chieu'
             ELSE N'Toi' END);
    SET @h = @h + 1;
END
GO

/* ---------- Sinh dữ liệu DimDate (01/01/2023 - 30/06/2023) ---------- */
DECLARE @d DATE = '2023-01-01';
WHILE @d <= '2023-06-30'
BEGIN
    INSERT INTO DimDate VALUES (
        YEAR(@d)*10000 + MONTH(@d)*100 + DAY(@d),
        @d, DAY(@d), MONTH(@d), DATENAME(MONTH,@d),
        DATEPART(QUARTER,@d), YEAR(@d),
        DATEPART(WEEKDAY,@d), DATENAME(WEEKDAY,@d),
        IIF(DATEPART(WEEKDAY,@d) IN (1,7), 1, 0)
    );
    SET @d = DATEADD(DAY,1,@d);
END
GO

/* ---------- Index cho các khóa ngoại của Fact (tăng tốc truy vấn) ---------- */
-- (Chạy SAU khi etl.py đã nạp FactSales; nếu chạy trước cũng không lỗi)
-- CREATE INDEX ix_fact_date    ON FactSales(date_key);
-- CREATE INDEX ix_fact_time    ON FactSales(time_key);
-- CREATE INDEX ix_fact_product ON FactSales(product_key);
-- CREATE INDEX ix_fact_store   ON FactSales(store_key);

PRINT 'OK: Da tao coffeeshop_dw + 5 bang. DimDate & DimTime da co du lieu. Tiep theo chay etl.py.';
GO
