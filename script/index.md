# Script Index

Thư mục này chứa các Python script do Agent tự viết để phục vụ các tác vụ lặp lại hoặc cần tool đặc biệt.

> **Hướng dẫn cho Agent**: Trước khi viết script mới, kiểm tra index này để tránh trùng lặp. Sau khi viết script mới, cập nhật index này ngay lập tức.

> **Cấu hình credentials**: Tất cả credentials nằm trong `script/.env` (gitignored). Copy `script/env_example` thành `script/.env` và điền thông tin thực tế.

---

## check_rpcs.py
- **Mục đích**: Kiểm tra danh sách RPC của bất kỳ EVM chain nào từ chainlist.org. Xác nhận từng RPC có hỗ trợ đầy đủ 3 API cần thiết (eth_blockNumber, eth_getBlockByNumber, eth_getBlockReceipts) và in ra chuỗi `<ENV_VAR>=...` để dán vào `.env`.
- **Input**:
  - Positional: `chain` — chain ID (số, ví dụ `56`) hoặc tên chain (substring, ví dụ `"BNB Smart Chain Mainnet"`)
  - `--timeout` — timeout mỗi request (giây, mặc định 10)
  - `--workers` — số luồng song song (mặc định 10)
  - `--env-var` — tên biến môi trường output (mặc định: tự suy từ tên chain, ví dụ `BNB_RPCS`)
- **Output**: PASS/FAIL từng RPC + dòng `<ENV_VAR>=<rpc1,rpc2,...>` để copy vào `chainslake-run/.env`
- **Ví dụ**:
  - `python script/check_rpcs.py 56`
  - `python script/check_rpcs.py 1 --env-var ETHEREUM_RPCS`

---

## setup_metabase.py
- **Mục đích**: Thiết lập Metabase on-premise từ đầu: tạo admin account, tạo API key, thêm SparkSQL/Trino database connections.
- **Config**: Đọc từ `script/.env` — `METABASE_URL`, `METABASE_EMAIL`, `METABASE_PASSWORD`, `METABASE_SITE_NAME`
- **Input**:
  - `--skip-databases` — Bỏ qua bước thêm database
  - `--api-key-file` — Đường dẫn ghi file `.env` chứa API key (mặc định: `query/.env`)
- **Output**: Admin account, API key trong `query/.env`, database connections
- **Ví dụ**:
  - `python script/setup_metabase.py`
  - `python script/setup_metabase.py --skip-databases`

---

## trigger_dag.py
- **Mục đích**: Trigger và theo dõi Airflow DAG run. Hỗ trợ cancel, check status, monitor tiến trình real-time.
- **Config**: Đọc từ `script/.env` — `AIRFLOW_URL`, `AIRFLOW_USERNAME`. Password đọc từ file (mặc định: `chainslake/airflow/standalone_admin_password.txt`).
- **Input**:
  - Positional: `dag_id` — Tên DAG (ví dụ `Ethereum`)
  - `--password-file` — Đường dẫn file chứa admin password
  - `--cancel-all` — Cancel tất cả runs đang chạy/queued
  - `--status` — Xem status các DAG runs gần nhất
  - `--no-wait` — Trigger rồi thoát ngay
  - `--poll-interval` — Thời gian poll (giây, mặc định 30)
  - `--max-wait` — Thời gian chờ tối đa (giây, mặc định 3600)
- **Output**: Trigger DAG, hiển thị task states real-time, trả exit code 0 nếu success
- **Ví dụ**:
  - `python script/trigger_dag.py Ethereum`
  - `python script/trigger_dag.py Ethereum --status`
  - `python script/trigger_dag.py Ethereum --cancel-all`
