# Test Case — ethereum_token.erc20_transfer

## General Information

| Property | Value |
|---|---|
| Table under test | `ethereum_token.erc20_transfer` |
| Created date | 2026-07-26 |
| Version | 1 |
| frequentType | `block` |
| Job script | `chainslake/jobs/ethereum/token/erc20_transfer.sh` |
| SQL file | `chainslake/sql/evm_token/erc20_transfer.sql` |

## Upstream

| Table | Join Type | Notes |
|---|---|---|
| `ethereum_decoded.erc20_evt_transfer` | Main source | Primary table, each row = 1 ERC-20 Transfer event |
| `ethereum.transactions` | INNER JOIN | Must have corresponding transaction; if missing → record is excluded |
| `ethereum_contract.erc20_tokens` | LEFT JOIN | May be NULL if contract has no metadata in registry |

---

## Group 1: Schema & Structure Tests

### TC-1.1: Table Existence Check

**Purpose**: Confirm the table was created successfully in the data warehouse.

```sql
DESCRIBE ethereum_token.erc20_transfer
```

**Expected**: Returns 15 columns with correct data types.

### TC-1.2: Column Data Type Check

**Purpose**: Ensure schema matches catalog design.

| Column | Expected Type | Actual Type |
|---|---|---|
| `block_date` | `date` | |
| `block_number` | `bigint` | |
| `block_time` | `timestamp` | |
| `updated_time` | `timestamp` | |
| `contract_address` | `string` | |
| `symbol` | `string` | |
| `decimals` | `int` | |
| `tx_hash` | `string` | |
| `evt_index` | `int` | |
| `from` | `string` | |
| `to` | `string` | |
| `value` | `double` | |
| `tx_from` | `string` | |
| `tx_to` | `string` | |
| `tx_method_id` | `string` | |

### TC-1.3: Partition Check

**Purpose**: Confirm table is partitioned by `block_date`.

```sql
SHOW PARTITIONS ethereum_token.erc20_transfer
```

**Expected**: Results in format `block_date=YYYY-MM-DD`.

### TC-1.4: Index Columns Check

**Purpose**: Confirm the first 3 index columns are in correct order: `block_date`, `block_number`, `block_time`.

```sql
DESCRIBE EXTENDED ethereum_token.erc20_transfer
```

**Expected**: First 3 columns match the index order.

---

## Group 2: Basic Data Tests

### TC-2.1: Total Row Count

**Purpose**: Ensure the table contains data.

```sql
SELECT count(*) as total_rows FROM ethereum_token.erc20_transfer
```

**Expected**: `total_rows > 0`.

### TC-2.2: Block Number Range Check

**Purpose**: Ensure data falls within a reasonable block range.

```sql
SELECT
    min(block_number) as min_block,
    max(block_number) as max_block,
    count(*) as total_rows
FROM ethereum_token.erc20_transfer
```

**Expected**:
- `min_block` >= 0
- `max_block` > `min_block`
- `total_rows` > 0

### TC-2.3: Data Distribution by block_date

**Purpose**: Ensure data is evenly distributed by day with no missing dates.

```sql
SELECT
    block_date,
    count(*) as row_count,
    min(block_number) as min_block,
    max(block_number) as max_block
FROM ethereum_token.erc20_transfer
GROUP BY block_date
ORDER BY block_date
```

**Expected**:
- Each day has data with > 0 rows
- `min_block` and `max_block` increase with `block_date`
- No missing dates (gaps)

### TC-2.4: Duplicate Record Check

**Purpose**: Ensure each transfer event appears only once.

```sql
SELECT
    tx_hash, evt_index, count(*) as cnt
FROM ethereum_token.erc20_transfer
GROUP BY tx_hash, evt_index
HAVING cnt > 1
```

**Expected**: Returns 0 rows (no duplicates).

---

## Group 3: SQL Transform Logic Tests

### TC-3.1: INNER JOIN with transactions Check

**Purpose**: Confirm each erc20_transfer record has a corresponding transaction. Transfer events without matching transactions are excluded (correct INNER JOIN behavior).

```sql
SELECT count(*) as orphan_count
FROM ethereum_decoded.erc20_evt_transfer e
LEFT JOIN ethereum_token.erc20_transfer t
ON e.tx_hash = t.tx_hash AND e.evt_index = t.evt_index
WHERE t.tx_hash IS NULL
AND e.block_number >= 25516917 AND e.block_number <= 25517819
```

**Expected**: `orphan_count` = 0 or very small (excluded by inner join).

### TC-3.2: LEFT JOIN with erc20_tokens — tokens WITH metadata

**Purpose**: Confirm tokens in the registry have symbol and decimals.

```sql
SELECT
    contract_address,
    symbol,
    decimals,
    count(*) as cnt
FROM ethereum_token.erc20_transfer
WHERE symbol IS NOT NULL AND decimals IS NOT NULL
GROUP BY contract_address, symbol, decimals
ORDER BY cnt DESC
LIMIT 10
```

**Expected**: Returns list of common tokens (USDC, USDT, WETH, DAI, ...).

### TC-3.3: LEFT JOIN with erc20_tokens — tokens WITHOUT metadata

**Purpose**: Confirm transfer events from contracts not in erc20_tokens are still retained, but symbol and decimals are NULL.

```sql
SELECT count(*) as null_metadata_count
FROM ethereum_token.erc20_transfer
WHERE symbol IS NULL OR decimals IS NULL
```

**Expected**: If > 0, this is normal (contract not registered in registry).

### TC-3.4: Value Conversion Calculation Check

**Purpose**: Confirm `value = raw_value * 10^(-decimals)` is calculated correctly.

```sql
SELECT
    t.contract_address,
    t.symbol,
    t.decimals,
    t.value as converted_value,
    e.value as raw_value,
    CAST(e.value AS DOUBLE) * POW(10, -t.decimals) as expected_value
FROM ethereum_token.erc20_transfer t
JOIN ethereum_decoded.erc20_evt_transfer e
ON t.tx_hash = e.tx_hash AND t.evt_index = e.evt_index
WHERE t.symbol IS NOT NULL
LIMIT 10
```

**Expected**: `converted_value` = `expected_value` (deviation < 0.000001 due to double rounding).

### TC-3.5: decimals = 0 Case (token without decimals)

**Purpose**: Confirm calculation is correct when decimals = 0 (raw value preserved).

```sql
SELECT
    contract_address, symbol, decimals,
    value
FROM ethereum_token.erc20_transfer
WHERE decimals = 0
```

**Expected**: `value` equals raw value from erc20_evt_transfer (since `10^0 = 1`).

### TC-3.6: High decimals Case (18 — most common)

**Purpose**: Confirm conversion calculation works correctly for tokens with 18 decimals (e.g., WETH, DAI).

```sql
SELECT
    contract_address, symbol, decimals,
    value
FROM ethereum_token.erc20_transfer
WHERE decimals = 18 AND symbol IN ('WETH', 'DAI', 'USDC')
LIMIT 10
```

**Expected**: `value` is a reasonable real number (e.g., WETH transfer of 1 ETH → value ≈ 1.0).

---

## Group 4: Data Integrity Tests

### TC-4.1: No NULL block_number

```sql
SELECT count(*) as null_count
FROM ethereum_token.erc20_transfer
WHERE block_number IS NULL
```

**Expected**: `null_count` = 0.

### TC-4.2: No NULL tx_hash

```sql
SELECT count(*) as null_count
FROM ethereum_token.erc20_transfer
WHERE tx_hash IS NULL
```

**Expected**: `null_count` = 0.

### TC-4.3: No NULL from/to

```sql
SELECT count(*) as null_count
FROM ethereum_token.erc20_transfer
WHERE `from` IS NULL OR `to` IS NULL
```

**Expected**: `null_count` = 0.

### TC-4.4: No NULL or NaN value

```sql
SELECT count(*) as null_count
FROM ethereum_token.erc20_transfer
WHERE value IS NULL OR isNaN(value)
```

**Expected**: `null_count` = 0.

### TC-4.5: block_time >= block_date

**Purpose**: Ensure block_time falls within its corresponding block_date.

```sql
SELECT count(*) as invalid_count
FROM ethereum_token.erc20_transfer
WHERE CAST(block_time AS DATE) != block_date
```

**Expected**: `invalid_count` = 0.

### TC-4.6: contract_address Valid Hex Format

```sql
SELECT count(*) as invalid_count
FROM ethereum_token.erc20_transfer
WHERE contract_address IS NOT NULL
AND NOT contract_address RLIKE '^0x[0-9a-fA-F]{40}$'
```

**Expected**: `invalid_count` = 0.

### TC-4.7: tx_from and tx_to Valid Hex Format

```sql
SELECT count(*) as invalid_count
FROM ethereum_token.erc20_transfer
WHERE (tx_from IS NOT NULL AND NOT tx_from RLIKE '^0x[0-9a-fA-F]{40}$')
OR (tx_to IS NOT NULL AND NOT tx_to RLIKE '^0x[0-9a-fA-F]{40}$')
```

**Expected**: `invalid_count` = 0.

---

## Group 5: Business Logic Tests

### TC-5.1: USDC Transfer Check (decimals=6)

**Purpose**: Confirm USDC transfers have reasonable values. USDC has 6 decimals, so 1 USDC = 1.0.

```sql
SELECT
    tx_hash, evt_index,
    contract_address, symbol, decimals,
    `from`, `to`, value
FROM ethereum_token.erc20_transfer
WHERE symbol = 'USDC' AND decimals = 6
AND value BETWEEN 100 AND 1000
LIMIT 5
```

**Expected**: Returns USDC transfers with reasonable values (reflecting correct USD value).

### TC-5.2: USDT Transfer Check (decimals=6)

```sql
SELECT
    tx_hash, evt_index,
    contract_address, symbol, decimals,
    `from`, `to`, value
FROM ethereum_token.erc20_transfer
WHERE symbol = 'USDT' AND decimals = 6
AND value > 0
LIMIT 5
```

**Expected**: USDT transfers with value > 0, symbol = 'USDT'.

### TC-5.3: WETH Transfer Check (decimals=18)

```sql
SELECT
    tx_hash, evt_index,
    contract_address, symbol, decimals,
    `from`, `to`, value
FROM ethereum_token.erc20_transfer
WHERE symbol = 'WETH' AND decimals = 18
AND value BETWEEN 0.01 AND 100
LIMIT 5
```

**Expected**: WETH transfers with value > 0, symbol = 'WETH'.

### TC-5.4: DAI Transfer Check (decimals=18)

```sql
SELECT
    tx_hash, evt_index,
    contract_address, symbol, decimals,
    `from`, `to`, value
FROM ethereum_token.erc20_transfer
WHERE symbol = 'DAI' AND decimals = 18
AND value > 0
LIMIT 5
```

**Expected**: DAI transfers with value > 0, symbol = 'DAI'.

### TC-5.5: from != to (No Self-Transfer Check)

**Purpose**: Most transfers have from != to. Self-transfers (from = to) are valid but rare.

```sql
SELECT count(*) as self_transfer_count
FROM ethereum_token.erc20_transfer
WHERE `from` = `to`
```

**Expected**: `self_transfer_count` = 0 or very small compared to total.

### TC-5.6: tx_method_id Validity Check

**Purpose**: ERC-20 transfers typically have method_id = `0xa9059cbb` (transfer) or `0x23b872dd` (transferFrom).

```sql
SELECT
    tx_method_id,
    count(*) as cnt
FROM ethereum_token.erc20_transfer
GROUP BY tx_method_id
ORDER BY cnt DESC
LIMIT 10
```

**Expected**: Most common method_ids are `0xa9059cbb` and `0x23b872dd`.

### TC-5.7: tx_to = contract_address Check

**Purpose**: In most cases, `tx_to` in the transaction = `contract_address` of the token (user calling function on token contract).

```sql
SELECT count(*) as mismatch_count
FROM ethereum_token.erc20_transfer
WHERE tx_to != contract_address
```

**Expected**: `mismatch_count` = 0 or very small (multisig, proxy, batch transfers may differ).

---

## Group 6: Range & Partition Tests

### TC-6.1: Block Number Within SQL Filter Range

**Purpose**: Confirm each record falls within the block range processed by the job.

```sql
SELECT
    min(block_number) as min_block,
    max(block_number) as max_block,
    count(*) as total
FROM ethereum_token.erc20_transfer
```

**Expected**: Results match catalog (fromBlock=25516917, toBlock=25517819).

### TC-6.2: Record Distribution by Partition

**Purpose**: Ensure data is evenly distributed, no partition too large or too small.

```sql
SELECT
    block_date,
    count(*) as row_count,
    count(DISTINCT block_number) as block_count
FROM ethereum_token.erc20_transfer
GROUP BY block_date
ORDER BY block_date
```

**Expected**:
- Each partition has data
- block_count per day ≈ 900–1100 blocks/day (≈ 12s/block × 86400s/day)

### TC-6.3: Block Number Monotonicity Within Partition

```sql
SELECT count(*) as disorder_count
FROM (
    SELECT block_number,
           LAG(block_number) OVER (PARTITION BY block_date ORDER BY block_number) as prev_block
    FROM ethereum_token.erc20_transfer
) t
WHERE prev_block IS NOT NULL AND block_number <= prev_block
```

**Expected**: `disorder_count` = 0.

---

## Group 7: Edge Case Tests

### TC-7.1: Token with Very High decimals (> 30)

**Purpose**: Some non-standard tokens have extremely high decimals. The `pow(10, -decimals)` calculation may produce very small numbers or zero.

```sql
SELECT
    contract_address, symbol, decimals,
    count(*) as cnt
FROM ethereum_token.erc20_transfer
WHERE decimals > 30
GROUP BY contract_address, symbol, decimals
```

**Expected**: If any exist → confirm value has been rounded to 0 or very small (mathematically correct).

### TC-7.2: value = 0 Check

**Purpose**: There may be transfer events with value = 0 (token burn or test transaction).

```sql
SELECT count(*) as zero_value_count
FROM ethereum_token.erc20_transfer
WHERE value = 0
```

**Expected**: `zero_value_count` = 0 or very small.

### TC-7.3: value < 0 Check (Anomalous)

```sql
SELECT count(*) as negative_count
FROM ethereum_token.erc20_transfer
WHERE value < 0
```

**Expected**: `negative_count` = 0 (ERC-20 transfer values are always >= 0).

### TC-7.4: Multiple Transfers per block_number

**Purpose**: A single block can contain multiple transfer events.

```sql
SELECT
    block_number,
    count(*) as transfer_count
FROM ethereum_token.erc20_transfer
GROUP BY block_number
ORDER BY transfer_count DESC
LIMIT 10
```

**Expected**: Returns blocks with many transfers (normal behavior).

### TC-7.5: Multiple Transfers per tx_hash

**Purpose**: A single transaction can contain multiple transfer events (batch transfer, multicall).

```sql
SELECT
    tx_hash,
    count(*) as transfer_count
FROM ethereum_token.erc20_transfer
GROUP BY tx_hash
HAVING transfer_count > 1
ORDER BY transfer_count DESC
LIMIT 10
```

**Expected**: Returns transactions with multiple transfers (valid, especially on DEX).

---

## Group 8: Upstream Consistency Tests

### TC-8.1: Row Count Consistency Between erc20_transfer and erc20_evt_transfer

**Purpose**: Confirm transfer event count in erc20_transfer = count in erc20_evt_transfer (within same block range).

```sql
SELECT
    (SELECT count(*) FROM ethereum_decoded.erc20_evt_transfer
     WHERE block_number >= 25516917 AND block_number <= 25517819) as upstream_count,
    (SELECT count(*) FROM ethereum_token.erc20_transfer) as token_count
```

**Expected**: `upstream_count` = `token_count` (or very close, since inner join may exclude a few records without matching transactions).

### TC-8.2: Symbol and Decimals Consistency with erc20_tokens

```sql
SELECT
    t.contract_address,
    t.symbol as token_symbol,
    t.decimals as token_decimals,
    c.symbol as contract_symbol,
    c.decimals as contract_decimals
FROM ethereum_token.erc20_transfer t
LEFT JOIN ethereum_contract.erc20_tokens c
ON t.contract_address = c.contract_address
WHERE t.symbol != c.symbol OR t.decimals != c.decimals
```

**Expected**: Returns 0 rows (all symbol/decimals match).

### TC-8.3: tx_from, tx_to Consistency with transactions

```sql
SELECT
    t.tx_hash,
    t.tx_from as token_tx_from,
    t.tx_to as token_tx_to,
    tx.`from` as tx_table_from,
    tx.`to` as tx_table_to
FROM ethereum_token.erc20_transfer t
JOIN ethereum.transactions tx
ON t.tx_hash = tx.hash
WHERE t.tx_from != tx.`from` OR t.tx_to != tx.`to`
```

**Expected**: Returns 0 rows.

---

## Summary

| Group | Test Cases | Notes |
|---|---|---|
| 1. Schema & Structure | 4 | Table, data types, partition, index |
| 2. Basic Data | 4 | Existence, block range, distribution, duplicates |
| 3. SQL Transform Logic | 6 | JOINs, value calculation, decimals edge cases |
| 4. Data Integrity | 7 | NULL checks, hex format, block_time vs block_date |
| 5. Business Logic | 7 | Specific tokens (USDC/USDT/WETH/DAI), method_id |
| 6. Range & Partition | 3 | Block range, partition distribution, block order |
| 7. Edge Cases | 5 | High decimals, value = 0, value < 0, batch transfers |
| 8. Upstream Consistency | 3 | Data consistency with upstream tables |
| **Total** | **39** | |

## How to Run Tests

1. Connect to Spark SQL (access via container or JDBC)
2. Run each test case in group order
3. Fill in the "Actual Result" column (add column when using)
4. If test case fails → Analyze root cause, add notes in the "Notes" column (add column when using)