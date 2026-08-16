---
name: add-contract-decode-job
description: Tạo job decode smart contract event từ logs thành bảng decoded riêng biệt dùng template decode_log.sql — dùng khi cần decode event mới từ EVM chain, output bảng <chain>_decoded.<table_name>
---

# Skill: Add Contract Decode Job

## Mô tả
Hướng dẫn tạo job decode smart contract event từ `ethereum.logs` thành bảng decoded riêng biệt, sử dụng template `decode_log.sql`.

## Điều kiện áp dụng
- Khi cần decode một event mới từ smart contract trên EVM chain
- Event có topic0 signature và ABI rõ ràng
- Output bảng nằm trong schema `<chain>_decoded`

## Các bước thực hiện

### Bước 1: Tạo ABI file

Tạo file `chainslake/evm/abi/<contract_name>.json` với nội dung JSON array chứa event definition:

```json
[
  {
    "anonymous": false,
    "inputs": [
      {"indexed": true, "name": "param1", "type": "address"},
      {"indexed": false, "name": "param2", "type": "uint256"}
    ],
    "name": "EventName",
    "type": "event"
  }
]
```

**Naming convention**: ABI file named sau contract group (ví dụ: `uniswap_v3.json`, `erc20.json`), KHÔNG phải full table name.

### Bước 2: Tạo SQL file (nếu cần custom)

- Nếu dùng template chuẩn: dùng `evm_contract/decode_log.sql` (cho production)
- Nếu cần `_dev` suffix: tạo `evm_contract/decode_log_dev.sql` với header:
  ```
  frequent_type=block
  list_input_tables=${chain_name}.logs_dev
  logs_table_name=${chain_name}.logs_dev
  pre_decode_tables=${table_name}
  output_table=${chain_name}_decoded.${table_name}_dev
  re_partition_by_range=block_date,block_time
  partition_by=block_date
  write_mode=Append
  number_index_columns=3
  ```

### Bước 3: Tạo `.sh` job script

File placement: `chainslake/jobs/<chain>/decoded/<table_name>.sh`

```bash
$CHAINSLAKE_RUN_DIR/chainslake-run.sh --class chainslake.sql.Main \
    --name <ChainName>Decoded<EventName> \
    --conf "spark.app_properties.app_name=sql.transformer" \
    --conf "spark.app_properties.table_name=<table_name>" \
    --conf "spark.app_properties.config_file=<chain>/application.properties" \
    --conf "spark.app_properties.sql_file=evm_contract/decode_log.sql"
```

**Key configs**:
- `table_name`: Tên base cho ABI lookup và temp table (ví dụ: `uniswap_v3_evt_swap`)
- `sql_file`: Template SQL file
- Spark app name: PascalCase, format `<ChainName>Decoded<EventName>`

### Bước 4: shallow clone input tables (cho dev)

```bash
python query/shallow_clone.py ethereum.logs  # Tạo ethereum.logs_dev
```

### Bước 5: Chạy test

```bash
docker exec -u hadoop chainslake-onprem-node01-1 bash -c \
  "export PS1='something' && source /etc/bash.bashrc && \
   cd /home/hadoop/projects/chainslake/jobs/<chain> && \
   ./decoded/<table_name>.sh" 2>&1
```

### Bước 6: Verify data

```bash
python query/query_table.py "SELECT count(*) FROM <chain>_decoded.<table_name>_dev"
python query/query_table.py "SELECT * FROM <chain>_decoded.<table_name>_dev LIMIT 5"
```

## Lưu ý / Gotchas

- **ABI file mapping**: Decode engine strip `_evt_*` suffix từ `table_name` để tìm ABI file. Ví dụ: `uniswap_v3_evt_swap` → tìm `uniswap_v3.json`
- **`pre_decode_tables`**: Được dùng làm tên temp table bởi decode engine, KHÔNG cần `_dev` suffix
- **`list_input_tables`**: Phải trỏ đến `_dev` version khi chạy dev (tránh đọc production)
- **Curve ABI**: Có nhiều variants (Router, StableSwap, TriCrypto) — đặt tất cả trong 1 file JSON array
- **Balancer V2**: Pool address = `substr(pool_id, 1, 42)` (20 bytes đầu của bytes32)

## Ví dụ thực tế
- Lần đầu áp dụng: 5 decoded tables cho daily_dex_token_volume, ngày 2026-07-26
- Tables: uniswap_v3_evt_swap, uniswap_v2_evt_swap, sushiswap_evt_swap, curve_evt_tokenexchange, balancer_v2_evt_swap
