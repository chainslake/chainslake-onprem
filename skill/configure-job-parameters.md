# Skill: Configure Job/Pipeline Parameters

## Mô tả
Hướng dẫn cấu hình các tham số quan trọng của job/pipeline trong Chainslake: `number_block_per_partition`, `max_number_partition`, `max_time_run`, `start_date` trên DAG, `run_mode`, và backfill job mới.

## Điều kiện áp dụng
- Khi thiết lập pipeline mới cho một chain
- Khi cần tối ưu lại tham số của pipeline đã có
- Khi thêm job mới vào DAG đã chạy được một thời gian
- Khi cần cấu hình `start_date` hoặc chuyển `run_mode`

## Tham số cấu hình quan trọng

Các tham số này có thể được cấu hình ở **2 nơi**:
1. **`application.properties`** — cấu hình chung cho toàn pipeline
2. **Trong file `.sh`** của job — thông qua `--conf "spark.app_properties.<tham_số>=<giá_trị>"`

**Thứ tự ưu tiên**: Nếu cả 2 nơi đều có, job sẽ sử dụng giá trị trong file `.sh`.

---

## Các bước thực hiện

### Bước 1: Cấu hình `number_block_per_partition`

Mục tiêu: mỗi partition xử lý ~1 giờ dữ liệu (+ 5% buffer).

#### Cách 1: Ước tính từ Internet (khi setup mới)

Tra cứu tốc độ block trung bình của chain và tính toán:

| Chain | Block time | number_block_per_partition |
|---|---|---|
| Ethereum | ~12s/block | 300 |
| BNB | ~3s/block | 1000 |
| Polygon | ~2s/block | 1500 |

Công thức: `number_block_per_partition = (3600 / block_time_seconds) * 1.05`

#### Cách 2: Tính chính xác từ dữ liệu thực (sau khi đã chạy 1-2 lần)

Sử dụng query để đếm số block thực tế trong 1 giờ:

```sql
-- Đếm số block trong mỗi giờ (dùng bảng transaction_blocks)
SELECT
    hour(from_unixtime(block_time)) as block_hour,
    count(*) as blocks_per_hour
FROM <chain>_origin.transaction_blocks
WHERE block_time >= unix_timestamp('<ngày_bắt_đầu>')
  AND block_time < unix_timestamp('<ngày_kết_thúc>')
GROUP BY hour(from_unixtime(block_time))
ORDER BY block_hour
```

Hoặc cách đơn giản hơn:

```sql
-- Lấy min/max block trong 1 giờ cụ thể
SELECT
    min(block_number) as min_block,
    max(block_number) as max_block,
    (max(block_number) - min(block_number)) as blocks_in_hour
FROM <chain>_origin.transaction_blocks
WHERE block_time >= unix_timestamp('<ngày> 00:00:00')
  AND block_time < unix_timestamp('<ngày> 01:00:00')
```

Sau khi có số block trung bình/giờ, nhân thêm 5% buffer:
```
number_block_per_partition = blocks_per_hour * 1.05
```

**Lưu ý quan trọng**: Đảm bảo có đủ data trong 1 giờ được chọn để tính (không lấy giờ bị thiếu data).

#### Quy trình tốt nhất khi setup chain mới

1. Lấy giá trị ước tính từ Internet (Bước 1 - Cách 1)
2. Set `max_number_partition=1`, `max_time_run=2` trong `application.properties`
3. Chạy job origin 1-2 lần để có dữ liệu
4. Query để tính chính xác `number_block_per_partition` (Bước 1 - Cách 2)
5. Cập nhật lại `application.properties` với giá trị chính xác

#### Áp dụng cấu hình

**Trong `application.properties`:**
```properties
number_block_per_partition=300
```

**Hoặc trong file `.sh` (override `application.properties`):**
```bash
$CHAINSLAKE_RUN_DIR/chainslake-run.sh --class chainslake.evm.Main \
    --name EthereumOriginTransactionBlocks \
    --conf "spark.app_properties.number_block_per_partition=300" \
    ...
```

---

### Bước 2: Cấu hình `max_number_partition`

Tham số này quyết định bao nhiêu partitions được xử lý **đồng thời** trong 1 vòng lặp.

#### Xác định tài nguyên hiện tại

Kiểm tra cấu hình Spark hiện tại trong `chainslake-run.sh`:

```bash
cat chainslake-run.sh
```

Chú ý 2 tham số:
- `--master local[N]` — số N = số threads (đọc song song)
- `--driver-memory Xg` — bộ nhớ cấp cho driver

Ví dụ hiện tại:
```bash
spark-submit --master local[2] \
    --driver-memory 4g \
    ...
```
→ 2 threads, 4GB memory

#### Tính memory cần thiết cho 1 partition

Bước 1: Xác định dung lượng 1 partition dữ liệu:

```sql
-- Xem dung lượng bảng (tổng)
DESCRIBE DETAIL <chain>_origin.transaction_blocks;
-- Tìm trường sizeInBytes
```

```sql
-- Nếu bảng partition theo block_number, ước tính dung lượng 1 partition
SELECT
    count(*) as total_rows,
    pg_total_relation_size('<chain>_origin.transaction_blocks') / count(*) as avg_row_bytes
FROM <chain>_origin.transaction_blocks
LIMIT 1;
```

Bước 2: Ước tính dung lượng 1 partition:
```
memory_per_partition ≈ (number_of_partitions × avg_row_bytes × rows_per_partition) / 1024^3
```

Bước 3: Tính `max_number_partition`:
```
max_number_partition = floor(available_memory_gb / memory_per_partition_gb)
```

**Lưu ý**: Memory cần > dung lượng data đọc + dung lượng data ghi. Luôn để buffer ~30%.

#### Quy tắc nhanh

| Tài nguyên | max_number_partition khuyến nghị |
|---|---|
| `local[2]` + `4g` | 1-4 (tùy dung lượng partition) |
| `local[4]` + `8g` | 2-8 |
| `local[8]` + `16g` | 4-16 |

**Quy tắc quan trọng**: Đối với job dùng `frequent_type=day` trong SQL header, `max_number_partition` **PHẢI >= 24** (vì mỗi ngày có 24 giờ, mỗi giờ là 1 partition).

#### Áp dụng cấu hình

**Trong `application.properties`:**
```properties
max_number_partition=1
```

**Hoặc trong file `.sh`:**
```bash
$CHAINSLAKE_RUN_DIR/chainslake-run.sh ... \
    --conf "spark.app_properties.max_number_partition=24" \
    ...
```

---

### Bước 3: Cấu hình `max_time_run`

Tham số này cho biết số vòng lặp trong 1 lần chạy job.

**Mục tiêu**: 1 lần chạy xử lý được **~1 ngày dữ liệu**.

Công thức:
```
max_time_run = ceil(24 / max_number_partition)
```

Ví dụ:
- `max_number_partition=1` → `max_time_run=24` (24 vòng × 1 partition = 24 partitions = 24 giờ = 1 ngày)
- `max_number_partition=24` → `max_time_run=1` (1 vòng × 24 partitions = 24 giờ = 1 ngày)
- `max_number_partition=12` → `max_time_run=2` (2 vòng × 12 partitions = 24 giờ = 1 ngày)

**Lưu ý**: Nếu `number_block_per_partition` tương đương ~1 giờ, thì `max_time_run` nên đủ để xử lý 24 giờ (1 ngày).

#### Áp dụng cấu hình

**Trong `application.properties`:**
```properties
max_time_run=1
```

---

### Bước 4: Cấu hình `start_date` và `catchup` trên DAG

```python
from datetime import datetime, timedelta

# Trong file DAG
with DAG(
    "Ethereum",
    start_date=datetime.now() - timedelta(days=730),  # ← Mặc định: 2 năm trước ngày hiện tại
    catchup=False,                                      # ← Không tự chạy lại từ start_date
    ...
)
```

**Cách xác định `start_date`**: Mặc định đặt `start_date` là **2 năm trước ngày hiện tại** (`datetime.now() - timedelta(days=730)`). Nếu người dùng cần dữ liệu sớm hơn, hỏi lại và đặt theo yêu cầu.

**`catchup=False`**: Quan trọng — DAG **không tự chạy lại** từ `start_date` đến hiện tại khi mới tạo. Việc backfill dữ liệu lịch sử sẽ được thực hiện thủ công ở **Bước 6**.

**Lưu ý**: `start_date` phải là **ngày trong quá khứ**. Nếu đặt `start_date` là hôm nay thì Airflow sẽ chỉ chạy từ hôm nay trở đi.

---

### Bước 5: Cấu hình `run_mode` (backward/forward)

#### Nguyên tắc

- **`backward`**: Chạy từ hiện tại về quá khứ (ưu tiên dữ liệu mới). Đồng thời cũng cho phép chạy tiến.
- **`forward`**: Chỉ cho phép chạy tiến (từ quá khứ đến hiện tại).

Mặc định: toàn pipeline chạy `backward`.

#### Khi nào cần chuyển `forward`

Khi pipeline đã đủ dữ liệu về đến `start_date` và muốn chuyển sang chế độ chạy tiến bình thường.

#### Cách chuyển — CHỈ cần thay đổi ở job đầu tiên

**Không cần** thay đổi `run_mode` cho tất cả job. Chỉ cần thay đổi tại job `_origin.transaction_blocks` (job đầu tiên trong pipeline).

**Lý do**: Khi job `_origin.transaction_blocks` dừng chạy backward (tức là đã có dữ liệu đến ngày cần), các job phía sau dù vẫn set `backward` cũng **không thể chạy tiếp về quá khứ** nữa vì không có data mới hơn để xử lý.

#### Cach thay đổi

**Trong `application.properties`** (thay đổi chung):
```properties
run_mode=forward
```

**Hoặc override trong file `.sh`** (chỉ áp dụng cho 1 job cụ thể):
```bash
$CHAINSLAKE_RUN_DIR/chainslake-run.sh ... \
    --conf "spark.app_properties.run_mode=forward" \
    ...
```

**Khuyến nghị**: Sử dụng `--conf` trong file `.sh` của `_origin.transaction_blocks` để chỉ thay đổi job đầu tiên, giữ nguyên các job khác ở `backward`.

---

### Bước 6: Backfill job mới thêm vào DAG

Khi DAG đã hoàn thành chạy dữ liệu về quá khứ, job mới thêm vào **phải tự chạy backfill** để có dữ liệu lịch sử.

#### Sử dụng Airflow CLI

```bash
# Backfill 1 task cụ thể
docker exec -u hadoop chainslake-onprem-node01-1 bash -c \
    "export PS1='something' && source /etc/bash.bashrc && \
     airflow tasks run <DAG_ID> <TASK_ID> <EXECUTION_DATE> --run-backwards"

# Ví dụ: Backfill task bnb_origin.transaction_blocks từ ngày 2025-10-11
docker exec -u hadoop chainslake-onprem-node01-1 bash -c \
    "export PS1='something' && source /etc/bash.bashrc && \
     airflow tasks run BNB bnb_origin.transaction_blocks 2025-10-11 --run-backwards"
```

#### Backfill toàn DAG (nếu cần)

```bash
docker exec -u hadoop chainslake-onprem-node01-1 bash -c \
    "export PS1='something' && source /etc/bash.bashrc && \
     airflow dags backfill -s 2025-10-11 -e <end_date> <DAG_ID>"
```

**Lưu ý**:
- `--run-backwards`: Chạy từ end_date về start_date (backward)
- Job mới sẽ chạy tuần tự theo dependency, nên các job upstream của nó cũng cần có data
- Nếu job mới nằm giữa pipeline (ví dụ: job extract mới), cần đảm bảo các job origin upstream đã có data

---

## Ví dụ thực tế

### Setup mới BNB Chain

```properties
# application.properties
chain_name=bnb
number_block_per_partition=1000      # ~3s/block → 1200 blocks/giờ → 1000 (buffer 5%)
max_number_partition=1               # local[2] + 4g
max_time_run=24                      # 24 vòng × 1 partition = 24 partitions = 1 ngày
run_mode=backward
```

```python
from datetime import datetime, timedelta

# DAG bnb.py
start_date=datetime.now() - timedelta(days=730),  # Mặc định 2 năm trước
catchup=False                                      # Không tự chạy lại
```

Sau khi chạy 1-2 lần, query để tính `number_block_per_partition` chính xác:

```sql
SELECT
    min(block_number) as min_b,
    max(block_number) as max_b,
    (max(block_number) - min(block_number)) as blocks_count
FROM bnb_origin.transaction_blocks
WHERE block_time >= unix_timestamp('2025-10-11 00:00:00')
  AND block_time < unix_timestamp('2025-10-11 01:00:00')
-- Kết quả: blocks_count = 1180 → number_block_per_partition = 1180 * 1.05 ≈ 1239
```

### Chuyển backward → forward

Sau khi chạy backfill đủ dữ liệu đến `start_date`:

```properties
# Trong application.properties của _origin.transaction_blocks (hoặc dùng --conf trong .sh)
run_mode=forward
```

### Thêm job mới vào DAG đã có data

Giả sử thêm `bnb.extract.new_table.sh`:

1. Tạo file `.sh` mới
2. Thêm task vào `bnb.py` DAG
3. Backfill riêng task mới:
```bash
docker exec -u hadoop chainslake-onprem-node01-1 bash -c \
    "export PS1='something' && source /etc/bash.bashrc && \
     airflow tasks run BNB bnb.new_table 2025-10-11 --run-backwards"
```

## Lưu ý / Gotchas

- **`number_block_per_partition` phải luôn > 0**: Nếu = 0 job sẽ lỗi hoặc chạy vô tận
- **`max_number_partition` cho `frequent_type=day`**: Bắt buộc >= 24
- **Ưu tiên `--conf` trong `.sh`**: Khi muốn thay đổi nhanh 1 job mà không muốn sửa `application.properties` chung
- **`run_mode=backward` linh hoạt hơn**: Cho phép chạy cả tiến và lùi, nên giữ nguyên ở các job ngoại trừ job origin đầu tiên khi muốn dừng chạy lùi
- **Backfill cần đúng execution_date**: Phải là ngày mà DAG chưa có dữ liệu, nếu không Airflow sẽ bỏ qua
- **Memory cần > data read + data write**: Luôn để buffer, đặc biệt với partition lớn
