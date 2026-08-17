# Chainslake Job Mechanics — Guide Book

This document describes the internal mechanics of jobs in the Chainslake system, helping users and Agents understand how data is processed, tracked, and ensured for accuracy — enabling precise pipeline configuration.

---

## Table of Contents

1. [Core Principle: 1 Job = 1 Table](#1-core-principle-1-job--1-table)
2. [Table Properties — Data Tracking Mechanism](#2-table-properties--data-tracking-mechanism)
3. [Upstream — Inter-table Dependency Network](#3-upstream--inter-table-dependency-network)
4. [Data Range Calculation Mechanism](#4-data-range-calculation-mechanism)
5. [Two Table Types: Block-based and Time-based](#5-two-table-types-block-based-and-time-based)
6. [Error Handling and Data Integrity Mechanisms](#6-error-handling-and-data-integrity-mechanisms)
7. [Job Execution Flow Summary](#7-job-execution-flow-summary)
8. [Real-world Examples](#8-real-world-examples)
9. [`pre_decode_tables` and `register_evm_call` Mechanics](#9-pre_decode_tables-and-register_evm_call-mechanics)

---

## 1. Core Principle: 1 Job = 1 Table

Every job in the Chainslake system is designed to write data into **exactly one table** in the data warehouse. This foundational principle helps:

- Accurately track processing progress for each table
- Manage dependencies between tables clearly
- Recover from errors without affecting other tables

When configuring a new job, you must clearly identify the **output** (output table) of that job. All processing logic revolves around transforming data from input tables to that single output table.

---

## 2. Table Properties — Data Tracking Mechanism

### 2.1 Concept

Each table in the data warehouse stores not only business data but also **metadata** in the form of **properties**. These properties are the key mechanism the system uses to know how far data in the table has been processed.

### 2.2 Data Range Tracking Properties

Depending on the table type (see [Section 5](#5-two-table-types-block-based-and-time-based)), the system uses one of two property pairs:

| Property Pair | Applies To | Description |
|---|---|---|
| `fromBlock`, `toBlock` | `frequentType=block` tables | Block_number range of data currently in the table |
| `fromEpochSecond`, `toEpochSecond` | `frequentType=minute/hour/day` tables | Time range (epoch seconds) of data currently in the table |

### 2.3 When Properties Are Updated

Properties are only updated **after data has been successfully written to the table** within one iteration (partition). Specifically:

```
Job starts running
    │
    ▼
Read properties of output table (if table exists)
    │
    ▼
Calculate data range to process
    │
    ▼
Process and write data (write to table)
    │
    ├── Success → Update properties (from/toBlock or from/toEpochSecond)
    │
    └── Failure → Properties NOT changed
```

**Why must properties only be updated after successful write?**

If properties were updated before writing completes, and the job crashes midway, the next run would assume data was already processed → **data gaps** with no self-healing mechanism. Updating after write ensures properties always accurately reflect actual data in the table.

---

## 3. Upstream — Inter-table Dependency Network

### 3.1 Upstream Concept

Every table (except **origin tables** — the starting tables sourced directly from RPC) has a list of input tables it depends on. This list is called **upstream**.

Upstream is declared in the `.sql` file via the `list_input_tables` property:

```sql
frequent_type=block
list_input_tables=${chain_name}_origin.transaction_blocks,${chain_name}_origin.blocks_receipt
output_table=${chain_name}.blocks
```

In this example, `ethereum.blocks` has upstream:
- `ethereum_origin.transaction_blocks`
- `ethereum_origin.blocks_receipt`

### 3.2 Where Upstream Is Stored

When a job runs, the upstream list is set into the **output table's properties**. This information helps:

- The system (and users) trace data lineage
- Downstream jobs know their dependencies
- Agents can automatically build dependency graphs

### 3.3 Origin Tables

Origin tables are the **starting tables** in the pipeline, with data fetched directly from blockchain RPC nodes. These tables **have no upstream** because they are the starting point of the entire processing chain.

In the current system, origin tables are typically in the `<chain_name>_origin` schema, e.g.:
- `ethereum_origin.transaction_blocks`
- `ethereum_origin.blocks_receipt`

---

## 4. Data Range Calculation Mechanism

### 4.1 Reading Properties When Job Starts

When a job is run, before processing data, the system performs:

1. **Read output table properties** — to know the current data range (from/to)
2. **Read properties of all upstream tables** — to know how far input data has been processed

### 4.2 Range Calculation Principle

The system calculates the data range to process in the current run based on: **all upstream tables must have sufficient data**.

This means the data range the job will process must be the **intersection** of available ranges across all upstreams, while also being **expanded** relative to the current output range (to process new data).

### 4.3 Supporting Both Backward and Forward

The system supports two processing directions:

| Mode | Description | Example |
|---|---|---|
| `backward` | Process from newest block to past | Output has data to block 1000, upstream has data to block 1100 → process blocks 1001–1100 |
| `forward` | Process from past to newest block | Output has data to block 1000, upstream has data to block 1100 → process blocks 1001–1100 |

In both cases, the system always ensures the processed data range has sufficient data from **all** upstream tables.

### 4.4 Handling Upstreams with Different Data Ranges

In practice, upstream tables may have data in different ranges. Example:

```
ethereum_origin.transaction_blocks:  block 0 → 1100  (fully processed)
ethereum_origin.blocks_receipt:      block 0 → 1050  (still processing)
ethereum.blocks (output):            block 0 → 1000  (fully processed)
```

In this case, the job calculates the processing range as block **1001 → 1050** (intersection of upstreams, expanded from output), because this is the range where both upstreams have complete data.

---

## 5. Two Table Types: Block-based and Time-based

Technically, tables are divided into 2 main types based on `frequentType`. This is the most important factor when configuring jobs, as it determines how the system tracks data and processes upstreams.

### 5.1 Type 1: `frequentType = block`

**Characteristics:**
- Tracks data by **block number** (`fromBlock`, `toBlock`)
- All upstream tables **must also have** `frequentType = block`
- Data range is determined by block range

**When to use:**
- Block-level data tables, each record corresponds to a blockchain block
- Origin tables (raw data from RPC)
- Extract/contract/token tables requiring precise block-level querying

**Example — `ethereum.blocks` table:**

```sql
frequent_type=block
list_input_tables=${chain_name}_origin.transaction_blocks,${chain_name}_origin.blocks_receipt
output_table=${chain_name}.blocks
```

Properties tracking:
```
fromBlock = 0
toBlock = 19500000
```

On next run, the system will process from block `19500001` onwards, ensuring both upstreams have data in that range.

### 5.2 Type 2: `frequentType = minute`, `hour`, or `day`

**Characteristics:**
- Tracks data by **time** (`fromEpochSecond`, `toEpochSecond`)
- Upstream tables **can have any frequentType**
- When upstream has `frequentType = block`, the system needs an **origin reference table** to map block_number → block_time

**When to use:**
- Time-aggregated tables (minute, hour, day)
- Analytics tables needing data in time frames

**Example — Daily table:**

```sql
frequent_type=day
list_input_tables=${chain_name}.blocks,${chain_name}.transactions
output_table=${chain_name}.daily_summary
```

Properties tracking:
```
fromEpochSecond = 1721942400    (2024-07-26 00:00:00 UTC)
toEpochSecond = 1722028800      (2024-07-27 00:00:00 UTC)
```

### 5.3 Handling Block-based Upstreams for Time-based Tables

When a table has `frequentType` as time-based but upstream has `frequentType` as block, the system needs to **convert block_number → block_time** to determine the corresponding time range.

Process:

```
1. Read properties of upstream (block-based): fromBlock, toBlock
2. Read origin_table (configured in application.properties, usually <chain>.blocks)
3. From origin_table, determine block_time corresponding to fromBlock and toBlock
4. Convert to fromEpochSecond and toEpochSecond
5. Calculate time range to process
```

This is why `application.properties` has:

```properties
origin_table=ethereum.blocks
```

This property specifies the reference table for mapping block → time.

### 5.4 "Sufficient Data" Principle for Time-based

This is the most important principle when processing time-based tables:

> **To process data for a specific time range, all upstream tables must have data covering that range (extending beyond both ends).**

Specific example: A table with `frequentType = day` wants to process data for **July 26, 2024**:

| Upstream | Data Range | Sufficient for July 26, 2024? |
|---|---|---|
| `ethereum.blocks` (block-based) | block → time: 2024-07-25 18:00 → 2024-07-26 18:00 | **Yes** — covers entire day 26 |
| `ethereum.transactions` (block-based) | block → time: 2024-07-25 20:00 → 2024-07-26 06:00 | **No** — only until 06:00 on day 26, missing data from 06:00–24:00 |

In this case, the job **cannot** process July 26, 2024 because upstream `transactions` doesn't have sufficient data. The job will wait until both upstreams have data extending beyond day 26.

**Summary:** This principle ensures data in time-based tables is always **complete** — never having data gaps due to upstream not finishing processing.

---

## 6. Error Handling and Data Integrity Mechanisms

### 6.1 Job Fails During Data Writing

If a job errors during data writing (e.g., crash, OOM, network error), the system handles as follows:

```
Current run:
    - Data may have been partially written to table (possibly corrupt)
    - Properties NOT updated (because write wasn't successful)

Next run:
    1. System reads properties → detects unconfirmed data
    2. Checks for "hanging" data from previous run
    3. If found → DELETES hanging data before writing new data
    4. Proceeds to process and write data from scratch
```

### 6.2 Why Old Data Must Be Deleted Before Writing New

Important principle: **data in the table must always be accurate**. If a previous run crashed midway, data in the table may be in an inconsistent state (e.g., one partition written, another not). Deleting old data ensures that after the job completes successfully, the table contains only confirmed correct data.

### 6.3 Retry Mechanism

The system supports retry configuration for each job:

```properties
max_retry=10           # Maximum retry count when a partition encounters an error
wait_miliseconds=100   # Wait time between each retry
```

---

## 7. Job Execution Flow Summary

Below is the general flow when a job runs:

```
┌─────────────────────────────────────────────────────────┐
│                    JOB STARTS                            │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  1. Read application.properties                         │
│     → Get chain_name, run_mode, origin_table, ...       │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  2. Read properties of OUTPUT table                     │
│     → Get fromBlock/toBlock or from/toEpochSecond       │
│     → Get upstream list (if table exists)               │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  3. Read properties of all UPSTREAM tables              │
│     → Determine available data range per input          │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  4. Calculate data range to process                     │
│     → Intersection of upstream ranges                   │
│     → Expanded relative to current output range         │
│     → If frequentType=time and upstream=block:          │
│       use origin_table to map block → time              │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  5. Check for hanging data from previous run            │
│     → If found → Delete hanging data                    │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  6. Process data by partition                           │
│     → Split into partitions by number_block_per_        │
│       partition or time range                           │
│     → Process max_number_partition per iteration        │
│     → Loop up to max_time_run iterations                │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  7. WRITE DATA TO TABLE                                 │
│     → If success: UPDATE properties                     │
│     → If failure: NO update, next run will              │
│       return to step 5 and reprocess                    │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                    JOB ENDS                              │
└─────────────────────────────────────────────────────────┘
```

---

## 8. Real-world Examples

### Ethereum Pipeline — Dependency Graph

```
ORIGIN (frequentType=block, no upstream)
├── ethereum_origin.transaction_blocks
└── ethereum_origin.blocks_receipt

EXTRACT (frequentType=block)
├── ethereum.blocks
│   └── upstream: origin.transaction_blocks, origin.blocks_receipt
├── ethereum.transactions
│   └── upstream: origin.blocks_receipt
└── ethereum.logs
    └── upstream: origin.blocks_receipt

DECODED (frequentType=block)
└── ethereum_decoded.erc20_evt_transfer
    └── upstream: ethereum.logs

CONTRACT (frequentType=block)
└── ethereum_contract.erc20_tokens
    └── upstream: ethereum_decoded.erc20_evt_transfer

TOKEN (frequentType=block)
└── ethereum_token.erc20_transfer
    └── upstream: ethereum.transactions, ethereum_decoded.erc20_evt_transfer,
                  ethereum_contract.erc20_tokens
```

### Range Calculation Example for `ethereum.blocks`

**Current state:**
```
ethereum_origin.transaction_blocks: fromBlock=0, toBlock=19500000
ethereum_origin.blocks_receipt:     fromBlock=0, toBlock=19500000
ethereum.blocks (output):           fromBlock=0, toBlock=19400000
```

**When running `ethereum.blocks` job:**
1. Available upstream: block 0 → 19500000 (both have data)
2. Current output: block 0 → 19400000
3. Range to process: block **19400001 → 19500000**
4. Split into partitions: 300 blocks per partition → ~333 partitions
5. Process with `max_number_partition=1`, loop `max_time_run=1` → process 1 partition per run

### Range Calculation Example for Time-based Table

Assume table `ethereum.daily_active_contracts` with `frequentType=day`:

**Current state:**
```
ethereum.blocks (upstream, block-based):
    fromBlock=0, toBlock=19500000
    → block_time range: 2015-07-30 → 2024-07-26 18:00

ethereum.decoded.erc20_evt_transfer (upstream, block-based):
    fromBlock=0, toBlock=19450000
    → block_time range: 2015-07-30 → 2024-07-25 12:00

ethereum.daily_active_contracts (output, day-based):
    fromEpochSecond → toEpochSecond: 2015-07-30 → 2024-07-24
```

**When running job:**
1. Upstream `blocks` has data to 2024-07-26 18:00
2. Upstream `decoded.erc20_evt_transfer` has data to 2024-07-25 12:00
3. Output processed to 2024-07-24
4. Upstream intersection: both have data to **2024-07-25 12:00**
5. Job can process **July 25, 2024** (sufficient full-day data from both upstreams)
6. **Cannot** process 2024-07-26 because `erc20_evt_transfer` only has data to 12:00 on day 25 → insufficient for full day 26

---

## 9. `pre_decode_tables` and `register_evm_call` Mechanics

Two configurations `pre_decode_tables` (used in event decode jobs) and `register_evm_call` (used in contract metadata jobs) are special mechanisms that allow SQL jobs to communicate directly with the blockchain via the EVM engine. Both are declared in the `.sql` file header and processed by the engine before/alongside the SQL body execution.

### 9.1 `pre_decode_tables` — Event Decode Mechanism

**Role**: Declares one or more temp table names (comma-separated without spaces) that the decode engine writes decoded event results to before the SQL body runs. The SQL body then simply reads from these temp tables.

**Declaration in `evm_contract/decode_log.sql` template**:

```
frequent_type=block
list_input_tables=${chain_name}.logs
logs_table_name=${chain_name}.logs
pre_decode_tables=${table_name}
output_table=${chain_name}_decoded.${table_name}
re_partition_by_range=block_date,block_time
partition_by=block_date
write_mode=Append
number_index_columns=3
```

One decode table corresponds to one output_table. To decode multiple events (multiple ABIs) in the same job, list multiple names comma-separated **without spaces**:

```
pre_decode_tables=uniswap_v2_evt_swap,sushiswap_evt_swap,curve_evt_tokenexchange
```

**How it works**:

```
Job runs
    │
    ▼
1. Read raw logs from list_input_tables / logs_table_name (e.g., ethereum.logs)
    │
    ▼
2. For each name in pre_decode_tables, decode engine finds matching ABI
   → strips _evt_* suffix → finds ABI file (e.g., uniswap_v3_evt_swap → uniswap_v3.json)
    │
    ▼
3. Engine decodes event logs per ABI within current block range
    │
    ▼
4. Decode results for each ABI are written to temp table with corresponding name in pre_decode_tables
    │
    ▼
5. SQL body runs: select * from ${pre_decode_tables}
   (or custom: join/union multiple temp tables, add metadata before output)
    │
    ▼
6. Results written to output_table (<chain>_decoded.<table_name>)
```

**Important points**:
- Each name in `pre_decode_tables` is the base `table_name` of an event (e.g., `uniswap_v3_evt_swap`), does NOT need `_dev` suffix and doesn't include schema — this is the temp table name created by the decode engine, not a production table
- Each temp table corresponds to **one ABI** (strips `_evt_*` suffix) and is decoded independently
- Output table is the actual `<chain>_decoded.<table_name>` table, created by the engine from temp tables via SQL body
- Column names in output retain ABI parameter names (camelCase), NOT converted to snake_case
- SQL body can be customized (join pool metadata, transform, etc.) to enrich decoded data before writing to output table
- `number_index_columns=3` corresponds to `block_date, block_number, block_time` — first 3 index columns

### 9.2 `register_evm_call` — Contract View Function Calling Mechanism

**Role**: Registers one or more ABI files (comma-separated without spaces) so SQL body can call smart contract **view functions** (name, symbol, decimals, ...) directly via RPC, for fetching contract metadata without storing in event tables.

**Declaration in SQL file** (e.g., `evm_contract/erc20_tokens.sql`):

```
frequent_type=block
list_input_tables=${chain_name}_decoded.erc20_evt_transfer
register_evm_call=erc20
max_num_files=200
output_table=${chain_name}_contract.erc20_tokens
write_mode=Append
number_index_columns=1
```

To call view functions from additional ABIs in the same job, list multiple names comma-separated **without spaces**:

```
register_evm_call=erc20,dex_pool
```

**How it works**:

```
Job runs
    │
    ▼
1. Engine reads register_evm_call config (e.g., erc20,dex_pool)
   → maps each name to ABI file chainslake/evm/abi/<name>.json
    │
    ▼
2. Engine registers SQL function named <abi_name> for each ABI
   (e.g.: erc20(...), dex_pool(...))
    │
    ▼
3. SQL body calls erc20(CONCAT(contract_address, ' name')) for each new contract
    │
    ▼
4. Engine parses argument: splits contract_address, function name and parameters
   (separated by spaces) → finds function in registered ABI
    │
    ▼
5. Engine calls eth_call via RPC to contract at address, passing parameters to view function
    │
    ▼
6. Result returned as string → cast if needed (e.g., decimals → INT)
    │
    ▼
7. Result written to output_table (<chain>_contract.<table_name>)
```

**Important points**:
- Each value in `register_evm_call` = ABI file name (without `.json`): `erc20` → file `erc20.json`, `dex_pool` → file `dex_pool.json`; each ABI registers a SQL function named after itself (`erc20(...)`, `dex_pool(...)`)
- **Call syntax**: `<abi_name>(CONCAT(contract_address, ' <function_name>'))` — exactly **1 space** between address and function name
- **Functions with multiple parameters**: append parameters after function name, separated by **spaces** (not commas):
  - No parameters: `erc20(CONCAT(contract_address, ' name'))`
  - 1 parameter: `dex_pool(CONCAT(pool_address, ' coins 0'))` → `coins(uint256 index)`
  - Multiple parameters: `<abi_name>(CONCAT(address, ' function_name param1 param2 ...'))`
- Function name must exactly match `"name"` in ABI
- Function returns string; cast if other type needed (e.g., `decimals` is `uint256` but returns string → `cast(... as INT)`)
- Job needs `rpc_list` config (`$<CHAIN>_RPCS` env var) for engine to call RPC — `.sh` must `export $(cat $CHAINSLAKE_RUN_DIR/.env)`
- `number_index_columns=1`: `contract_address` is index column, combined with `${if table_existed}` logic in SQL for **deduplication** — only calls function for new contracts not yet in output table

### 9.3 Comparison Summary

| Feature | `pre_decode_tables` | `register_evm_call` |
|---|---|---|
| Purpose | Decode events from existing logs | Call view functions to fetch contract metadata |
| Input | Raw logs table (`<chain>.logs`) | Decoded event table (with `contract_address`) |
| Output | `<chain>_decoded.<table_name>` | `<chain>_contract.<table_name>` |
| Needs RPC | No (only decodes from existing log data) | Yes (`rpc_list`) |
| Engine action | Decode engine writes temp table before SQL | EVM call engine registers functions for SQL |
| Deduplication | Not needed (log data is unique) | Yes (`${if table_existed}` + index column) |

---

## Quick Reference

| Component | Role |
|---|---|
| `application.properties` | Common config: chain_name, run_mode, number_block_per_partition, origin_table, ... |
| `.sql` header (`list_input_tables`) | Declares upstream of output table |
| `.sql` header (`frequent_type`) | Determines table type: block or time-based |
| `.sql` header (`output_table`) | Single output table of job |
| `.sql` body (`${from}`, `${to}`) | Dynamic variables calculated by system, no manual setting needed |
| `.sql` header (`pre_decode_tables`) | List of temp table names (comma-separated without spaces) that decode engine writes decoded event results to before SQL body runs (see [Section 9.1](#91-pre_decode_tables--event-decode-mechanism)) |
| `.sql` header (`register_evm_call`) | Registers one or more ABI files (comma-separated without spaces) for SQL to call contract view functions via RPC (see [Section 9.2](#92-register_evm_call--contract-view-function-calling-mechanism)) |
| Properties `fromBlock/toBlock` | Tracks block range (block-based) |
| Properties `fromEpochSecond/toEpochSecond` | Tracks time range (time-based) |
| `origin_table` in application.properties | Reference table for mapping block → time (for time-based jobs) |