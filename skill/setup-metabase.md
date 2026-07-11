# Skill: Setup Metabase On-Premise

## Mô tả
Thiết lập Metabase trên môi trường on-premise: tạo admin account, kết nối database (SparkSQL/Trino), tạo API key cho automation.

## Điều kiện áp dụng
- Metabase container đã được khởi động (port 53000)
- Truy cập第一次 vào `http://localhost:53000` — chưa có admin account
- Cần setup lại Metabase từ đầu (reset database)

## Các bước thực hiện

### Bước 1: Dùng script `setup_metabase.py`

```bash
python script/setup_metabase.py
```

Script tự động:
1. Đợi Metabase ready (kiểm tra `/api/health`)
2. Tạo admin account qua `/api/setup` API
3. Tạo API key và ghi vào `query/.env`
4. Thêm SparkSQL database connection
5. Thêm Trino database connection (nếu Starburst driver available)

**Tham số tuỳ chọn:**
```bash
python script/setup_metabase.py \
    --url http://localhost:53000 \
    --email admin@chainslake.com \
    --password "Ch@insl4ke2026!" \
    --site-name "Chainslake Warehouse" \
    --skip-databases \
    --api-key-file query/.env
```

### Bước 2: Kiểm tra kết quả

1. Truy cập `http://localhost:53000` — login bằng admin credentials
2. Vào **Settings → Admin → Databases** — kiểm tra Spark/Trino đã được thêm
3. File `query/.env` đã có `METABASE_API_KEY=...`

## Lưu ý / Gotchas

### API `/api/setup` — Metabase v0.50.x format
Metabase v0.50.x OSS **không hỗ trợ** `MB_CONFIG_FILE` (chỉ Pro/Enterprise).
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

## Ví dụ thực tế
- Ngày: 2026-07-11
- Metabase v0.50.16 OSS
- Setup thành công với user nested object format
- SparkSQL: OK, Trino: FAIL (SSL requirement)
