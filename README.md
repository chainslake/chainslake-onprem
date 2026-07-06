# Chainslake On-Premises — Blockchain Data Warehouse

**Chainslake** là một blockchain data warehouse, cho phép người dùng tự quản lý và vận hành hạ tầng phân tích dữ liệu blockchain một cách an toàn và riêng tư. Chainslake cung cấp cả giải pháp **On-Cloud** và **On-Premises** phù hợp với nhu cầu của nhiều khách hàng.

Repository này giới thiệu giải pháp **Onprem**, phù hợp với nhóm khách hàng đang có sẵn hạ tầng phần cứng hoặc muốn chạy thử nghiệm trên máy local.

---

## Mục lục

1. [Tổng quan kiến trúc](#tổng-quan-kiến-trúc)
2. [Cài đặt hệ thống](#cài-đặt-hệ-thống)
3. [Cấu trúc thư mục](#cấu-trúc-thư-mục)
4. [Thư mục `chainslake-run`](#thư-mục-chainslake-run)
5. [Thư mục `chainslake`](#thư-mục-chainslake)
   - [jobs — Script thực thi](#jobs--script-thực-thi)
   - [sql — Logic biến đổi dữ liệu](#sql--logic-biến-đổi-dữ-liệu)
   - [evm/abi — ABI Contract](#evmabi--abi-contract)
   - [airflow/dags — Pipeline & Scheduling](#airflowdags--pipeline--scheduling)
   - [application.properties — Cấu hình pipeline](#applicationproperties--cấu-hình-pipeline)
6. [Luồng hoạt động](#luồng-hoạt-động)
7. [Ví dụ chi tiết: Pipeline Ethereum](#ví-dụ-chi-tiết-pipeline-ethereum)
8. [Tool query dữ liệu trong Data warehouse](#tool-query-dữ-liệu-trong-data-warehouse)
9. [Liên hệ](#liên-hệ)

---

## Tổng quan kiến trúc

Chainslake Onprem được xây dựng trên nền tảng các công nghệ Big Data mã nguồn mở:

- **HDFS** — Lưu trữ dữ liệu phân tán (Delta Lake format)
- **Apache Spark** — Xử lý và biến đổi dữ liệu theo batch
- **Apache Hive Metastore** — Quản lý metadata các bảng
- **Trino** — Query engine tốc độ cao để truy vấn dữ liệu
- **Apache Airflow** — Lên lịch và quản lý pipeline
- **Metabase** — Giao diện BI để phân tích và trực quan hóa dữ liệu

Toàn bộ hệ thống được đóng gói trong Docker, giúp triển khai nhanh chóng trên bất kỳ môi trường nào.

---

## Cài đặt hệ thống

Để cài đặt và khởi động hệ thống Chainslake Onprem trên máy local hoặc server riêng, hãy đọc và thực hiện theo hướng dẫn chi tiết trong:

📄 **[docker/README.md](./docker/README.md)**

Hướng dẫn đó bao gồm toàn bộ các bước:
- Yêu cầu hệ thống
- Cấu hình môi trường
- Khởi tạo và khởi động các service
- Kiểm tra Supervisord, Airflow, Metabase
- Xử lý sự cố thường gặp

---

## Cấu trúc thư mục

```
chainslake-onprem/
├── chainslake-run/             # File thực thi và thư viện phụ thuộc
│   ├── .env                    # Biến môi trường (copy từ env_example)
│   ├── env_example             # File mẫu biến môi trường
│   ├── chainslake-run.sh       # Lệnh spark-submit để chạy các job
│   ├── chainslake-deps.jar     # Thư viện phụ thuộc
│   └── chainslake.jar          # File thực thi chính (liên hệ Admin để lấy)
│
├── chainslake/                 # Source code cấu hình và thực thi các job
│   ├── jobs/                   # Script .sh cho từng job
│   │   └── ethereum/
│   │       ├── application.properties
│   │       ├── origin/
│   │       ├── extract/
│   │       └── contract/
│   ├── sql/                    # File .sql cho app sql.transformer
│   │   ├── evm/
│   │   └── evm_contract/
│   ├── evm/
│   │   └── abi/                # ABI của các EVM smart contract
│   └── airflow/
│       └── dags/               # Airflow DAG để build pipeline và schedule
│
└── docker/                     # Cấu hình Docker Compose
    ├── README.md               # Hướng dẫn cài đặt
    ├── docker-compose.yml
    └── ...
```

> **Lưu ý:** Cả hai thư mục `chainslake-run` và `chainslake` đều được mount vào `home/projects/` bên trong container `node01`. Xem chi tiết trong [docker/README.md](./docker/README.md).

---

## Thư mục `chainslake-run`

Thư mục này chứa các thành phần cần thiết để thực thi các Spark job.

### Cấu trúc

| File/Thư mục | Mô tả |
|---|---|
| `env_example` | File mẫu chứa biến môi trường, cần copy thành `.env` và chỉnh sửa |
| `.env` | File biến môi trường thực tế (không được commit lên git) |
| `chainslake-run.sh` | Script wrapper cho lệnh `spark-submit`, là nền tảng cho mọi job |
| `chainslake-deps.jar` | Thư viện phụ thuộc (Delta Lake, Hadoop connector, v.v.) |
| `chainslake.jar` | File thực thi chính của Chainslake — **không nằm trong repo**, liên hệ Admin để lấy |

### Thiết lập `.env`

```bash
cp chainslake-run/env_example chainslake-run/.env
# Mở và chỉnh sửa các giá trị phù hợp với môi trường của bạn
```

File `.env` chứa các biến như danh sách RPC endpoint của các blockchain:

```env
ETHEREUM_RPCS=https://rpc.nodeflare.app/eth/public,...
```

Các biến này được load vào môi trường trước khi chạy những job cần gọi trực tiếp đến RPC (ví dụ: các job trong thư mục `origin/`).

### `chainslake-run.sh`

Script này là wrapper cho `spark-submit`, thiết lập sẵn các cấu hình Spark mặc định:

```bash
spark-submit --master local[2] \
    --driver-memory 4g \
    --deploy-mode client \
    "$@" \
    --conf "spark.app_properties.chainslake_home_dir=$CHAINSLAKE_HOME_DIR" \
    --conf "spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension" \
    --conf "spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog" \
    --jars $CHAINSLAKE_RUN_DIR/chainslake-deps.jar \
    $CHAINSLAKE_RUN_DIR/chainslake.jar
```

Mỗi script job sẽ gọi `chainslake-run.sh` và bổ sung thêm các tham số `--class`, `--name`, và `--conf` riêng của job đó.

---

## Thư mục `chainslake`

Thư mục này chứa toàn bộ source code để cấu hình và điều phối các job xử lý dữ liệu.

---

### `jobs` — Script thực thi

Mỗi file `.sh` trong thư mục `jobs/` đại diện cho **một job**, và mỗi job sẽ ghi dữ liệu ra **một bảng** trong data warehouse.

Cấu trúc thư mục `jobs/` được tổ chức theo chain và loại job:

```
jobs/
└── ethereum/
    ├── application.properties   # Cấu hình chung cho pipeline Ethereum
    ├── origin/                  # Job lấy dữ liệu thô từ RPC node
    │   ├── blocks_receipt.sh
    │   └── transaction_blocks.sh
    ├── extract/                 # Job biến đổi dữ liệu thô thành bảng có cấu trúc
    │   ├── blocks.sh
    │   ├── transactions.sh
    │   └── logs.sh
    └── contract/                # Job decode dữ liệu contract
        └── decoded_log.sh
```

Mỗi script `.sh` gọi đến `chainslake-run.sh` và chỉ định:
- `--class`: Class Java/Scala cần thực thi
- `--name`: Tên Spark application (dùng để nhận diện trên Spark UI)
- `--conf spark.app_properties.app_name`: **App nào** sẽ được gọi (mỗi app có logic riêng)
- `--conf spark.app_properties.config_file`: File `application.properties` của pipeline

**Ví dụ — `extract/blocks.sh`:**

```bash
$CHAINSLAKE_RUN_DIR/chainslake-run.sh --class chainslake.sql.Main \
    --name EthereumBlocks \
    --conf "spark.app_properties.app_name=sql.transformer" \
    --conf "spark.app_properties.config_file=ethereum/application.properties" \
    --conf "spark.app_properties.sql_file=evm/blocks.sql"
```

**Ví dụ — `origin/blocks_receipt.sh`** (cần load `.env` vì dùng RPC):

```bash
export $(cat $CHAINSLAKE_RUN_DIR/.env) && $CHAINSLAKE_RUN_DIR/chainslake-run.sh --class chainslake.evm.Main \
    --name EthereumOriginBlocksReceipt \
    --conf "spark.app_properties.app_name=evm_origin.blocks_receipt" \
    --conf "spark.app_properties.rpc_list=$ETHEREUM_RPCS" \
    --conf "spark.app_properties.config_file=ethereum/application.properties"
```

#### App `sql.transformer`

Đây là app đặc biệt cho phép thực hiện một phép biến đổi dữ liệu thuần bằng SQL. Thay vì viết code Spark, bạn chỉ cần:
1. Viết một file `.sql` chứa logic biến đổi
2. Trỏ job đến file `.sql` đó qua tham số `sql_file`

App này đọc các bảng input, thực thi SQL, và ghi kết quả ra bảng output — toàn bộ cấu hình nằm trong file `.sql`.

---

### `sql` — Logic biến đổi dữ liệu

Thư mục `sql/` chứa các file `.sql` được sử dụng bởi app `sql.transformer`. Mỗi file `.sql` gồm **hai phần** phân tách bởi dấu `===`:

```
<phần header — cấu hình job>
===
<phần body — logic SQL>
```

#### Phần Header

Phần header chứa các cấu hình dạng `key=value`. Hai cấu hình quan trọng nhất:

| Cấu hình | Mô tả |
|---|---|
| `output_table` | Bảng mà job sẽ ghi dữ liệu vào |
| `list_input_tables` | Danh sách các bảng mà job đọc dữ liệu từ (phân cách bằng dấu phẩy) |

Ngoài ra còn các cấu hình khác như `partition_by`, `write_mode`, `number_index_columns`, v.v.

#### Phần Body

Phần body chứa câu lệnh SQL để biến đổi từ bảng input ra bảng output.

#### Biến động `${}`

Trong file `.sql`, các giá trị động được đặt trong cú pháp `${}`. Các biến này được lấy từ:
- Cấu hình của job (tham số `--conf`)
- File `application.properties` mà job đang sử dụng

Hai biến đặc biệt do hệ thống tự tính toán:

| Biến | Mô tả |
|---|---|
| `${from}` | Block bắt đầu xử lý trong lần chạy hiện tại |
| `${to}` | Block kết thúc xử lý trong lần chạy hiện tại |

**Ví dụ — `sql/evm/blocks.sql`:**

```sql
frequent_type=block
list_input_tables=${chain_name}_origin.transaction_blocks,${chain_name}_origin.blocks_receipt
output_table=${chain_name}.blocks
partition_by=block_date
write_mode=Append
number_index_columns=3

===

with transaction_blocks as (
    select block_date, block_number, block_time, number_tx
    from ${transaction_blocks}
    where block_number >= ${from} and block_number <= ${to}
)
, blocks_receipt as (
    select block_date, block_number, block_time, number_logs
    from ${blocks_receipt}
    where block_number >= ${from} and block_number <= ${to}
)

select t.block_date
    , t.block_number
    , t.block_time
    , t.number_tx
    , l.number_logs
from transaction_blocks t
inner join blocks_receipt l
on t.block_number = l.block_number
```

Trong ví dụ này:
- Input: `ethereum_origin.transaction_blocks` và `ethereum_origin.blocks_receipt`
- Output: `ethereum.blocks`
- Biến `${chain_name}` được lấy từ `application.properties` (giá trị: `ethereum`)
- Biến `${from}` và `${to}` được hệ thống tự tính theo tiến trình xử lý

---

### `evm/abi` — ABI Contract

Thư mục `evm/abi/` chứa các file ABI (Application Binary Interface) của smart contract trên các EVM blockchain. Các file ABI này được sử dụng để decode dữ liệu log theo business logic của từng contract.

**Ví dụ:** File `erc20.json` chứa ABI chuẩn của ERC-20 token, cho phép decode các event như `Transfer`, `Approval` từ raw log data.

Khi thêm một contract mới cần decode, bạn chỉ cần:
1. Thêm file ABI của contract vào thư mục này
2. Tạo job `decoded_log.sh` tương ứng và file `.sql` để xử lý logic decode

---

### `airflow/dags` — Pipeline & Scheduling

Thư mục `airflow/dags/` chứa các **Airflow DAG** dùng để định nghĩa pipeline và lên lịch chạy job. Thông thường, tất cả các job của một blockchain được đặt chung trong một DAG.

Airflow được truy cập tại:

```
http://localhost:58080
```

(Xem thông tin đăng nhập trong [docker/README.md](./docker/README.md))

**Ví dụ — `dags/ethereum.py`:**

```python
with DAG(
    "Ethereum",
    schedule="10 0 * * *",   # Chạy lúc 0:10 mỗi ngày
    max_active_runs=1,
    max_active_tasks=10,
    is_paused_upon_creation=True,
) as dag:

    # ORIGIN: Lấy dữ liệu thô từ RPC
    ethereum_origin_transaction_blocks = BashOperator(...)
    ethereum_origin_blocks_receipt = BashOperator(...)
    ethereum_origin_transaction_blocks >> ethereum_origin_blocks_receipt

    # EXTRACT: Biến đổi thành bảng có cấu trúc
    ethereum_blocks = BashOperator(...)
    ethereum_origin_blocks_receipt >> ethereum_blocks

    ethereum_transactions = BashOperator(...)
    ethereum_logs = BashOperator(...)
    ethereum_origin_blocks_receipt >> [ethereum_transactions, ethereum_logs]

    # DECODED: Decode contract events
    ethereum_decoded_erc20_evt_transfer = BashOperator(...)
    ethereum_logs >> ethereum_decoded_erc20_evt_transfer
```

Thứ tự phụ thuộc giữa các task (toán tử `>>`) tạo thành một graph phụ thuộc rõ ràng. Các task không phụ thuộc nhau có thể chạy song song (giới hạn bởi `max_active_tasks`).

Việc bật/tắt từng DAG hoặc từng task được thực hiện trực tiếp trên giao diện Airflow.

---

### `application.properties` — Cấu hình pipeline

Mỗi pipeline (thư mục job của một chain) có một file `application.properties` riêng. File này chứa các cấu hình chung mà mọi job trong pipeline đều đọc khi khởi động.

**Ví dụ — `jobs/ethereum/application.properties`:**

```properties
chain_name=ethereum
max_number_partition=1
max_time_run=1
run_mode=backward
number_block_per_partition=300
max_retry=10
wait_miliseconds=100
```

#### Giải thích các cấu hình

| Cấu hình | Mô tả |
|---|---|
| `chain_name` | Tên của blockchain. Thường được dùng làm **schema** cho các bảng trong data warehouse. Ví dụ: `output_table=${chain_name}.blocks` → bảng `ethereum.blocks` |
| `number_block_per_partition` | Số block trong mỗi partition. Mỗi partition được xử lý bởi một luồng (thread/process). Nên chọn sao cho mỗi partition tương đương khoảng 1 giờ dữ liệu |
| `max_number_partition` | Số partition tối đa được xử lý trong **một vòng lặp**. Có thể chạy song song hoặc tuần tự tùy thuộc vào số core và executor được cấp phát trong Spark. Sau mỗi vòng lặp, job ghi dữ liệu xuống bảng một lần |
| `max_time_run` | Số vòng lặp tối đa trong **một lần chạy job** |
| `run_mode` | `backward` hoặc `forward`. Xác định chiều xử lý dữ liệu: **backward** (từ hiện tại về quá khứ, ưu tiên dữ liệu mới nhất) hoặc **forward** (từ quá khứ đến hiện tại). Mỗi vòng lặp backward vẫn xử lý cả dữ liệu mới và dữ liệu cũ (theo hướng ngược lại) |
| `start_number` / `end_number` | Phạm vi block cần xử lý. `-1` nghĩa là không giới hạn |
| `max_retry` | Số lần thử lại tối đa khi một partition gặp lỗi |
| `is_alert` | Bật/tắt cảnh báo khi job lỗi |

> Ngoài các cấu hình trên, từng job có thể có thêm các cấu hình đặc thù được mô tả riêng trong tài liệu của job đó.

---

## Luồng hoạt động

Dưới đây là luồng xử lý dữ liệu tổng quát trong một pipeline Chainslake:

```
RPC Node (Blockchain)
        │
        ▼
  [origin jobs]          ← Lấy dữ liệu thô, lưu vào schema *_origin
        │
        ▼
  [extract jobs]         ← Biến đổi và chuẩn hóa dữ liệu (dùng sql.transformer)
        │
        ▼
  [contract/decode jobs] ← Decode smart contract events theo ABI
        │
        ▼
  Data Warehouse (HDFS / Delta Lake)
        │
        ▼
  Trino / SparkSQL → Metabase (BI & Visualization)
```

Toàn bộ luồng này được điều phối bởi **Airflow DAG**, chạy theo lịch định sẵn và đảm bảo thứ tự phụ thuộc giữa các bước.

---

## Ví dụ chi tiết: Pipeline Ethereum

### Các bảng được tạo ra

| Schema | Bảng | Mô tả |
|---|---|---|
| `ethereum_origin` | `transaction_blocks` | Dữ liệu thô về block và transaction từ RPC |
| `ethereum_origin` | `blocks_receipt` | Dữ liệu thô về block receipts từ RPC |
| `ethereum` | `blocks` | Bảng block đã chuẩn hóa |
| `ethereum` | `transactions` | Bảng transaction đã chuẩn hóa |
| `ethereum` | `logs` | Bảng raw logs đã chuẩn hóa |
| `ethereum_decoded` | `erc20_evt_transfer` | Event Transfer của ERC-20 token đã decode |

### Chạy thủ công một job

Để chạy thủ công một job (ví dụ: job `blocks`), SSH vào `node01` hoặc exec vào container:

```bash
docker exec -it chainslake-onprem-node01-1 bash
```

Sau đó:

```bash
cd /home/hadoop/projects/chainslake/jobs/ethereum
./extract/blocks.sh
```

Hoặc có thể gọi trực tiếp từ bên ngoài qua lệnh sau:

```bash
docker exec -u hadoop chainslake-onprem-node01-1 bash -c "export PS1='something' && source /etc/bash.bashrc && cd /home/hadoop/projects/chainslake/jobs/ethereum && ./extract/blocks.sh" 2>&1
```

### Thêm một pipeline mới (ví dụ: BNB Chain)

1. Tạo thư mục `chainslake/jobs/bnb/`
2. Tạo file `application.properties` với `chain_name=bnb`
3. Tạo các script `.sh` cho từng job (origin, extract, contract)
4. Tạo DAG mới `chainslake/airflow/dags/bnb.py`
5. Nếu cần decode contract mới, thêm ABI vào `chainslake/evm/abi/`

---

## Tool query dữ liệu trong Data warehouse

Để sử dụng tool query dữ liệu trong Data warehouse hãy tham khảo tài liệu sau:

📄 **[query/README.md](./query/README.md)**

Hướng dẫn đó bao gồm:
- Cài đặt thư viện
- Cấu hình API Key
- Danh sách các script và cách sử dụng:
    - `get_example_table.py` — Lấy bản ghi mẫu từ bảng
    - `query_table.py` — Thực thi câu truy vấn SQL
    - `drop_table.py` — Xóa bảng

---

## Liên hệ

File `chainslake.jar` (file thực thi chính) **không được phân phối trong repo này**. Để lấy file này, vui lòng liên hệ với Admin của Chainslake.

Đối với các vấn đề kỹ thuật hoặc hỗ trợ cài đặt, vui lòng tạo issue trên repository này.
