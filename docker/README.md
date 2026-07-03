# Chainslake Warehouse — Hướng dẫn cài đặt qua Docker

Tài liệu này hướng dẫn từng bước cài đặt **Chainslake Data Warehouse** trên máy cục bộ sử dụng Docker Compose.

---

## Yêu cầu hệ thống

- **Docker** >= 20.10
- **Docker Compose** >= 2.0
- RAM tối thiểu: 8 GB (khuyến nghị 16 GB)
- Ổ đĩa trống: tối thiểu 20 GB

---

## Kiến trúc hệ thống

Hệ thống gồm 4 Docker service chính:

| Service    | Mô tả                                                                                  | Port          |
|------------|----------------------------------------------------------------------------------------|---------------|
| `postgres`  | Cơ sở dữ liệu PostgreSQL — lưu metadata của Airflow, Hive Metastore và Metabase       | 5432 (nội bộ) |
| `node01`   | Hadoop node chính: chạy HDFS NameNode + DataNode, Airflow, Trino, Hive, Spark         | 58080, 59870, 59001 |
| `node02`   | Hadoop node thứ hai: chạy HDFS DataNode                                                | —             |
| `metabase` | Ứng dụng Metabase để query dữ liệu và tạo biểu đồ                                     | 53000         |

---

## Bước 1: Chuẩn bị cấu hình môi trường

### 1.1. Tạo file `.env`

Sao chép file mẫu và chỉnh sửa theo môi trường của bạn:

```bash
cp env_example .env
```

Nội dung file `.env`:

```env
# Mật khẩu PostgreSQL (thay bằng mật khẩu mạnh hơn khi triển khai thực tế)
POSTGRES_PASSWORD=postgresexamplepassword

# Thư mục lưu dữ liệu PostgreSQL 
POSTGRES_DATA_DIR=./postgres_data

# Thư mục dữ liệu HDFS cho từng node
NODE01_DATA_DIR=./hadoop_data_node01
NODE02_DATA_DIR=./hadoop_data_node02

# Đường dẫn trong container
CHAINSLAKE_HOME_DIR=/home/hadoop/projects/chainslake
CHAINSLAKE_RUN_DIR=/home/hadoop/projects/chainslake-run
CHAINSLAKE_JAR=/home/hadoop/chainslake.jar
```

---

## Bước 2: Khởi tạo thư mục hệ thống

Chạy script `init_dir.sh` để tạo các thư mục cần thiết:

```bash
bash init_dir.sh
```

Script này thực hiện:

1. Khởi động tạm thời một container `lakechain/chainslake` và sao chép thư mục `/home/hadoop` ra ngoài thành thư mục `home/` — đây là thư mục chứa toàn bộ code, cấu hình và dữ liệu runtime của hệ thống.
2. Tạo thư mục `hadoop_data_node01/` — lưu dữ liệu HDFS của node01.
3. Tạo thư mục `hadoop_data_node02/` — lưu dữ liệu HDFS của node02.

Sau khi chạy, cấu trúc thư mục sẽ như sau:

```
docker/
├── home/                    # Home directory của hadoop user, mount vào node01
├── hadoop_data_node01/      # Dữ liệu HDFS của node01
├── hadoop_data_node02/      # Dữ liệu HDFS của node02
├── postgres_data/           # Dữ liệu PostgreSQL (tạo tự động nếu chưa có)
├── etc/                     # File cấu hình các service
├── docker-compose.yml
├── .env
└── init_dir.sh
```

> **Lưu ý:** Nếu bạn không có quyền `sudo`, lệnh `chown` trong script có thể bị bỏ qua. Các thư mục vẫn được tạo với quyền sở hữu của user hiện tại và hoạt động bình thường.

---

## Bước 3: Khởi động các service

```bash
docker compose up -d
```

Docker Compose sẽ tạo và khởi động tất cả các service. Kết quả mong đợi:

```
✔ Network chainslake-onprem-network  Created
✔ Container chainslake-onprem-postgres-1  Started
✔ Container chainslake-onprem-node02-1    Started
✔ Container chainslake-onprem-node01-1    Started
✔ Container chainslake-onprem-metabase-1  Started
```

Kiểm tra trạng thái các container:

```bash
docker compose ps
```

Tất cả container phải ở trạng thái `Up`:

```
NAME                           SERVICE    STATUS    PORTS
chainslake-onprem-postgres-1   postgres   Up        5432/tcp
chainslake-onprem-node02-1     node02     Up
chainslake-onprem-node01-1     node01     Up        0.0.0.0:58080->8080/tcp, 0.0.0.0:59001->9001/tcp, 0.0.0.0:59870->9870/tcp
chainslake-onprem-metabase-1   metabase   Up        0.0.0.0:53000->3000/tcp
```

---

## Bước 4: Kiểm tra Supervisord (localhost:59001)

**Supervisord** là công cụ quản lý các process chạy bên trong `node01`. Sau khi khởi động, truy cập:

```
http://localhost:59001
```

### Thông tin đăng nhập

Lấy username và password trong file `etc/supervisord_node01.conf`:

```ini
[inet_http_server]
port=0.0.0.0:9001
username=supervisord
password=supervisord@password
```

| Trường   | Giá trị               |
|----------|-----------------------|
| Username | `supervisord`         |
| Password | `supervisord@password` |

### Các service được quản lý

Sau khi đăng nhập, bạn sẽ thấy danh sách các service và trạng thái của chúng. Tất cả phải ở trạng thái **RUNNING**:

| Service                 | Mô tả                                   |
|-------------------------|-----------------------------------------|
| `airflow`               | Airflow scheduler & web server          |
| `hdfs-namenode`         | HDFS NameNode                           |
| `hdfs-secondarynamenode`| HDFS Secondary NameNode                 |
| `hdfs-datanode`         | HDFS DataNode trên node01               |
| `hive-metastore`        | Hive Metastore service                  |
| `spark-thriftserver`    | Spark Thrift Server (JDBC/ODBC)         |
| `trino`                 | Trino query engine                      |

> **Lưu ý:** Các service có thể mất 1–2 phút để khởi động hoàn toàn sau khi container start. Nếu một số service ở trạng thái `STARTING`, hãy chờ thêm và refresh lại trang.

---

## Bước 5: Kiểm tra Airflow (localhost:58080)

**Apache Airflow** được dùng để lên lịch và quản lý các pipeline dữ liệu. Truy cập:

```
http://localhost:58080
```

### Thông tin đăng nhập

| Trường   | Giá trị                                      |
|----------|----------------------------------------------|
| Username | `admin`                                      |
| Password | Xem trong file mô tả bên dưới                |

Mật khẩu do Airflow tự sinh khi khởi chạy lần đầu. Đọc mật khẩu bằng lệnh:

```bash
cat home/projects/chainslake/airflow/standalone_admin_password.txt
```

Hoặc từ bên trong container:

```bash
docker exec chainslake-onprem-node01-1 cat /home/hadoop/projects/chainslake/airflow/standalone_admin_password.txt
```

> **Lưu ý:** File `standalone_admin_password.txt` chỉ xuất hiện sau khi Airflow đã khởi động thành công lần đầu. Nếu file chưa tồn tại, hãy đợi thêm 1–2 phút và kiểm tra lại trạng thái service `airflow` trên Supervisord.

---

## Bước 6: Kiểm tra và cấu hình Metabase (localhost:53000)

**Metabase** là công cụ BI để query dữ liệu và tạo biểu đồ trực quan. Truy cập:

```
http://localhost:53000
```

### 6.1. Tạo tài khoản admin

Lần đầu truy cập, Metabase sẽ yêu cầu thiết lập tài khoản admin:

1. Chọn ngôn ngữ và múi giờ.
2. Điền thông tin tài khoản admin (email, mật khẩu) theo ý muốn.
3. Hoàn tất các bước thiết lập ban đầu.

### 6.2. Kết nối với Data Warehouse qua SparkSQL

Sau khi tạo tài khoản, thêm kết nối đến data warehouse:

1. Vào **Settings** → **Admin** → **Databases** → **Add database**.
2. Điền thông tin kết nối như sau:

| Trường          | Giá trị    |
|-----------------|------------|
| Database type   | `SparkSQL` |
| Display name    | `Spark`    |
| Host            | `node01`   |
| Port            | `10000`    |
| Database name   | `default`  |
| Username        | `hadoop`   |
| Password        | `hadooppass` |

3. Nhấn **Save** để lưu kết nối.

> **Lưu ý:** Spark Thrift Server (port 10000) có thể mất vài phút để sẵn sàng nhận kết nối sau khi khởi động. Nếu kết nối thất bại, hãy kiểm tra trạng thái service `spark-thriftserver` trên Supervisord (localhost:59001) và thử lại sau.

---

## Dừng và khởi động lại hệ thống

Dừng tất cả service:

```bash
docker compose down
```

Khởi động lại:

```bash
docker compose up -d
```

Xem log của một service:

```bash
docker compose logs -f node01
docker compose logs -f metabase
```

---

## Xử lý sự cố thường gặp

**Supervisord không hiện đủ 7 service ở trạng thái RUNNING**

Các service trong node01 cần thời gian khởi động theo thứ tự. Hãy chờ 2–3 phút sau khi `docker compose up -d`, rồi refresh trang Supervisord.

---

**Không tìm thấy file `standalone_admin_password.txt` của Airflow**

File này chỉ được tạo sau khi Airflow khởi động thành công lần đầu. Kiểm tra log của Airflow:

```bash
docker exec chainslake-onprem-node01-1 tail -50 /tmp/airflow.log
```

---

**Metabase không kết nối được với SparkSQL**

Kiểm tra Spark Thrift Server trên Supervisord. Nếu service chưa `RUNNING`, hãy đợi thêm. Có thể thử restart service từ giao diện Supervisord.
