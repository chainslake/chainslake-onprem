---
name: add-contract-decode-job
description: Create a job to decode smart contract events from logs into a separate decoded table using decode_log.sql template — used when decoding new events from an EVM chain, output table <chain>_decoded.<table_name>
---

# Skill: Add Contract Decode Job

## Description
Guide to creating a job that decodes smart contract events from `ethereum.logs` into a separate decoded table, using the `decode_log.sql` template.

## When to Use
- When you need to decode a new event from a smart contract on an EVM chain
- The event has a clear topic0 signature and ABI
- The output table belongs to the `<chain>_decoded` schema

## Implementation Steps

### Step 1: Create ABI File

Create file `chainslake/evm/abi/<contract_name>.json` containing a JSON array with event definitions:

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

**Naming convention**: ABI file is named after the contract group (e.g., `uniswap_v3.json`, `erc20.json`), NOT the full table name.

### Step 2: Create SQL File (if custom needed)

- If using standard template: use `evm_contract/decode_log.sql` (for production)
- If `_dev` suffix needed: create `evm_contract/decode_log_dev.sql` with header:
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

### Step 3: Create `.sh` Job Script

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
- `table_name`: Base name for ABI lookup and temp table (e.g., `uniswap_v3_evt_swap`)
- `sql_file`: Template SQL file
- Spark app name: PascalCase, format `<ChainName>Decoded<EventName>`

### Step 4: Shallow Clone Input Tables (for dev)

```bash
python query/shallow_clone.py ethereum.logs  # Creates ethereum.logs_dev
```

### Step 5: Run Test

Run the job with the job runner (wraps `docker exec` internally — do NOT call `docker exec` directly):

```bash
python script/run_job.py <chain>/decoded/<table_name>.sh
```

### Step 6: Verify Data

```bash
python query/query_table.py "SELECT count(*) FROM <chain>_decoded.<table_name>_dev"
python query/query_table.py "SELECT * FROM <chain>_decoded.<table_name>_dev LIMIT 5"
```

## Notes / Gotchas

- **ABI file mapping**: The decode engine strips the `_evt_*` suffix from `table_name` to find the ABI file. Example: `uniswap_v3_evt_swap` → searches for `uniswap_v3.json`
- **`pre_decode_tables`**: Used as the temp table name by the decode engine, does NOT need `_dev` suffix
- **`list_input_tables`**: Must point to `_dev` version when running dev (avoid reading production)
- **Curve ABI**: Has multiple variants (Router, StableSwap, TriCrypto) — put all in one JSON array file
- **Balancer V2**: Pool address = `substr(pool_id, 1, 42)` (first 20 bytes of bytes32)

## Real-world Example
- First applied: 5 decoded tables for daily_dex_token_volume, on 2026-07-26
- Tables: uniswap_v3_evt_swap, uniswap_v2_evt_swap, sushiswap_evt_swap, curve_evt_tokenexchange, balancer_v2_evt_swap