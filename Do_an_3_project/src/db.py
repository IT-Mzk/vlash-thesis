"""
db.py - Cấu hình kết nối tới SQL Server.
=========================================
CHỈ CẦN SỬA biến SERVER bên dưới cho đúng máy của bạn, các file khác dùng chung.

Cách tìm tên SERVER:
- Mở SSMS, ở ô "Server name" lúc Connect hiện gì thì điền y hệt vào đây.
- Thường là:  localhost\\SQLEXPRESS   hoặc   .\\SQLEXPRESS   hoặc   (local)
"""
import urllib
from sqlalchemy import create_engine

# >>>>>>>>>>>>>>>>>>  SỬA Ở ĐÂY NẾU CẦN  <<<<<<<<<<<<<<<<<<
SERVER = r"localhost\SQLEXPRESS"      # tên SQL Server instance
DRIVER = "ODBC Driver 17 for SQL Server"   # đổi thành 18 nếu bạn cài driver 18
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


def get_engine(database: str):
    """Trả về SQLAlchemy engine kết nối tới 1 database (Windows Authentication)."""
    params = urllib.parse.quote_plus(
        f"DRIVER={{{DRIVER}}};"
        f"SERVER={SERVER};"
        f"DATABASE={database};"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )
    return create_engine(f"mssql+pyodbc:///?odbc_connect={params}", fast_executemany=True)
