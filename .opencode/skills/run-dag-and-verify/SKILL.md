---
name: run-dag-and-verify
description: Trigger an Airflow DAG, monitor progress until completion, and verify data in tables after the run
---

# Skill: Run DAG and Verify Data

## Description
Trigger an Airflow DAG (default Ethereum), monitor progress until completion, and verify data in tables after the run.

## When to Use
- Docker containers are running (`docker compose up -d`)
- Airflow is active (port 58080)
- DAG exists and is configured correctly
- RPC endpoints are configured in `chainslake-run/.env`

## Implementation Steps

### Step 1: Check `.env` for RPCs

```bash
cat chainslake-run/.env
```

If not present or empty, run `python script/check_rpcs.py <chain_id>` first.

### Step 2: Trigger and Monitor DAG

```bash
python script/trigger_dag.py Ethereum
```

The script runs Airflow CLI inside the container via `docker exec`:
1. Pauses DAG to avoid conflicts with running jobs
2. Unpauses DAG
3. Triggers manual run
4. Polls status every 30s until success/failed

**Optional parameters:**
```bash
# Trigger and exit immediately (don't wait)
python script/trigger_dag.py Ethereum --no-wait

# Check status only
python script/trigger_dag.py Ethereum --status

# Pause DAG and view active runs
python script/trigger_dag.py Ethereum --cancel-all

# Custom poll interval
python script/trigger_dag.py Ethereum --poll-interval 60
```

### Step 3: Verify Data

After DAG succeeds, verify data:

```bash
# Check row count per table
python query/query_table.py "SELECT count(*) as total FROM ethereum.blocks LIMIT 1"
python query/query_table.py "SELECT count(*) as total FROM ethereum.transactions LIMIT 1"
python query/query_table.py "SELECT count(*) as total FROM ethereum.logs LIMIT 1"
python query/query_table.py "SELECT count(*) as total FROM ethereum_decoded.erc20_evt_transfer LIMIT 1"
python query/query_table.py "SELECT count(*) as total FROM ethereum_contract.erc20_tokens LIMIT 1"
python query/query_table.py "SELECT count(*) as total FROM ethereum_token.erc20_transfer LIMIT 1"

# View schema and sample data
python query/get_example_table.py ethereum.blocks
python query/get_example_table.py ethereum.transactions
```

## Ethereum DAG Dependency Graph

```
origin.transaction_blocks → origin.blocks_receipt
origin.blocks_receipt → [blocks, transactions, logs]
logs → decoded.erc20_evt_transfer
decoded.erc20_evt_transfer → contract.erc20_tokens
[transactions, decoded.erc20_evt_transfer, contract.erc20_tokens] → token.erc20_transfer
```

8 tasks, running sequentially with LocalExecutor.

## Notes / Gotchas

### Airflow CLI
The script uses `docker exec` to call `airflow` CLI inside the `chainslake-onprem-node01-1` container.
- Container must be running (`docker ps | grep node01`)
- Execution user: `hadoop`
- No HTTP auth or credentials needed — CLI uses automatic local auth

### Limitation: Cancel Run
Airflow CLI **does not have a direct command** to cancel a DAG run.
- `--cancel-all` will **pause the DAG** + report active runs
- Running tasks will complete on their own, cannot force stop via CLI
- If real cancellation is needed, use the Airflow UI on port 58080

### RPC Rate Limiting
If only 1-2 RPCs are available, origin jobs may fail with errors:
- `Max number retry` — RPC is rate limited
- `Expected BEGIN_ARRAY but was BEGIN_OBJECT` — RPC returned JSON-RPC error

**Solutions:**
1. Run `check_rpcs.py` with more RPCs
2. Increase `wait_miliseconds` in `application.properties` (default 100 → try 500)
3. Reduce `max_concurrent_blocks` (default 100 → try 10)

### DAG Auto-backfill
When unpausing a DAG, Airflow may auto-create scheduled runs for the period the DAG was paused.
- Old scheduled runs may fail due to missing `.env`
- Solution: cancel all runs before triggering manual run

### LocalExecutor
Airflow standalone uses LocalExecutor — runs **only 1 task at a time**.
- 8 Ethereum tasks may take 30-60 minutes depending on RPC speed
- Tasks run sequentially according to the dependency graph

## Real-world Example
- Date: 2026-07-11
- 12 RPCs passed (check_rpcs.py with relaxed conditions)
- 8/8 tasks succeeded
- 301 blocks, 163k transactions, 190k logs, 120k ERC20 transfers