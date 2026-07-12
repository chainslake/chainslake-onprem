# Skill: Setup Metabase On-Premise

## Mô tả
Thiết lập Metabase trên môi trường on-premise: tạo admin account, kết nối database (SparkSQL/Trino), tạo API key cho automation, và sử dụng Metabase CLI (`mb`) để quản lý.

## Điều kiện áp dụng
- Metabase container đã được khởi động (port 53000)
- Truy cập lần đầu vào `http://localhost:53000` — chưa có admin account
- Cần setup lại Metabase từ đầu (reset database)
- Metabase v0.62+ (hỗ trợ Metabase CLI `mb`)

## Cài đặt Metabase CLI

```bash
# Cài đặt (cần Node.js v18+)
npm install -g @metabase/cli

# Xác minh
mb --version

# Đăng nhập
mb auth login --url http://localhost:53000 --api-key <API_KEY>

# Kiểm tra trạng thái
mb auth status
```

## Các bước thực hiện

### Bước 1: Cấu hình credentials trong `script/.env`

Script đọc tất cả credentials từ `script/.env`. **KHÔNG truyền mật khẩu qua command line.**

```bash
# Nếu chưa có script/.env, copy từ template
cp script/env_example script/.env
```

Chỉnh sửa `script/.env` với thông tin thực tế:

```env
METABASE_URL=http://localhost:53000
METABASE_EMAIL=admin@chainslake.com
METABASE_PASSWORD=<your_password_here>
METABASE_SITE_NAME=Chainslake Warehouse
```

### Bước 2: Chạy script setup

```bash
python script/setup_metabase.py
```

Script tự động:
1. Đợi Metabase ready (kiểm tra `/api/health`)
2. Tạo admin account qua `/api/setup` API
3. Tạo API key và ghi vào `query/.env`
4. Thêm SparkSQL database connection
5. Thêm Trino database connection (nếu Starburst driver available)
6. Authenticate Metabase CLI (`mb auth login`)

**Tham số tuỳ chọn:**
```bash
python script/setup_metabase.py --skip-databases    # Bỏ qua thêm database
python script/setup_metabase.py --skip-cli          # Bypass CLI auth
python script/setup_metabase.py --api-key-file path/to/.env  # Đổi nơi ghi API key
```

### Bước 2: Sử dụng Metabase CLI để quản lý

```bash
# Liệt kê databases
mb db list

# Xem chi tiết database
mb db get <db-id>

# Đồng bộ schema
mb db sync-schema <db-id>

# Quét lại field values
mb db rescan-values <db-id>

# Liệt kê schemas
mb db schemas <db-id>

# Liệt kê tables trong schema
mb db schema-tables <db-id> <schema-name>

# Liệt kê cards (questions/models/metrics)
mb card list

# Liệt kê dashboards
mb dashboard list

# Liệt kê collections
mb collection list

# Tìm kiếm nội dung
mb search <query>

# Xem settings
mb setting get <key>
```

### Bước 3: Kiểm tra kết quả

1. Truy cập `http://localhost:53000` — login bằng admin credentials
2. Vào **Settings → Admin → Databases** — kiểm tra Spark/Trino đã được thêm
3. File `query/.env` đã có `METABASE_API_KEY=...`

## Lưu ý / Gotchas

### API `/api/setup` — Metabase v0.62.x format
Metabase v0.62.x OSS **không hỗ trợ** `MB_CONFIG_FILE` (chỉ Pro/Enterprise).
Endpoint `/api/setup` yêu cầu format đặc biệt:

```json
{
  "token": "<setup-token từ /api/session/properties>",
  "user": {"email": "...", "first_name": "...", "last_name": "...", "password": "..."},
  "prefs": {"site_name": "...", "site_locale": "en"},
  "database": null
}
```

**Sai thường gặp:**
- Gửi `email` ở root level → lỗi `"email": ["should be a string, received: nil"]`
- Dùng `invited_email` ở root level → cùng lỗi trên
- Password quá yếu (ví dụ `admin123456`) → lỗi `"password is too common"`
- Gửi `password` ở root level thay vì trong `user` object → lỗi nil

### Trino connection
Starburst Metabase driver yêu cầu SSL. Nếu server Trino local không bật SSL:
- Lỗi `"TLS/SSL is required for authentication with username and password"`
- Set `ssl: true, insecure: true` trong details
- Nếu vẫn fail (lỗi SSL message), skip Trino — SparkSQL đủ dùng

### API Key
- Endpoint: `POST /api/api-key` (cần session token)
- Key trả về 1 lần duy nhất qua `unmasked_key`
- Ghi ngay vào `query/.env`

### Metabase CLI (`mb`)
- Yêu cầu Metabase v0.58+ (hiện tại v0.62.4.3)
- `mb auth login` hỗ trợ API key hoặc browser OAuth (v0.62+)
- CLI không hỗ trợ `db create` — dùng API `/api/database` để thêm database
- CLI hỗ trợ: list/get/sync/rescan cho databases; CRUD cho cards, dashboards, collections
- Output mặc định là text, thêm `--json` để lấy JSON
- Dùng `mb skills get core` để xem conventions chi tiết

## Ví dụ thực tế
- Ngày: 2026-07-12
- Metabase v0.62.4.3 OSS
- Metabase CLI v0.2.1
- Setup thành công với user nested object format
- SparkSQL: OK, Trino: OK
- CLI authenticated và hoạt động bình thường
