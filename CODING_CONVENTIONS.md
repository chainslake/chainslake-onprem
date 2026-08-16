# CODING_CONVENTIONS.md — Chainslake Coding Conventions

> Conventions dự án **BẮT BUỘC tuân thủ** khi phát triển job/pipeline.

## 1. Cấu trúc pipeline cho một blockchain mới

```
chainslake/jobs/<chain_name>/
├── application.properties
├── origin/          # Job lấy dữ liệu thô từ RPC
├── extract/         # Job biến đổi dữ liệu thô
├── contract/        # Job decode smart contract
└── token/           # Job tạo bảng dữ liệu token (nếu có)
```

## 2. Cấu trúc file `.sh` (job script)

Mỗi job script gọi `chainslake-run.sh` với các tham số:
- `--class`: Java/Scala class cần thực thi
- `--name`: Tên Spark app (format: `<ChainName><JobName>`)
- `--conf spark.app_properties.app_name`: Tên app logic
- `--conf spark.app_properties.config_file`: Path đến `application.properties`

**Ví dụ chuẩn (job dùng `sql.transformer`):**
```bash
$CHAINSLAKE_RUN_DIR/chainslake-run.sh --class chainslake.sql.Main \
    --name EthereumBlocks \
    --conf "spark.app_properties.app_name=sql.transformer" \
    --conf "spark.app_properties.config_file=ethereum/application.properties" \
    --conf "spark.app_properties.sql_file=evm/blocks.sql"
```

**Ví dụ chuẩn (job origin, cần load `.env`):**
```bash
export $(cat $CHAINSLAKE_RUN_DIR/.env) && $CHAINSLAKE_RUN_DIR/chainslake-run.sh --class chainslake.evm.Main \
    --name EthereumOriginBlocksReceipt \
    --conf "spark.app_properties.app_name=evm_origin.blocks_receipt" \
    --conf "spark.app_properties.rpc_list=$ETHEREUM_RPCS" \
    --conf "spark.app_properties.config_file=ethereum/application.properties"
```

## 3. Cấu trúc file `.sql`

Mỗi file `.sql` gồm hai phần phân tách bởi `===`:

```
<header: key=value config>
===
<body: SQL logic>
```

**Các config header quan trọng:**

| Config | Mô tả |
|---|---|
| `frequent_type` | Loại tần suất xử lý: `block`, `day`, v.v. |
| `list_input_tables` | Bảng input, dùng `${chain_name}` làm prefix schema |
| `output_table` | Bảng output |
| `partition_by` | Cột partition |
| `write_mode` | `Append` hoặc `Overwrite` |
| `number_index_columns` | Số cột index đầu tiên |

**Biến động trong SQL:**
- `${chain_name}` — tên blockchain, lấy từ `application.properties`
- `${from}`, `${to}` — range block của lần chạy hiện tại, hệ thống tự tính
- `${table_name}` — tham chiếu đến bảng input trong phần body (dùng tên bảng không có schema)

## 4. Naming convention cho bảng

| Schema | Mô tả | Ví dụ |
|---|---|---|
| `<chain>_origin` | Dữ liệu thô từ RPC | `ethereum_origin.transaction_blocks` |
| `<chain>` | Dữ liệu chuẩn hóa | `ethereum.blocks`, `ethereum.transactions` |
| `<chain>_decoded` | Dữ liệu contract đã decode | `ethereum_decoded.erc20_evt_transfer` |
| `<chain>_contract` | Metadata contract | `ethereum_contract.erc20_tokens` |
| `<chain>_token` | Dữ liệu token tổng hợp | `ethereum_token.erc20_transfer` |

## 5. Cấu trúc Airflow DAG

- Một DAG per blockchain
- Schedule mặc định: `"10 0 * * *"` (chạy lúc 0:10 mỗi ngày)
- `max_active_runs=1`, `max_active_tasks=10`
- `is_paused_upon_creation=True`
- Thứ tự task theo dependency thực tế của dữ liệu
- Dùng `BashOperator` gọi trực tiếp shell script tương ứng
