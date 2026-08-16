---
name: deploy-new-tables
description: Triển khai các bảng/job mới từ môi trường dev (_dev suffix) lên production — bỏ suffix _dev, reset properties, dọn _dev tables, chạy UAT 5 ngày, thêm vào DAG
---

# Skill: Deploy New Tables

## Mô tả
Hướng dẫn triển khai các bảng/job đã hoàn thành vòng lặp DEV-TEST từ bảng `_dev` lên production: chuẩn bị code bỏ `_dev`, reset properties, dọn dẹp `_dev` tables, tạo UAT.md, chạy thử 5 ngày dữ liệu theo lineage, và cấu hình daily run + thêm vào DAG.

## Điều kiện áp dụng

- Thư mục bài toán `docs/<problem-name>/` đã hoàn thành vòng lặp DEV-TEST:
  - `design/` — thiết kế từ Data Architect
  - `development.md` — thông tin job từ Developer
  - `test/` — test cases đã PASS từ Tester
- Các bảng đã dev với suffix `_dev` (do Developer tạo)

## Input

- Thư mục bài toán `docs/<problem-name>/` — đã hoàn thành vòng lặp DEV-TEST:
  - `design/` — thiết kế từ Data Architect
  - `development.md` — thông tin job từ Developer (danh sách job đã dev, input/output tables _dev, script chạy job)
  - `test/` — test cases đã PASS từ Tester

## Kiến thức nền tảng

- Cấu trúc thư mục: `chainslake/jobs/<chain_name>/{origin,extract,contract,token}/`
- Naming conventions, SQL format, application.properties
- Properties: `fromBlock/toBlock` (block) vs `fromEpochSecond/toEpochSecond` (time), `frequenceType`, `run_mode` `backward`/`forward`
- `chainslake/` được mount tự động vào container (volume `../chainslake` → `/home/hadoop/projects/chainslake`) — deploy DAG chỉ cần ghi file, KHÔNG cần thao tác docker

## Các bước thực hiện

### Bước 1: Chuẩn bị code (bỏ _dev suffix)

- Đọc `development.md` để lấy danh sách job đã dev.
- Với mỗi job, bỏ suffix `_dev`:
  - Đổi tên bảng output: `arbitrum.erc20_transfer_dev` → `arbitrum.erc20_transfer`
  - Đổi tên bảng input (nếu input cũng là `_dev`)
  - Đổi tên file `.sh` bỏ `_dev`
  - Sửa nội dung `.sh`/`.sql`: thay tên bảng `_dev` → tên bảng đúng
- **Nếu tên file trùng với file đang có** (trường hợp update bảng cũ): overwrite file cũ bằng file mới.
- **QUAN TRỌNG**: KHÔNG xóa bảng cũ, chỉ update properties.

### Bước 2: Reset properties (để chạy lại từ đầu)

Sau khi đổi tên, cần update properties để bảng chạy lại từ đầu:

- **Bảng chạy `backward`**:
  - `fromBlock = toBlock + 1` (hoặc `fromEpochSecond = toEpochSecond`)
  - → Lần chạy tiếp theo sẽ chạy lại từ toBlock về trước
- **Bảng chạy `forward`**:
  - `toBlock = fromBlock - 1` (hoặc `toEpochSecond = fromEpochSecond`)
  - → Lần chạy tiếp theo sẽ chạy lại từ đầu

Dùng trên bảng production:
```bash
python query/ddl_spark.py "ALTER TABLE <schema>.<table> SET TBLPROPERTIES (fromBlock=<value>)"
```

### Bước 3: Dọn dẹp _dev tables

Xóa các bảng dữ liệu có đuôi `_dev` trong data warehouse:
```bash
python query/drop_table.py <schema>.<table>_dev
```

### Bước 4: Tạo file UAT.md

- Tạo `docs/<problem-name>/UAT.md` theo template `template/UAT.md`
- Để trống phần Resource config và kết quả (sẽ điền sau khi chạy)

### Bước 5: Chạy thử 5 ngày dữ liệu

- Cấu hình job trong `.sh` để chạy 5 ngày dữ liệu (thay vì toàn bộ).
- Trigger thủ công theo đúng **thứ tự lineage** mà Architect đã thiết kế (đọc lineage từ `design/`: upstream phải chạy trước downstream).
- Lỗi **thiếu tài nguyên** → điều chỉnh: giảm `max_number_partition` + tăng `max_time_run`.
- Lỗi **logic** → trả lại team-lead để Developer xử lý.
- Sau khi chạy xong, thu thập:
  - Thời gian chạy
  - Khoảng data chạy (from-to)
  - Kích thước output (số bản ghi, dung lượng)
- Cập nhật thông tin vào `docs/<problem-name>/UAT.md`.

### Bước 6: Cấu hình daily run

- Điều chỉnh lại cấu hình job: mỗi lần chạy 1 ngày dữ liệu.
- Bổ sung job vào DAG theo đúng thiết kế lineage: tạo/sửa file `chainslake/airflow/dags/<chain>.py` (thư mục `chainslake/` được mount tự động vào container — KHÔNG cần thao tác docker).

## Tools được dùng

- `python query/query_table.py "<SQL>"` — verify data (chỉ SELECT có LIMIT)
- `python query/ddl_spark.py "<SQL>"` — set TBLPROPERTIES / DDL trên bảng production
- `python query/drop_table.py <table>` — xóa bảng `_dev`
- `python query/check_table_properties.py <table>` — kiểm tra tblproperties
- `python script/run_job.py <job_ref>` — chạy job
- `python script/trigger_dag.py <dag>` — trigger DAG

## Lưu ý / Gotchas

- **KHÔNG xóa bảng cũ khi update**: chỉ cập nhật properties, không drop bảng production đang có dữ liệu
- **Reset properties đúng run_mode**: `backward` → set `fromBlock = toBlock+1`; `forward` → set `toBlock = fromBlock-1` (set ngược sẽ chạy sai phạm vi)
- **Chạy theo thứ tự lineage**: upstream phải chạy xong trước downstream, nếu không job downstream sẽ không có data để xử lý
- **Thiếu tài nguyên ≠ lỗi logic**: giảm `max_number_partition` + tăng `max_time_run` khi thiếu RAM/thread; lỗi logic mới trả lại Developer
- **Deploy DAG không cần docker**: `chainslake/` đã mount vào container, chỉ cần ghi file `chainslake/airflow/dags/<chain>.py`

## Ví dụ thực tế

- Bài toán daily_dex_token_volume: sau khi Developer hoàn thành job `_dev` và Tester PASS, DataOps bỏ `_dev`, reset properties theo design (`backward`), tạo UAT.md, chạy thử 5 ngày theo lineage, rồi thêm job vào `chainslake/airflow/dags/ethereum.py`.
