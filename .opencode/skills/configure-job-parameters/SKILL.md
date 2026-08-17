---
name: configure-job-parameters
description: Configure key job/pipeline parameters: number_block_per_partition, max_number_partition, max_time_run, start_date, run_mode, backfill
---

# Skill: Configure Job/Pipeline Parameters

## Description
Guide to configuring key parameters for jobs/pipelines in Chainslake: `number_block_per_partition`, `max_number_partition`, `max_time_run`, `start_date` on DAG, `run_mode`, and backfilling new jobs.

## When to Use
- When setting up a new pipeline for a chain
- When optimizing parameters for an existing pipeline
- When adding a new job to a DAG that has been running for a while
- When configuring `start_date` or switching `run_mode`

## Key Configuration Parameters

These parameters can be configured in **2 places**:
1. **`application.properties`** — common configuration for the entire pipeline
2. **In the `.sh` file** of the job — via `--conf "spark.app_properties.<parameter>=<value>"`

**Priority order**: If both places have a value, the job will use the value from the `.sh` file.

---

## Implementation Steps

### Step 1: Configure `number_block_per_partition`

Goal: each partition processes ~1 hour of data (+ 5% buffer).

#### Method 1: Estimate from Internet (for new setups)

Look up the chain's average block time and calculate:

| Chain | Block time | number_block_per_partition |
|---|---|---|
| Ethereum | ~12s/block | 300 |
| BNB | ~3s/block | 1000 |
| Polygon | ~2s/block | 1500 |

Formula: `number_block_per_partition = (3600 / block_time_seconds) * 1.05`

#### Method 2: Calculate accurately from real data (after 1-2 runs)

Use a query to count the actual number of blocks in 1 hour:

```sql
-- Count blocks per hour (using transaction_blocks table)
SELECT
    hour(from_unixtime(block_time)) as block_hour,
    count(*) as blocks_per_hour
FROM <chain>_origin.transaction_blocks
WHERE block_time >= unix_timestamp('<start_date>')
  AND block_time < unix_timestamp('<end_date>')
GROUP BY hour(from_unixtime(block_time))
ORDER BY block_hour
```

Or a simpler approach:

```sql
-- Get min/max blocks in a specific hour
SELECT
    min(block_number) as min_block,
    max(block_number) as max_block,
    (max(block_number) - min(block_number)) as blocks_in_hour
FROM <chain>_origin.transaction_blocks
WHERE block_time >= unix_timestamp('<date> 00:00:00')
  AND block_time < unix_timestamp('<date> 01:00:00')
```

Once you have the average blocks/hour, add 5% buffer:
```
number_block_per_partition = blocks_per_hour * 1.05
```

**Important note**: Ensure the selected hour has complete data (don't pick an hour with missing data).

#### Best Practice for New Chain Setup

1. Get estimated value from Internet (Step 1 - Method 1)
2. Set `max_number_partition=1`, `max_time_run=2` in `application.properties`
3. Run origin job 1-2 times to get data
4. Query to calculate exact `number_block_per_partition` (Step 1 - Method 2)
5. Update `application.properties` with the exact value

#### Applying the Configuration

**In `application.properties`:**
```properties
number_block_per_partition=300
```

**Or in the `.sh` file (overrides `application.properties`):**
```bash
$CHAINSLAKE_RUN_DIR/chainslake-run.sh --class chainslake.evm.Main \
    --name EthereumOriginTransactionBlocks \
    --conf "spark.app_properties.number_block_per_partition=300" \
    ...
```

---

### Step 2: Configure `max_number_partition`

This parameter determines how many partitions are processed **simultaneously** in one iteration.

#### Identify Current Resources

Check the current Spark configuration in `chainslake-run.sh`:

```bash
cat chainslake-run.sh
```

Note 2 parameters:
- `--master local[N]` — N = number of threads (parallel reads)
- `--driver-memory Xg` — memory allocated to driver

Current example:
```bash
spark-submit --master local[2] \
    --driver-memory 4g \
    ...
```
→ 2 threads, 4GB memory

#### Calculate Memory Needed for 1 Partition

Step 1: Determine partition data size:

```sql
-- Check table size (total)
DESCRIBE DETAIL <chain>_origin.transaction_blocks;
-- Find the sizeInBytes field
```

```sql
-- If table is partitioned by block_number, estimate 1 partition size
SELECT
    count(*) as total_rows,
    pg_total_relation_size('<chain>_origin.transaction_blocks') / count(*) as avg_row_bytes
FROM <chain>_origin.transaction_blocks
LIMIT 1;
```

Step 2: Estimate 1 partition size:
```
memory_per_partition ≈ (number_of_partitions × avg_row_bytes × rows_per_partition) / 1024^3
```

Step 3: Calculate `max_number_partition`:
```
max_number_partition = floor(available_memory_gb / memory_per_partition_gb)
```

**Note**: Memory needs to be > data read size + data write size. Always keep ~30% buffer.

#### Quick Rules

| Resources | Recommended max_number_partition |
|---|---|
| `local[2]` + `4g` | 1-4 (depends on partition size) |
| `local[4]` + `8g` | 2-8 |
| `local[8]` + `16g` | 4-16 |

**Important rule**: For jobs using `frequent_type=day` in the SQL header, `max_number_partition` **MUST be >= 24** (because each day has 24 hours, each hour is 1 partition).

#### Applying the Configuration

**In `application.properties`:**
```properties
max_number_partition=1
```

**Or in the `.sh` file:**
```bash
$CHAINSLAKE_RUN_DIR/chainslake-run.sh ... \
    --conf "spark.app_properties.max_number_partition=24" \
    ...
```

---

### Step 3: Configure `max_time_run`

This parameter indicates the number of iterations in one job run.

**Goal**: One run should process **~1 day of data**.

Formula:
```
max_time_run = ceil(24 / max_number_partition)
```

Examples:
- `max_number_partition=1` → `max_time_run=24` (24 iterations × 1 partition = 24 partitions = 24 hours = 1 day)
- `max_number_partition=24` → `max_time_run=1` (1 iteration × 24 partitions = 24 hours = 1 day)
- `max_number_partition=12` → `max_time_run=2` (2 iterations × 12 partitions = 24 hours = 1 day)

**Note**: If `number_block_per_partition` equals ~1 hour, then `max_time_run` should be enough to process 24 hours (1 day).

#### Applying the Configuration

**In `application.properties`:**
```properties
max_time_run=1
```

---

### Step 4: Configure `start_date` and `catchup` on DAG

```python
from datetime import datetime, timedelta

# In DAG file
with DAG(
    "Ethereum",
    start_date=datetime.now() - timedelta(days=730),  # ← Default: 2 years before current date
    catchup=False,                                      # ← Don't auto-run from start_date
    ...
)
```

**How to determine `start_date`**: Default is **2 years before the current date** (`datetime.now() - timedelta(days=730)`). If the user needs earlier data, ask and set accordingly.

**`catchup=False`**: Important — the DAG **does NOT auto-run** from `start_date` to present when first created. Historical data backfill will be done manually in **Step 6**.

**Note**: `start_date` must be a **date in the past**. If you set `start_date` to today, Airflow will only run from today onwards.

---

### Step 5: Configure `run_mode` (backward/forward)

#### Principles

- **`backward`**: Runs from present to past (prioritizes newer data). Also allows running forward.
- **`forward`**: Only allows running forward (from past to present).

Default: entire pipeline runs `backward`.

#### When to Switch to `forward`

When the pipeline has enough data back to `start_date` and you want to switch to normal forward processing.

#### How to Switch — ONLY Need to Change the First Job

**No need** to change `run_mode` for all jobs. Only change it for the `_origin.transaction_blocks` job (the first job in the pipeline).

**Reason**: When `_origin.transaction_blocks` stops running backward (meaning data exists up to the needed date), downstream jobs even if still set to `backward` **cannot continue running to the past** because there's no newer data to process.

#### How to Change

**In `application.properties`** (change globally):
```properties
run_mode=forward
```

**Or override in the `.sh` file** (apply to specific job only):
```bash
$CHAINSLAKE_RUN_DIR/chainslake-run.sh ... \
    --conf "spark.app_properties.run_mode=forward" \
    ...
```

**Recommendation**: Use `--conf` in the `_origin.transaction_blocks` `.sh` file to change only the first job, keeping other jobs at `backward`.

---

### Step 6: Backfill Newly Added Jobs to DAG

When the DAG has finished backfilling historical data, newly added jobs **must backfill themselves** to get historical data.

#### Using Airflow CLI

```bash
# Backfill a specific task
docker exec -u hadoop chainslake-onprem-node01-1 bash -c \
    "export PS1='something' && source /etc/bash.bashrc && \
     airflow tasks run <DAG_ID> <TASK_ID> <EXECUTION_DATE> --run-backwards"

# Example: Backfill task bnb_origin.transaction_blocks from 2025-10-11
docker exec -u hadoop chainslake-onprem-node01-1 bash -c \
    "export PS1='something' && source /etc/bash.bashrc && \
     airflow tasks run BNB bnb_origin.transaction_blocks 2025-10-11 --run-backwards"
```

#### Backfill Entire DAG (if needed)

```bash
docker exec -u hadoop chainslake-onprem-node01-1 bash -c \
    "export PS1='something' && source /etc/bash.bashrc && \
     airflow dags backfill -s 2025-10-11 -e <end_date> <DAG_ID>"
```

**Notes**:
- `--run-backwards`: Run from end_date to start_date (backward)
- New jobs will run sequentially according to dependencies, so their upstream jobs must have data
- If the new job is in the middle of the pipeline (e.g., a new extract job), ensure upstream origin jobs have data

---

## Real-world Examples

### New BNB Chain Setup

```properties
# application.properties
chain_name=bnb
number_block_per_partition=1000      # ~3s/block → 1200 blocks/hour → 1000 (5% buffer)
max_number_partition=1               # local[2] + 4g
max_time_run=24                      # 24 iterations × 1 partition = 24 partitions = 1 day
run_mode=backward
```

```python
from datetime import datetime, timedelta

# DAG bnb.py
start_date=datetime.now() - timedelta(days=730),  # Default 2 years ago
catchup=False                                      # Don't auto-run
```

After running 1-2 times, query to calculate exact `number_block_per_partition`:

```sql
SELECT
    min(block_number) as min_b,
    max(block_number) as max_b,
    (max(block_number) - min(block_number)) as blocks_count
FROM bnb_origin.transaction_blocks
WHERE block_time >= unix_timestamp('2025-10-11 00:00:00')
  AND block_time < unix_timestamp('2025-10-11 01:00:00')
-- Result: blocks_count = 1180 → number_block_per_partition = 1180 * 1.05 ≈ 1239
```

### Switching backward → forward

After backfilling enough data to `start_date`:

```properties
# In application.properties of _origin.transaction_blocks (or use --conf in .sh)
run_mode=forward
```

### Adding New Job to DAG with Existing Data

Suppose adding `bnb.extract.new_table.sh`:

1. Create new `.sh` file
2. Add task to `bnb.py` DAG
3. Backfill the new task only:
```bash
docker exec -u hadoop chainslake-onprem-node01-1 bash -c \
    "export PS1='something' && source /etc/bash.bashrc && \
     airflow tasks run BNB bnb.new_table 2025-10-11 --run-backwards"
```

## Notes / Gotchas

- **`number_block_per_partition` must always be > 0**: If = 0 the job will error or run indefinitely
- **`max_number_partition` for `frequent_type=day`**: Must be >= 24
- **Prefer `--conf` in `.sh`**: When you want to quickly change one job without modifying the shared `application.properties`
- **`run_mode=backward` is more flexible**: Allows running both forward and backward, so keep it unless you want to stop backward processing on the first origin job
- **Backfill needs correct execution_date**: Must be a date the DAG doesn't have data for, otherwise Airflow will skip it
- **Memory needs to be > data read + data write**: Always keep buffer, especially with large partitions