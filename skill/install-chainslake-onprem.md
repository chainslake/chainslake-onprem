# Skill: Cài đặt Chainslake On-Premises

## Mô tả
Hướng dẫn cài đặt hệ thống Chainslake Data Warehouse trên máy local hoặc server riêng bằng Docker Compose.

## Điều kiện áp dụng
- Người dùng yêu cầu cài đặt Chainslake on-prem từ đầu
- Hệ thống chưa có các Docker service đang chạy

---

## Yêu cầu hệ thống

- Docker >= 20.10, Docker Compose >= 2.0
- RAM >= 8 GB (khuyến nghị 16 GB)
- Ổ trống >= 20 GB

## Kiến trúc service

| Service | Mô tả | Port |
|---|---|---|
| `postgres` | PostgreSQL — metadata cho Airflow, Hive, Metabase | 5432 (nội bộ) |
| `node01` | HDFS NameNode + DataNode, Airflow, Trino, Hive, Spark | 58080, 59870, 59001 |
| `node02` | HDFS DataNode | — |
| `metabase` | BI tool | 53000 |

---

## Bước 1: Tạo file `.env`

```bash
cd docker
cp env_example .env
```

Nội dung `.env` mặc định:

```env
POSTGRES_PASSWORD=postgresexamplepassword
POSTGRES_DATA_DIR=./postgres_data
NODE01_DATA_DIR=./hadoop_data_node01
NODE02_DATA_DIR=./hadoop_data_node02
CHAINSLAKE_HOME_DIR=/home/hadoop/projects/chainslake
CHAINSLAKE_RUN_DIR=/home/hadoop/projects/chainslake-run
```

## Bước 2: Khởi tạo thư mục hệ thống

```bash
bash init_dir.sh
```

Script thực hiện:
1. Khởi động tạm container `lakechain/chainslake` → sao chép `/home/hadoop` ra thành `docker/home/`
2. Tạo `hadoop_data_node01/` và `hadoop_data_node02/`

Kết quả:

```
docker/
├── home/                    # mount vào node01
├── hadoop_data_node01/
├── hadoop_data_node02/
├── postgres_data/
├── etc/
├── docker-compose.yml
├── .env
└── init_dir.sh
```

## Bước 3: Khởi động service

```bash
docker compose up -d
docker compose ps          # tất cả phải ở trạng thái Up
```

## Bước 4: Kiểm tra Supervisord

Truy cập `http://localhost:59001`

| Trường | Giá trị |
|---|---|
| Username | `supervisord` |
| Password | `supervisord@password` |

7 service phải ở trạng thái RUNNING: `airflow`, `hdfs-namenode`, `hdfs-secondarynamenode`, `hdfs-datanode`, `hive-metastore`, `spark-thriftserver`, `trino`.

> Nếu một số service `STARTING`, chờ 1–2 phút rồi refresh.

## Bước 5: Kiểm tra Airflow

Truy cập `http://localhost:58080`

| Trường | Giá trị |
|---|---|
| Username | `admin` |
| Password | Đọc từ file (xem bên dưới) |

Lấy mật khẩu:

```bash
cat docker/home/projects/chainslake/airflow/standalone_admin_password.txt
```

Hoặc qua container:

```bash
docker exec chainslake-onprem-node01-1 cat /home/hadoop/projects/chainslake/airflow/standalone_admin_password.txt
```

> File chỉ xuất hiện sau khi Airflow khởi động xong lần đầu. Nếu chưa có, chờ thêm 1–2 phút.

## Bước 6: Thiết lập Metabase

### 6.1. Chuẩn bị credentials

```bash
cp script/env_example script/.env
```

Chỉnh sửa `script/.env`:

```env
METABASE_URL=http://localhost:53000
METABASE_EMAIL=admin@chainslake.com
METABASE_PASSWORD=<your_password_here>
METABASE_SITE_NAME=Chainslake Warehouse
```

### 6.2. Chạy script setup

```bash
python script/setup_metabase.py
```

Script tự động: đợi Metabase sẵn sàng → tạo admin → tạo API key → thêm SparkSQL/Trino → authenticate CLI.

Tuỳ chọn:
```bash
python script/setup_metabase.py --skip-databases   # bỏ qua thêm DB
python script/setup_metabase.py --skip-cli          # bypass CLI auth
```

### 6.3. Kiểm tra

- Login `http://localhost:53000`
- **Settings → Admin → Databases** — Spark và Trino đã được thêm
- `query/.env` đã có `METABASE_API_KEY=...`

---

## Dừng / khởi động lại

```bash
docker compose down        # dừng
docker compose up -d       # khởi động
docker compose logs -f node01   # xem log
```

---

## Xử lý sự cố

| Vấn đề | Cách xử lý |
|---|---|
| Supervisord thiếu service RUNNING | Chờ 2–3 phút sau `docker compose up -d`, refresh lại |
| Thiếu `standalone_admin_password.txt` | `docker exec chainslake-onprem-node01-1 tail -50 /tmp/airflow.log` — chờ Airflow khởi động xong |
| Metabase không kết nối SparkSQL | Kiểm tra Spark Thrift Server trên Supervisord, restart nếu chưa RUNNING |
