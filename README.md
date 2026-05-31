# RESTAURANT MANAGEMENT !
=IF(C2<>"",C2 & " - " & D2,LOOKUP(2,1/(C$2:C2<>""),C$2:C2) & " - " & D2)
=IF(C2<>"";C2 & " - " & D2;LOOKUP(2;1/(C$2:C2<>"");C$2:C2) & " - " & D2)
# Tech Stack

-   Architecture: 3-layer
-   Winform: Guna2 Framework for UI
-   Library: Google OR Tools
-   Design Pattern: Singleton

## Git flow

## Git Flow

### 1. Get a Task

1. Switch to develop:
    ```bash
    git checkout develop
    git pull origin develop
    ```
2. Create feature branch:
    ```bash
    git checkout -b feature/new-feature
    ```

### 2. In Development

-   Loop to add and commit:

    ```bash
    while true; do
        git add .
        git commit -m "Add new feature..."

        git fetch origin
        git rebase origin/develop
        if CONFLICT
            fix conflict
            git add .
            git rebase --continue
    done
    ```

### 3. Finished

1. Push feature branch:
    ```bash
    git push origin feature/new-feature
    ```
2. Create Pull Request and wait for review.
3. Delete local branch:
    ```bash
    git branch -d feature/new-feature
    ```

### WARMING

-   Cấm tuyệt đối dùng --force
-   Cấm tuyệt đối dùng --force
-   Cấm tuyệt đối dùng --force

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
| FlowLayoutPanel  | flp     | flpMain        |
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
