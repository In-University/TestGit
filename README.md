# RESTAURANT MANAGEMENT !

# Tech Stack

-   Architecture: 3-layer
-   Winform: Guna2 Framework for UI
-   Library: Google OR Tools
-   Design Pattern: Singleton

## Git flow

-   git pull
-   solve conflict (nếu xảy ra)
-   git add .
-   git commit -m "message"
-   git push
-   solve conflict (nếu xảy ra) thì lặp lại từ đầu

## **Explain function**

**1. DataProvider Class**

-   **ExcuteQuery**: dùng cho câu lệnh **SELECT** trả về kết quả dạng DataTable
-   **ExcuteNonQuery**: dùng cho câu lệnh **INSERT, UPDATE, DELETE** trả về kết quả dạng **bool**
-   **ExcuteScalar**: trả về dạng số (dùng với **AVG, COUNT, SUM**, ...)
    _Giải thích tham số_
    **_- Ví dụ với ExcuteQuery_**
    > public DataTable ExecuteQuery(string query, SqlParameter[] parameters = null)
-   Cách 1: Không truyền parameter:
    > dataProvider.ExcuteQuery("SELECT \* FROM Employee)
-   Cách 2: Truyền parameter:
    > string query = "SELECT \* FROM NhanVien WHERE MaNhanVien = @MaNV OR MaNhanVien = @MaNV2"
    > SqlParameter[] sqlParameters = new SqlParameter[] {
    > new SqlParameter("@MaNV", MaNV),
    > new SqlParameter("@MaNV2", MaNV2) };  
    > return dataProvider.ExecuteQuery(query , sqlParameters);
