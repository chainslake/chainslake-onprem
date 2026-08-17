# CODING_CONVENTIONS.md — Chainslake Coding Conventions

> Project conventions that **MUST be followed** when developing jobs/pipelines.

## 1. Pipeline Structure for a New Blockchain

```
chainslake/jobs/<chain_name>/
├── application.properties
├── origin/          # Jobs that fetch raw data from RPC
├── extract/         # Jobs that transform raw data
├── contract/        # Jobs that decode smart contracts
└── token/           # Jobs that create token data tables (if applicable)
```

## 2. `.sh` File Structure (Job Script)

Each job script calls `chainslake-run.sh` with the following parameters:
- `--class`: Java/Scala class to execute
- `--name`: Spark app name (format: `<ChainName><JobName>`)
- `--conf spark.app_properties.app_name`: Logic app name
- `--conf spark.app_properties.config_file`: Path to `application.properties`

**Standard example (job using `sql.transformer`):**
```bash
$CHAINSLAKE_RUN_DIR/chainslake-run.sh --class chainslake.sql.Main \
    --name EthereumBlocks \
    --conf "spark.app_properties.app_name=sql.transformer" \
    --conf "spark.app_properties.config_file=ethereum/application.properties" \
    --conf "spark.app_properties.sql_file=evm/blocks.sql"
```

**Standard example (origin job, needs `.env` loaded):**
```bash
export $(cat $CHAINSLAKE_RUN_DIR/.env) && $CHAINSLAKE_RUN_DIR/chainslake-run.sh --class chainslake.evm.Main \
    --name EthereumOriginBlocksReceipt \
    --conf "spark.app_properties.app_name=evm_origin.blocks_receipt" \
    --conf "spark.app_properties.rpc_list=$ETHEREUM_RPCS" \
    --conf "spark.app_properties.config_file=ethereum/application.properties"
```

## 3. `.sql` File Structure

Each `.sql` file consists of two sections separated by `===`:

```
<header: key=value configuration>
===
<body: SQL logic>
```

**Important header configurations:**

| Config | Description |
|---|---|
| `frequent_type` | Processing frequency type: `block`, `day`, etc. |
| `list_input_tables` | Input tables, use `${chain_name}` as schema prefix |
| `output_table` | Output table |
| `partition_by` | Partition column |
| `write_mode` | `Append` or `Overwrite` |
| `number_index_columns` | Number of leading index columns |

**Dynamic variables in SQL:**
- `${chain_name}` — blockchain name, sourced from `application.properties`
- `${from}`, `${to}` — block range for the current run, auto-calculated by the system
- `${table_name}` — reference to input tables in the body section (use table name without schema)

## 4. Table Naming Conventions

| Schema | Description | Example |
|---|---|---|
| `<chain>_origin` | Raw data from RPC | `ethereum_origin.transaction_blocks` |
| `<chain>` | Normalized data | `ethereum.blocks`, `ethereum.transactions` |
| `<chain>_decoded` | Decoded contract data | `ethereum_decoded.erc20_evt_transfer` |
| `<chain>_contract` | Contract metadata | `ethereum_contract.erc20_tokens` |
| `<chain>_token` | Aggregated token data | `ethereum_token.erc20_transfer` |

## 5. Airflow DAG Structure

- One DAG per blockchain
- Default schedule: `"10 0 * * *"` (runs at 0:10 daily)
- `max_active_runs=1`, `max_active_tasks=10`
- `is_paused_upon_creation=True`
- Task order follows actual data dependencies
- Use `BashOperator` to directly invoke corresponding shell scripts