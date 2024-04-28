# RESTAURANT MANAGEMENT !

# Tech Stack

-   Architecture: 3-layer
-   Winform: Guna2 Framework for UI
-   Library: Google OR Tools
-   Design Pattern: Singleton

## Git flow

-   git pull
-   git add .
-   git commit -m "message"
-   git push
-   solve conflict

## Naming Convention

#Naming conventions For All Winforms Control

| Control Type     | Prefix  | Example        |
| ---------------- | ------- | -------------- |
| Button           | btn     | btnSubmit      |
| Label            | lbl     | lblUsername    |
| TextBox          | txt     | txtFirstName   |
| DataGridView     | dgv     | dgvStudents    |
| ComboBox         | cbo     | cboCountry     |
| ListBox          | lst     | lstItems       |
| CheckBox         | chk     | chkRememberMe  |
| RadioButton      | rdo     | rdoMale        |
| PictureBox       | pic     | picProfile     |
| DateTimePicker   | dtp     | dtpDOB         |
| Panel            | pnl     | pnlMain        |
| NumericUpDown    | num     | numQuantity    |
| GroupBox         | grp     | grpOptions     |
| TabControl       | tab     | tabMain        |
| TabPage          | tabPage | tabPageGeneral |
| MenuStrip        | mnu     | mnuFile        |
| ContextMenuStrip | cms     | cmsOptions     |
| ToolStrip        | ts      | tsMain         |
| StatusStrip      | sts     | stsMain        |

#Naming conventions for class variables and other elements

| Element         | Prefix/Suffix | Example                     |
| --------------- | ------------- | --------------------------- |
| Class Variable  | \_camelCase   | \_firstName, \_lastName     |
| Private Field   | \_camelCase   | \_age, \_isActivated        |
| Public Property | CamelCase     | FirstName, LastName         |
| Constant        | UPPER_CASE    | MAX_LENGTH, PI              |
| Local Variable  | camelCase     | firstName, lastName         |
| Method          | PascalCase    | CalculateTotal, PrintReport |
| Interface       | I_PascalCase  | IShape, IAccount            |
| Enumeration     | PascalCase    | LogLevel, ErrorCode         |
| Event           | EventName     | ButtonClicked, FormClosed   |
| Parameter       | camelCase     | username, itemCount         |

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
