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

## Cấu trúc project

```
query/
├── .env                  # Biến môi trường (API key) — không commit lên git
├── env_example           # File mẫu cấu hình .env
├── metabase_query.py     # Module lõi gọi Metabase API
├── get_example_table.py  # Lấy bản ghi mẫu từ bảng
├── query_table.py        # Thực thi câu truy vấn SQL (read-only)
└── drop_table.py         # Xóa bảng (có xác nhận)
```
