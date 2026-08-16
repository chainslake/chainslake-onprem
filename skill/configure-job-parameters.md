# Skill: Configure Job/Pipeline Parameters

## Description
Guide for configuring the key parameters of jobs/pipelines in Chainslake: `number_block_per_partition`, `max_number_partition`, `max_time_run`, `start_date` on the DAG, `run_mode`, and backfilling a new job.

## Applicability Conditions
- When setting up a new pipeline for a chain
- When needing to re-tune the parameters of an existing pipeline
- When adding a new job to a DAG that has already been running for a while
- When needing to configure `start_date` or switch `run_mode`

## Key configuration parameters

These parameters can be configured in **2 places**:
1. **`application.properties`** — global configuration for the whole pipeline
2. **In the job's `.sh` file** — via `--conf "spark.app_properties.<parameter>=<value>"`

**Priority order**: If both places have a value, the job uses the value from the `.sh` file.

---

## Steps

### Step 1: Configure `number_block_per_partition`

Goal: each partition processes ~1 hour of data (+ 5% buffer).

#### Method 1: Estimate from the Internet (when setting up new)

Look up the average block speed of the chain and calculate:

| Chain | Block time | number_block_per_partition |
|---|---|---|
| Ethereum | ~12s/block | 300 |
| BNB | ~3s/block | 1000 |
| Polygon | ~2s/block | 1500 |

Formula: `number_block_per_partition = (3600 / block_time_seconds) * 1.05`

#### Method 2: Calculate precisely from real data (after running 1-2 times)

Use a query to count the actual number of blocks in 1 hour:

```sql
-- Count the number of blocks in each hour (use the transaction_blocks table)
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
-- Get the min/max block in a specific hour
SELECT
    min(block_number) as min_block,
    max(block_number) as max_block,
    (max(block_number) - min(block_number)) as blocks_in_hour
FROM <chain>_origin.transaction_blocks
WHERE block_time >= unix_timestamp('<date> 00:00:00')
  AND block_time < unix_timestamp('<date> 01:00:00')
```

Once you have the average blocks/hour, multiply by a 5% buffer:
```
number_block_per_partition = blocks_per_hour * 1.05
```

**Important note**: Make sure the chosen hour has enough data to calculate with (do not use an hour with missing data).

#### Best practice when setting up a new chain

1. Get the estimated value from the Internet (Step 1 - Method 1)
2. Set `max_number_partition=1`, `max_time_run=2` in `application.properties`
3. Run the origin job 1-2 times to have data
4. Query to calculate `number_block_per_partition` precisely (Step 1 - Method 2)
5. Update `application.properties` with the accurate value

#### Applying the configuration

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

This parameter determines how many partitions are processed **concurrently** in 1 loop iteration.

#### Determine current resources

Check the current Spark configuration in `chainslake-run.sh`:

```bash
cat chainslake-run.sh
```

Pay attention to these 2 parameters:
- `--master local[N]` — N = number of threads (parallel reads)
- `--driver-memory Xg` — memory allocated to the driver

Current example:
```bash
spark-submit --master local[2] \
    --driver-memory 4g \
    ...
```
→ 2 threads, 4GB memory

#### Calculate the memory required for 1 partition

Step 1: Determine the size of 1 partition of data:

```sql
-- View table size (total)
DESCRIBE DETAIL <chain>_origin.transaction_blocks;
-- Find the sizeInBytes field
```

```sql
-- If the table is partitioned by block_number, estimate the size of 1 partition
SELECT
    count(*) as total_rows,
    pg_total_relation_size('<chain>_origin.transaction_blocks') / count(*) as avg_row_bytes
FROM <chain>_origin.transaction_blocks
LIMIT 1;
```

Step 2: Estimate the size of 1 partition:
```
memory_per_partition ≈ (number_of_partitions × avg_row_bytes × rows_per_partition) / 1024^3
```

Step 3: Calculate `max_number_partition`:
```
max_number_partition = floor(available_memory_gb / memory_per_partition_gb)
```

**Note**: Memory must be > the data read size + the data write size. Always keep a ~30% buffer.

#### Quick rules

| Resources | Recommended max_number_partition |
|---|---|
| `local[2]` + `4g` | 1-4 (depending on partition size) |
| `local[4]` + `8g` | 2-8 |
| `local[8]` + `16g` | 4-16 |

**Important rule**: For jobs using `frequent_type=day` in the SQL header, `max_number_partition` **MUST be >= 24** (because each day has 24 hours, each hour is 1 partition).

#### Applying the configuration

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

This parameter specifies the number of loop iterations in 1 job run.

**Goal**: 1 run should process **~1 day of data**.

Formula:
```
max_time_run = ceil(24 / max_number_partition)
```

Example:
- `max_number_partition=1` → `max_time_run=24` (24 iterations × 1 partition = 24 partitions = 24 hours = 1 day)
- `max_number_partition=24` → `max_time_run=1` (1 iteration × 24 partitions = 24 hours = 1 day)
- `max_number_partition=12` → `max_time_run=2` (2 iterations × 12 partitions = 24 hours = 1 day)

**Note**: If `number_block_per_partition` corresponds to ~1 hour, then `max_time_run` should be enough to process 24 hours (1 day).

#### Applying the configuration

**In `application.properties`:**
```properties
max_time_run=1
```

---

### Step 4: Configure `start_date` and `catchup` on the DAG

```python
from datetime import datetime, timedelta

# In the DAG file
with DAG(
    "Ethereum",
    start_date=datetime.now() - timedelta(days=730),  # ← Default: 2 years before the current date
    catchup=False,                                      # ← Does not automatically rerun from start_date
    ...
)
```

**How to determine `start_date`**: By default, set `start_date` to **2 years before the current date** (`datetime.now() - timedelta(days=730)`). If the user needs earlier data, ask and set it according to the request.

**`catchup=False`**: Important — the DAG does **not automatically rerun** from `start_date` to the present when newly created. Backfilling historical data is done manually in **Step 6**.

**Note**: `start_date` must be a **date in the past**. If `start_date` is set to today, Airflow will only run from today onward.

---

### Step 5: Configure `run_mode` (backward/forward)

#### Principles

- **`backward`**: Runs from the present back to the past (prioritizes new data). It also allows running forward.
- **`forward`**: Only allows running forward (from the past to the present).

Default: the whole pipeline runs `backward`.

#### When to switch to `forward`

When the pipeline has backfilled data back to `start_date` and you want to switch to normal forward running mode.

#### How to switch — ONLY need to change the first job

**No need** to change `run_mode` for all jobs. Only change it at the `_origin.transaction_blocks` job (the first job in the pipeline).

**Reason**: When the `_origin.transaction_blocks` job stops running backward (i.e., it already has data up to the required date), the downstream jobs, even if they still set `backward`, can **no longer run further into the past** because there is no newer data to process.

#### How to change

**In `application.properties`** (global change):
```properties
run_mode=forward
```

**Or override in the `.sh` file** (only applies to 1 specific job):
```bash
$CHAINSLAKE_RUN_DIR/chainslake-run.sh ... \
    --conf "spark.app_properties.run_mode=forward" \
    ...
```

**Recommendation**: Use `--conf` in the `_origin.transaction_blocks` `.sh` file to change only the first job, keeping the other jobs at `backward`.

---

### Step 6: Backfill a job newly added to the DAG

When the DAG has already finished backfilling data to the past, a newly added job **must automatically run backfill** to have historical data.

#### Using the Airflow CLI

```bash
# Backfill 1 specific task
docker exec -u hadoop chainslake-onprem-node01-1 bash -c \
    "export PS1='something' && source /etc/bash.bashrc && \
     airflow tasks run <DAG_ID> <TASK_ID> <EXECUTION_DATE> --run-backwards"

# Example: Backfill task bnb_origin.transaction_blocks from 2025-10-11
docker exec -u hadoop chainslake-onprem-node01-1 bash -c \
    "export PS1='something' && source /etc/bash.bashrc && \
     airflow tasks run BNB bnb_origin.transaction_blocks 2025-10-11 --run-backwards"
```

#### Backfill the whole DAG (if needed)

```bash
docker exec -u hadoop chainslake-onprem-node01-1 bash -c \
    "export PS1='something' && source /etc/bash.bashrc && \
     airflow dags backfill -s 2025-10-11 -e <end_date> <DAG_ID>"
```

**Note**:
- `--run-backwards`: Runs from end_date to start_date (backward)
- The new job runs sequentially according to dependencies, so its upstream jobs also need to have data
- If the new job is in the middle of the pipeline (e.g., a new extract job), make sure the upstream origin jobs already have data

---

## Real-World Example

### Setting up BNB Chain from scratch

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
start_date=datetime.now() - timedelta(days=730),  # Default 2 years back
catchup=False                                      # Does not automatically rerun
```

After running 1-2 times, query to calculate `number_block_per_partition` precisely:

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

### Adding a new job to a DAG that already has data

Assume adding `bnb.extract.new_table.sh`:

1. Create the new `.sh` file
2. Add the task to the `bnb.py` DAG
3. Backfill only the new task:
```bash
docker exec -u hadoop chainslake-onprem-node01-1 bash -c \
    "export PS1='something' && source /etc/bash.bashrc && \
     airflow tasks run BNB bnb.new_table 2025-10-11 --run-backwards"
```

## Notes / Gotchas

- **`number_block_per_partition` must always be > 0**: If = 0, the job will error or run endlessly
- **`max_number_partition` for `frequent_type=day`**: Must be >= 24
- **Prefer `--conf` in `.sh`**: When you want to quickly change 1 job without editing the shared `application.properties`
- **`run_mode=backward` is more flexible**: It allows running both forward and backward, so keep it on all jobs except the first origin job when you want to stop running backward
- **Backfill needs the correct execution_date**: It must be a date for which the DAG does not yet have data, otherwise Airflow will skip it
- **Memory must be > data read + data write**: Always keep a buffer, especially for large partitions
