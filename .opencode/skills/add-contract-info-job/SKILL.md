---
name: add-contract-info-job
description: Tạo job lấy thông tin/metadata từ smart contract (name, symbol, decimals...) qua view functions trong ABI (register_evm_call), output ra bảng <chain>_contract với logic chống lặp contract_address
---

# Skill: Add Contract Info Job

## Mô tả
Hướng dẫn tạo job lấy thông tin/metadata từ smart contract (ví dụ: `name`, `symbol`, `decimals` của token ERC20) bằng cách gọi các **view function** khai báo trong ABI, output ra bảng metadata trong schema `<chain>_contract`. Job chỉ xử lý các contract MỚI xuất hiện mỗi lần chạy, không lặp lại `contract_address`.

## Điều kiện áp dụng
- Cần một bảng metadata chứa thông tin tĩnh của contract (name, symbol, decimals, ...)
- Đã có bảng event đã decode (`<chain>_decoded.<event_table>`) chứa cột `contract_address` và `block_number` — dùng để phát hiện contract nào xuất hiện
- Contract có các view function (`stateMutability: view`) trả về thông tin cần lấy

## Các bước thực hiện

### Bước 1: Tạo / kiểm tra ABI file

File tại `chainslake/evm/abi/<abi_name>.json` — **`<abi_name>` chính là tên function gọi trong SQL**. Ví dụ `erc20.json` → gọi `erc20(...)` trong SQL.

File chứa các function `view`/`constant` cần lấy thông tin:

```json
[
  {
    "constant": true,
    "inputs": [],
    "name": "name",
    "outputs": [{"name": "", "type": "string"}],
    "payable": false,
    "stateMutability": "view",
    "type": "function"
  },
  {
    "constant": true,
    "inputs": [],
    "name": "symbol",
    "outputs": [{"name": "", "type": "string"}],
    "payable": false,
    "stateMutability": "view",
    "type": "function"
  },
  {
    "constant": true,
    "inputs": [],
    "name": "decimals",
    "outputs": [{"name": "", "type": "uint256"}],
    "payable": false,
    "stateMutability": "view",
    "type": "function"
  }
]
```

**Naming convention**: ABI file named theo contract group (ví dụ: `erc20.json`), KHÔNG phải theo table name.

### Bước 2: Tạo SQL file

File tại `chainslake/sql/evm_contract/<job>.sql` (production) hoặc `<job>_dev.sql` (dev). Header:

```
frequent_type=block
list_input_tables=${chain_name}_decoded.<event_table>
register_evm_call=<abi_name>
max_num_files=200
output_table=${chain_name}_contract.<output_table>
write_mode=Append
number_index_columns=1
```

**Config header quan trọng**:
- `register_evm_call=<abi_name>`: Đăng ký ABI để SQL gọi được các view function. Giá trị = tên file ABI (bỏ `.json`)
- `list_input_tables`: Bảng event decoded dùng để phát hiện contract
- `output_table`: Bảng metadata output, schema `<chain>_contract`
- `number_index_columns=1`: `contract_address` là cột index 1 (dùng để chống duplicate)

Body SQL theo pattern sau (ví dụ `erc20_tokens.sql`):

```sql
with list_contract_address as (
    select distinct contract_address
    from ${list_input_tables}
    where block_number >= ${from} and block_number <= ${to}
)

${if table_existed}

, new_contract_address as (
    select new.contract_address from list_contract_address new
    left join ${output_table} old
    on new.contract_address = old.contract_address
    where old.name is null
)

, new_contract_address_repartition as (
    select /*+ REPARTITION(10) */ contract_address from new_contract_address
)

${else}

, new_contract_address_repartition as (
    select /*+ REPARTITION(10) */ contract_address from list_contract_address
)

${endif}

select contract_address
, current_timestamp() as updated_time
, <abi_name>(CONCAT(contract_address, ' name')) as name
, <abi_name>(CONCAT(contract_address, ' symbol')) as symbol
, cast(<abi_name>(CONCAT(contract_address, ' decimals')) as INT) as decimals
from new_contract_address_repartition
```

**Logic chống lặp `contract_address`**:
- `list_contract_address`: `select distinct` tất cả contract xuất hiện trong block range hiện tại
- `${if table_existed}`: Nếu output table đã tồn tại → `left join` với output table, giữ lại chỉ các contract chưa có (`old.name is null`) — nếu contract đã tồn tại, join với hàng output sẽ có `name != null` nên bị loại
- `${else}`: Lần chạy đầu tiên (table chưa tồn tại) → lấy toàn bộ

**Cách gọi view function**: `CONCAT(contract_address, ' <function_name>')` — tên function cách contract_address bằng 1 space. Function trả về string, nếu cần cast kiểu khác (ví dụ `decimals` → INT).

### Bước 3: Tạo `.sh` job script

File placement: `chainslake/jobs/<chain>/contract/<table_name>.sh`

```bash
export $(cat $CHAINSLAKE_RUN_DIR/.env) && $CHAINSLAKE_RUN_DIR/chainslake-run.sh --class chainslake.sql.Main \
    --master local[10] \
    --name <ChainName><OutputTableName> \
    --conf "spark.app_properties.app_name=sql.transformer" \
    --conf "spark.app_properties.config_file=<chain>/application.properties" \
    --conf "spark.app_properties.rpc_list=$<CHAIN>_RPCS" \
    --conf "spark.app_properties.sql_file=evm_contract/<job>.sql"
```

**Key configs**:
- `app_name=sql.transformer`: Job chạy SQL transformer
- `sql_file`: Trỏ đến file SQL đã tạo ở Bước 2
- `rpc_list=$<CHAIN>_RPCS`: Biến env từ `.env`, load bằng `export $(cat $CHAINSLAKE_RUN_DIR/.env)`
- Spark app name: PascalCase, ví dụ `EthereumERC20Tokens`

### Bước 4: Chạy test (dev, dùng `_dev` suffix)

Với dev: tạo `evm_contract/<job>_dev.sql` output ra `${chain_name}_contract.<output_table>_dev`, và `.sh` trỏ đến file `_dev.sql`.

```bash
docker exec -u hadoop chainslake-onprem-node01-1 bash -c \
  "export PS1='something' && source /etc/bash.bashrc && \
   cd /home/hadoop/projects/chainslake/jobs/<chain> && \
   ./contract/<table_name>.sh" 2>&1
```

### Bước 5: Verify data

```bash
python query/query_table.py "SELECT count(*) FROM <chain>_contract.<output_table>"
python query/query_table.py "SELECT contract_address, name, symbol, decimals FROM <chain>_contract.<output_table> LIMIT 5"
python query/query_table.py "SELECT count(*) FROM (<chain>_contract.<output_table>) t GROUP BY contract_address HAVING count(*) > 1"  # phải = 0 (không lặp)
python query/get_example_table.py <chain>_contract.<output_table>
```

### Bước 6: Thêm vào Airflow DAG

Thêm `BashOperator` vào DAG của chain (`chainslake/airflow/dags/<chain>.py`), đặt sau task decoded event là input, trước các job downstream:

```python
<chain>_contract_<output_table> = BashOperator(
    task_id="<chain>_contract.<output_table>",
    bash_command=f"cd {RUN_DIR} && ./contract/<table_name>.sh "
)

<chain>_decoded_<event_table> >> <chain>_contract_<output_table>
<chain>_contract_<output_table> >> <downstream_task>
```

## Lưu ý / Gotchas

- **`register_evm_call` = tên file ABI** (bỏ `.json`): `erc20` → file `erc20.json`, gọi `erc20('0x... name')` trong SQL. Đây là cơ chế map function → ABI
- **Cú pháp gọi function**: `<abi_name>(CONCAT(contract_address, ' <function_name>'))` — có 1 space giữa address và tên function, tên function phải khớp chính xác với `"name"` trong ABI
- **Chống lặp**: Điều kiện lọc contract mới dùng cột của output table đã có dữ liệu (ví dụ `old.name is null`). Nếu function call trả về `NULL` cho contract không implement function, contract đó sẽ được coi là "mới" và bị gọi lại ở lần chạy sau
- **`write_mode=Append`**: Bắt buộc vì job chỉ thêm contract mới, KHÔNG overwrite toàn bộ table
- **`number_index_columns=1`**: `contract_address` là index column → được dùng làm khóa chống duplicate
- **Input phải có cột `contract_address` và `block_number`** — nếu bảng decoded không có 2 cột này thì không dùng được pattern này
- **Function trả về string**: `decimals` là `uint256` trong ABI nhưng function call trả về dạng string → cần `cast(... as INT)`
- **Dev convention**: Dùng `_dev` suffix cho output table và SQL file, tránh đọc/ghi production table

## Ví dụ thực tế
- Job: `chainslake/jobs/ethereum/contract/erc20_tokens.sh`
- SQL: `chainslake/sql/evm_contract/erc20_tokens.sql`
- ABI: `chainslake/evm/abi/erc20.json`
- Output: `ethereum_contract.erc20_tokens` (name, symbol, decimals), input `ethereum_decoded.erc20_evt_transfer`
- DAG: `chainslake/airflow/dags/ethereum.py` — `ethereum_decoded_erc20_evt_transfer >> ethereum_contract_erc20_tokens >> ethereum_token_erc20_transfer`
