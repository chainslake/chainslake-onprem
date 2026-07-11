# Skill: Run DAG and Verify Data

## Mô tả
Trigger một Airflow DAG (mặc định Ethereum), theo dõi tiến trình直到hoàn thành, và kiểm tra dữ liệu trong các bảng sau khi chạy.

## Điều kiện áp dụng
- Docker containers đã chạy (`docker compose up -d`)
- Airflow đang hoạt động (port 58080)
- DAG đã tồn tại và cấu hình đúng
- RPC endpoints đã được cấu hình trong `chainslake-run/.env`

## Các bước thực hiện

### Bước 1: Kiểm tra `.env` có RPC chưa

```bash
cat chainslake-run/.env
```

Nếu chưa có hoặc trống, cần chạy `python script/check_rpcs.py <chain_id>` trước.

### Bước 2: Trigger và monitor DAG

```bash
python script/trigger_dag.py Ethereum
```

Script chạy Airflow CLI bên trong container qua `docker exec`:
1. Pause DAG để tránh conflict với runs đang chạy
2. Unpause DAG
3. Trigger manual run
4. Poll status mỗi 30s cho đến khi success/failed

**Tham số tuỳ chọn:**
```bash
# Trigger rồi thoát ngay (không chờ)
python script/trigger_dag.py Ethereum --no-wait

# Chỉ xem status
python script/trigger_dag.py Ethereum --status

# Pause DAG và xem runs đang active
python script/trigger_dag.py Ethereum --cancel-all

# Custom poll interval
python script/trigger_dag.py Ethereum --poll-interval 60
```

### Bước 3: Verify dữ liệu

Sau khi DAG success, kiểm tra data:

```bash
# Kiểm tra số dòng mỗi bảng
python query/query_table.py "SELECT count(*) as total FROM ethereum.blocks LIMIT 1"
python query/query_table.py "SELECT count(*) as total FROM ethereum.transactions LIMIT 1"
python query/query_table.py "SELECT count(*) as total FROM ethereum.logs LIMIT 1"
python query/query_table.py "SELECT count(*) as total FROM ethereum_decoded.erc20_evt_transfer LIMIT 1"
python query/query_table.py "SELECT count(*) as total FROM ethereum_contract.erc20_tokens LIMIT 1"
python query/query_table.py "SELECT count(*) as total FROM ethereum_token.erc20_transfer LIMIT 1"

# Xem schema và data mẫu
python query/get_example_table.py ethereum.blocks
python query/get_example_table.py ethereum.transactions
```

## Dependency graph của Ethereum DAG

```
origin.transaction_blocks → origin.blocks_receipt
origin.blocks_receipt → [blocks, transactions, logs]
logs → decoded.erc20_evt_transfer
decoded.erc20_evt_transfer → contract.erc20_tokens
[transactions, decoded.erc20_evt_transfer, contract.erc20_tokens] → token.erc20_transfer
```

8 tasks, chạy tuần tự theo LocalExecutor.

## Lưu ý / Gotchas

### Airflow CLI
Script dùng `docker exec` gọi `airflow` CLI bên trong container `chainslake-onprem-node01-1`.
- Container phải đang chạy (`docker ps | grep node01`)
- User thực thi: `hadoop`
- Không cần HTTP auth hay credentials — CLI dùng local auth tự động

### Hạn chế: Cancel run
Airflow CLI **không có lệnh trực tiếp** để cancel một DAG run.
- `--cancel-all` sẽ **pause DAG** + báo cáo các runs đang active
- Các task đang chạy sẽ tự hoàn thành, không thể force stop qua CLI
- Nếu cần cancel thực sự, dùng Airflow UI trên port 58080

### RPC rate limiting
Nếu chỉ có 1-2 RPCs, job origin có thể fail với lỗi:
- `Max number retry` — RPC bị rate limit
- `Expected BEGIN_ARRAY but was BEGIN_OBJECT` — RPC trả về lỗi JSON-RPC

**Giải pháp:**
1. Chạy `check_rpcs.py` với nhiều RPCs hơn
2. Tăng `wait_miliseconds` trong `application.properties` (mặc định 100 → thử 500)
3. Giảm `max_concurrent_blocks` (mặc định 100 → thử 10)

### DAG auto-backfill
Khi unpause DAG, Airflow có thể tự tạo scheduled run cho khoảng thời gian DAG bị pause.
- Schedule run cũ có thể fail do thiếu `.env`
- Solution: cancel tất cả runs trước khi trigger manual

### LocalExecutor
Airflow standalone dùng LocalExecutor — chỉ chạy **1 task tại một thời điểm**.
- 8 tasks Ethereum có thể mất 30-60 phút tùy RPC speed
- Tasks chạy tuần tự theo dependency graph

## Ví dụ thực tế
- Ngày: 2026-07-11
- 12 RPCs pass (check_rpcs.py với condition relax)
- 8/8 tasks succeeded
- 301 blocks, 163k transactions, 190k logs, 120k ERC20 transfers
