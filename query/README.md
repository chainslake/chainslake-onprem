# Query Scripts

Bộ script Python để tương tác với Data Warehouse thông qua Metabase API.

## Cài đặt

### 1. Cài đặt thư viện

```bash
pip install requests python-dotenv
```

### 2. Cấu hình API Key

Tạo file `.env` trong cùng thư mục với nội dung:

```
METABASE_API_KEY=<API key của bạn>
```

Để tạo API key, truy cập: `http://localhost:53000/admin/settings/authentication`

---

## Scripts

### `get_example_table.py` — Lấy bản ghi mẫu từ bảng

Truy vấn 1 bản ghi từ bảng để xem schema và dữ liệu mẫu.

**Cú pháp:**
```bash
python get_example_table.py <tên_bảng>
```

**Ví dụ:**
```bash
python get_example_table.py ethereum.transactions
```

**Kết quả trả về:**
```json
{
  "rows": [["0xabc...", 1234567, ...]],
  "cols": [
    {"name": "hash", "type": "type/Text"},
    {"name": "block_number", "type": "type/BigInteger"}
  ]
}
```

---

### `query_table.py` — Thực thi câu truy vấn SQL

Thực thi câu truy vấn SELECT trên Data Warehouse. Script sẽ:
- **Chặn** các câu truy vấn có thể thay đổi dữ liệu (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `TRUNCATE`, `ALTER`, `CREATE`, `REPLACE`, `MERGE`)
- **Yêu cầu** câu truy vấn phải có mệnh đề `LIMIT`

**Cú pháp:**
```bash
python query_table.py "<câu_truy_vấn_SQL>"
```

**Ví dụ:**
```bash
python query_table.py "SELECT * FROM ethereum.transactions LIMIT 10"
python query_table.py "SELECT hash, block_number FROM ethereum.transactions WHERE block_number > 1000000 LIMIT 50"
```

**Lỗi khi thiếu LIMIT:**
```
Lỗi: Câu truy vấn phải có mệnh đề LIMIT để giới hạn số bản ghi trả về.
Ví dụ: SELECT * FROM ethereum.transactions LIMIT 100
```

**Lỗi khi dùng lệnh destructive:**
```
Lỗi: Câu truy vấn chứa lệnh 'DROP' có thể thay đổi dữ liệu và bị chặn.
Chỉ cho phép các câu truy vấn SELECT (read-only).
```

---

### `drop_table.py` — Xóa bảng

Xóa một bảng khỏi Data Warehouse. Script yêu cầu xác nhận trước khi thực hiện để tránh xóa nhầm.

**Cú pháp:**
```bash
python drop_table.py <tên_bảng>
```

**Ví dụ:**
```bash
python drop_table.py ethereum.transactions
```

**Quy trình xác nhận:**
```
Bạn có chắc chắn muốn xóa bảng 'ethereum.transactions'? Nhập tên bảng để xác nhận: ethereum.transactions
Đã xóa bảng 'ethereum.transactions' thành công.
```

Nếu nhập sai tên bảng, thao tác sẽ bị hủy:
```
Bạn có chắc chắn muốn xóa bảng 'ethereum.transactions'? Nhập tên bảng để xác nhận: abc
Xác nhận không khớp. Hủy thao tác xóa bảng.
```

---

### `check_table_properties.py` — Kiểm tra properties của bảng

Hiển thị tblproperties của bảng trên Data Warehouse. Đặc biệt useful khi kiểm tra trạng thái lock và phạm vi dữ liệu.

**Cú pháp:**
```bash
python check_table_properties.py <tên_bảng>
```

**Ví dụ:**
```bash
python check_table_properties.py ethereum.blocks
```

**Kết quả trả về:**
```
=== tblproperties của 'ethereum.blocks' ===

Property                        Value
--------------------------------------------------------------------------------
isLock                          0
frequenceType                   block
fromBlock                       12345678
toBlock                         12345999

=== Property quan trọng ===

  isLock (ĐÃ MỞ KHÓA): 0
  frequenceType: block
  fromBlock: 12345678
  toBlock: 12345999
```

**Các property quan trọng:**
| Property | Mô tả |
|---|---|
| `isLock` | Trạng thái khóa: 1 = bị khóa (job đang ghi), 0 = mở khóa |
| `frequenceType` | Loại tần suất: `block`, `hour`, `minute`, `day` |
| `fromBlock`, `toBlock` | Phạm vi block hiện có (nếu frequenceType=block) |
| `fromEpochSecond`, `toEpochSecond` | Phạm vi epoch second hiện có (nếu frequenceType là minute/hour/day) |

---

### `unlock_table.py` — Mở khóa bảng

Mở khóa bảng khi job bị lỗi "Table is Lock". Yêu cầu xác nhận trước khi thực hiện.

**⚠️ Lưu ý:** Chỉ sử dụng khi chắc chắn không còn job nào đang ghi dữ liệu vào bảng.

**Cú pháp:**
```bash
python unlock_table.py <tên_bảng>
```

**Ví dụ:**
```bash
python unlock_table.py ethereum.blocks
```

**Quy trình xác nhận:**
```
⚠️  Bạn sắp mở khóa bảng 'ethereum.blocks'.
    Lệnh sẽ thực thi: ALTER TABLE ethereum.blocks SET TBLPROPERTIES (isLock=0)

Nhập tên bảng để xác nhận: ethereum.blocks
✅ Đã mở khóa bảng 'ethereum.blocks' thành công.
```

### `insert_dev_data.py` — Insert data vào bảng `_dev`

Insert dữ liệu vào bảng có hậu tố `_dev` để phục vụ testing (thêm dữ liệu edge case, chuẩn bị dữ liệu test...). Script **CHỈ cho phép** insert vào bảng `_dev` — bảng production sẽ bị chặn. Nếu câu INSERT dạng `SELECT` thì **bắt buộc phải có `LIMIT`**.

**Cú pháp:**
```bash
python insert_dev_data.py "<câu_INSERT_SQL>"
python insert_dev_data.py -f insert.sql
```

**Ví dụ:**
```bash
# Insert theo VALUES
python insert_dev_data.py "INSERT INTO ethereum.transactions_dev (hash, block_number) VALUES ('0xabc', 123)"

# Insert từ SELECT (bắt buộc có LIMIT)
python insert_dev_data.py "INSERT INTO ethereum.transactions_dev SELECT * FROM ethereum.transactions_dev LIMIT 10"

# Insert Overwrite (bắt buộc có LIMIT nếu dùng SELECT)
python insert_dev_data.py "INSERT OVERWRITE ethereum.transactions_dev SELECT * FROM ethereum.transactions_dev LIMIT 10"
```

**Lỗi khi insert vào bảng production (không có `_dev`):**
```
Lỗi: Bảng đích 'ethereum.transactions' không có hậu tố _dev. CHỈ cho phép insert vào bảng _dev để bảo vệ production.
```

**Lỗi khi INSERT dạng SELECT thiếu LIMIT:**
```
Lỗi: Câu INSERT dạng SELECT phải có mệnh đề LIMIT để giới hạn số bản ghi.
```

---

### `set_table_property.py` — Set properties của bảng `_dev`

Set TBLPROPERTIES cho bảng có hậu tố `_dev` để phục vụ testing (điều chỉnh `fromBlock`, `toBlock`, `isLock`, `frequenceType`...). Script **CHỈ cho phép** set trên bảng `_dev` — bảng production sẽ bị chặn.

**Cú pháp:**
```bash
python set_table_property.py "<câu_ALTER_SQL>"
python set_table_property.py -f set_props.sql
```

**Ví dụ:**
```bash
# Set fromBlock
python set_table_property.py "ALTER TABLE ethereum.transactions_dev SET TBLPROPERTIES (fromBlock=1000)"

# Set nhiều properties
python set_table_property.py "ALTER TABLE ethereum.transactions_dev SET TBLPROPERTIES (fromBlock=1000, toBlock=2000)"
```

**Lỗi khi set trên bảng production (không có `_dev`):**
```
Lỗi: Bảng đích 'ethereum.transactions' không có hậu tố _dev. CHỈ cho phép set properties trên bảng _dev để bảo vệ production.
```

---

## Cấu trúc project

```
query/
├── .env                      # Biến môi trường (API key) — không commit lên git
├── env_example               # File mẫu cấu hình .env
├── metabase_query.py         # Module lõi gọi Metabase API
├── get_example_table.py      # Lấy bản ghi mẫu từ bảng
├── query_table.py            # Thực thi câu truy vấn SQL (read-only)
├── drop_table.py             # Xóa bảng (có xác nhận)
├── check_table_properties.py # Kiểm tra tblproperties của bảng
├── unlock_table.py           # Mở khóa bảng (set isLock=0)
├── insert_dev_data.py        # Insert data vào bảng _dev (chỉ _dev)
└── set_table_property.py     # Set TBLPROPERTIES bảng _dev (chỉ _dev)
```
