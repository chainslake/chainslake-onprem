---
name: add-contract-info-job
description: Create a job to fetch contract metadata (name, symbol, decimals...) via view functions in ABI (register_evm_call), output to <chain>_contract table with deduplication logic for contract_address
---

# Skill: Add Contract Info Job

## Description
Guide to creating a job that fetches contract metadata (e.g., ERC20 token `name`, `symbol`, `decimals`) by calling **view functions** declared in the ABI, outputting to a metadata table in the `<chain>_contract` schema. The job only processes NEW contracts on each run, avoiding duplicate `contract_address` entries.

## When to Use
- You need a metadata table containing static contract information (name, symbol, decimals, ...)
- A decoded event table (`<chain>_decoded.<event_table>`) exists with `contract_address` and `block_number` columns — used to detect which contracts appear
- The contract has view functions (`stateMutability: view`) that return the needed information

## Implementation Steps

### Step 1: Create / Verify ABI File

File at `chainslake/evm/abi/<abi_name>.json` — **`<abi_name>` is the function name called in SQL**. Example: `erc20.json` → call `erc20(...)` in SQL.

The file contains `view`/`constant` functions to retrieve information:

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

**Naming convention**: ABI file is named after the contract group (e.g., `erc20.json`), NOT after the table name.

### Step 2: Create SQL File

File at `chainslake/sql/evm_contract/<job>.sql` (production) or `<job>_dev.sql` (dev). Header:

```
frequent_type=block
list_input_tables=${chain_name}_decoded.<event_table>
register_evm_call=<abi_name>
max_num_files=200
output_table=${chain_name}_contract.<output_table>
write_mode=Append
number_index_columns=1
```

**Important header configs**:
- `register_evm_call=<abi_name>`: Registers the ABI so SQL can call view functions. Value = ABI file name (without `.json`)
- `list_input_tables`: Decoded event table used to detect contracts
- `output_table`: Output metadata table, schema `<chain>_contract`
- `number_index_columns=1`: `contract_address` is the first index column (used for deduplication)

Body SQL follows this pattern (example `erc20_tokens.sql`):

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

**Contract address deduplication logic**:
- `list_contract_address`: `select distinct` all contracts appearing in the current block range
- `${if table_existed}`: If output table already exists → `left join` with output table, keeping only contracts not yet present (`old.name is null`) — if contract already exists, the join with output row will have `name != null` so it gets excluded
- `${else}`: First run (table doesn't exist yet) → take all contracts

**How to call view functions**: `CONCAT(contract_address, ' <function_name>')` — function name separated from contract_address by 1 space. Function returns string, cast if needed for other types (e.g., `decimals` → INT).

### Step 3: Create `.sh` Job Script

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
- `app_name=sql.transformer`: Job runs SQL transformer
- `sql_file`: Points to the SQL file created in Step 2
- `rpc_list=$<CHAIN>_RPCS`: Env variable from `.env`, loaded via `export $(cat $CHAINSLAKE_RUN_DIR/.env)`
- Spark app name: PascalCase, e.g., `EthereumERC20Tokens`

### Step 4: Run Test (dev, using `_dev` suffix)

For dev: create `evm_contract/<job>_dev.sql` outputting to `${chain_name}_contract.<output_table>_dev`, and `.sh` pointing to `_dev.sql` file.

Run the job with the job runner (wraps `docker exec` internally — do NOT call `docker exec` directly):

```bash
python script/run_job.py <chain>/contract/<table_name>.sh
```

### Step 5: Verify Data

```bash
python query/query_table.py "SELECT count(*) FROM <chain>_contract.<output_table>"
python query/query_table.py "SELECT contract_address, name, symbol, decimals FROM <chain>_contract.<output_table> LIMIT 5"
python query/query_table.py "SELECT count(*) FROM (<chain>_contract.<output_table>) t GROUP BY contract_address HAVING count(*) > 1"  # must be 0 (no duplicates)
python query/get_example_table.py <chain>_contract.<output_table>
```

### Step 6: Add to Airflow DAG

Add a `BashOperator` to the chain's DAG (`chainslake/airflow/dags/<chain>.py`), placed after the decoded event task as input, before downstream jobs:

```python
<chain>_contract_<output_table> = BashOperator(
    task_id="<chain>_contract.<output_table>",
    bash_command=f"cd {RUN_DIR} && ./contract/<table_name>.sh "
)

<chain>_decoded_<event_table> >> <chain>_contract_<output_table>
<chain>_contract_<output_table> >> <downstream_task>
```

## Notes / Gotchas

- **`register_evm_call` = ABI file name** (without `.json`): `erc20` → file `erc20.json`, calls `erc20('0x... name')` in SQL. This is the function-to-ABI mapping mechanism
- **Function call syntax**: `<abi_name>(CONCAT(contract_address, ' <function_name>'))` — 1 space between address and function name, function name must exactly match `"name"` in ABI
- **Deduplication**: The filter condition for new contracts uses a column from the output table that already has data (e.g., `old.name is null`). If the function call returns `NULL` for a contract that doesn't implement the function, that contract will be considered "new" and called again in the next run
- **`write_mode=Append`**: Required because the job only adds new contracts, does NOT overwrite the entire table
- **`number_index_columns=1`**: `contract_address` is an index column → used as the deduplication key
- **Input must have `contract_address` and `block_number` columns** — if the decoded table doesn't have these 2 columns, this pattern cannot be used
- **Function returns string**: `decimals` is `uint256` in ABI but the function call returns it as a string → needs `cast(... as INT)`
- **Dev convention**: Use `_dev` suffix for output table and SQL file, avoid reading/writing production tables

## Real-world Example
- Job: `chainslake/jobs/ethereum/contract/erc20_tokens.sh`
- SQL: `chainslake/sql/evm_contract/erc20_tokens.sql`
- ABI: `chainslake/evm/abi/erc20.json`
- Output: `ethereum_contract.erc20_tokens` (name, symbol, decimals), input `ethereum_decoded.erc20_evt_transfer`
- DAG: `chainslake/airflow/dags/ethereum.py` — `ethereum_decoded_erc20_evt_transfer >> ethereum_contract_erc20_tokens >> ethereum_token_erc20_transfer`