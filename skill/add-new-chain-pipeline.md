# Skill: Add New Chain Pipeline

## Mô tả
Hướng dẫn tạo một data pipeline hoàn chỉnh cho một EVM-compatible blockchain mới trong hệ thống Chainslake Onprem, bao gồm: tìm RPC, cập nhật `.env`, tạo job scripts, và tạo Airflow DAG.

## Điều kiện áp dụng
- Khi người dùng muốn thêm một blockchain EVM mới (ví dụ: BNB, Polygon, Arbitrum, Base, v.v.)
- Chain cần tương thích với các API: `eth_blockNumber`, `eth_getBlockByNumber`, `eth_getBlockReceipts`

## Các bước thực hiện

### Bước 1: Lấy và kiểm tra danh sách RPC

Dùng script tái sử dụng `script/check_rpcs.py` (không cần viết script mới cho mỗi chain):

```bash
# Theo chainId (khuyến nghị)
python script/check_rpcs.py <CHAIN_ID>

# Ví dụ
python script/check_rpcs.py 56          # BNB → tự suy BNB_RPCS
python script/check_rpcs.py 137         # Polygon → tự suy POLYGON_RPCS
python script/check_rpcs.py 1 --env-var ETHEREUM_RPCS

# Tùy chỉnh thêm
python script/check_rpcs.py 56 --timeout 15 --workers 20
```

Script sẽ:
- Tự động lấy danh sách RPC từ chainlist.org theo chainId
- Kiểm tra song song: `eth_blockNumber` → `eth_getBlockByNumber` → `eth_getBlockReceipts`
- In ra dòng `<ENV_VAR>=...` để copy vào `.env`

**Tra cứu chainId**: https://chainlist.org (hoặc https://chainid.network)

### Bước 2: Cập nhật `chainslake-run/.env`

Append dòng sau vào cuối file `.env`:
```
<CHAIN_UPPER>_RPCS=<danh_sách_rpc_pass_phân_cách_bằng_dấu_phẩy>
```

Ví dụ: `BNB_RPCS=https://bsc-dataseed1.ninicoin.io,...`

### Bước 3: Tạo `jobs/<chain_name>/application.properties`

Copy từ `jobs/ethereum/application.properties`, thay đổi:
- `chain_name=<chain_name>` (ví dụ: `bnb`, `polygon`)
- `rpc_name=<Tên đầy đủ của chain>` (ví dụ: `BNB Smart Chain Mainnet`)
- `number_block_per_partition`: chỉnh theo tốc độ block của chain
  - Ethereum (~12s/block): 300
  - BNB (~3s/block): 1000
  - Polygon (~2s/block): 1500
- `origin_table=<chain_name>.blocks`

### Bước 4: Tạo các job scripts

Tạo đầy đủ cấu trúc thư mục và các file `.sh`:

```
jobs/<chain_name>/
├── application.properties
├── origin/
│   ├── transaction_blocks.sh   ← dùng $<CHAIN>_RPCS, app_name=evm_origin.transaction_blocks
│   └── blocks_receipt.sh       ← dùng $<CHAIN>_RPCS, app_name=evm_origin.blocks_receipt
├── extract/
│   ├── blocks.sh               ← sql.transformer, sql_file=evm/blocks.sql
│   ├── transactions.sh         ← dùng $<CHAIN>_RPCS, app_name=evm.transactions
│   └── logs.sh                 ← dùng $<CHAIN>_RPCS, app_name=evm.logs
├── contract/
│   ├── decoded_log.sh          ← sql.transformer, sql_file=evm_contract/decode_log.sql, nhận $1 $2
│   └── erc20_tokens.sh         ← sql.transformer, sql_file=evm_contract/erc20_tokens.sql
└── token/
    └── erc20_transfer.sh       ← sql.transformer, sql_file=evm_token/erc20_transfer.sql
```

Naming convention cho `--name` trong spark-submit:
- Format: `<ChainName><JobName>` (PascalCase, không có dấu gạch ngang)
- Ví dụ: `BnbOriginBlocksReceipt`, `BnbBlocks`, `BnbDecodedLog`

Sau khi tạo: `chmod +x jobs/<chain_name>/**/*.sh`

### Bước 5: Tạo Airflow DAG

Tạo `chainslake/airflow/dags/<chain_name>.py`, copy từ `ethereum.py` và thay thế:
- DAG name: `"<CHAIN_UPPER>"`
- `RUN_DIR` path: `"/jobs/<chain_name>"`
- Tất cả prefix `ethereum_` → `<chain_name>_`
- `task_id` theo naming: `<chain_name>_origin.transaction_blocks`, `<chain_name>.blocks`, v.v.

Dependency graph chuẩn:
```
origin_transaction_blocks → origin_blocks_receipt
origin_blocks_receipt → [blocks, transactions, logs]
logs → decoded_erc20_evt_transfer
decoded_erc20_evt_transfer → contract_erc20_tokens
[transactions, decoded_erc20_evt_transfer] → token_erc20_transfer
contract_erc20_tokens → token_erc20_transfer
```

## Lưu ý / Gotchas

- **`number_block_per_partition`**: BNB ra ~1 block/3 giây, nên dùng 1000 để mỗi partition ≈ ~50 phút dữ liệu
- **Biến env trong .sh**: Các job origin và extract/transactions, extract/logs cần `export $(cat $CHAINSLAKE_RUN_DIR/.env)` ở đầu để load RPC list. Job `blocks.sh` (dùng sql.transformer) không cần.
- **`decoded_log.sh` nhận tham số**: Script này nhận `$1` (table_name) và `$2` (run_mode) như Ethereum, không hardcode
- **RPC check**: Một số RPC trả về `result=null` cho `eth_getBlockReceipts` — đây là dấu hiệu không hỗ trợ, phải loại bỏ
- **Timeout**: Dùng timeout=10s khi check RPC; một số RPC chạy chậm nhưng vẫn hợp lệ — tăng lên 15s nếu cần

## Ví dụ thực tế
- Lần đầu áp dụng: BNB Smart Chain Mainnet (chainId=56), ngày 2026-07-10
- 52 RPC kiểm tra → 20 PASS, 32 FAIL
- Lệnh dùng: `python script/check_rpcs.py 56`
- File tham chiếu: `jobs/bnb/`, `airflow/dags/bnb.py`
