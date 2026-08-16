# Skill: Run DAG and Verify Data

## Description
Trigger an Airflow DAG (Ethereum by default), monitor its progress until completion, and verify the data in the tables after the run.

## Applicability Conditions
- Docker containers are running (`docker compose up -d`)
- Airflow is operational (port 58080)
- The DAG exists and is configured correctly
- RPC endpoints are configured in `chainslake-run/.env`

## Steps

### Step 1: Check that `.env` has RPCs

```bash
cat chainslake-run/.env
```

If missing or empty, run `python script/check_rpcs.py <chain_id>` first.

### Step 2: Trigger and monitor the DAG

```bash
python script/trigger_dag.py Ethereum
```

The script runs the Airflow CLI inside the container via `docker exec`:
1. Pause the DAG to avoid conflicts with running runs
2. Unpause the DAG
3. Trigger a manual run
4. Poll status every 30s until success/failed

**Optional parameters:**
```bash
# Trigger and exit immediately (do not wait)
python script/trigger_dag.py Ethereum --no-wait

# Only view status
python script/trigger_dag.py Ethereum --status

# Pause the DAG and view active runs
python script/trigger_dag.py Ethereum --cancel-all

# Custom poll interval
python script/trigger_dag.py Ethereum --poll-interval 60
```

### Step 3: Verify the data

After the DAG succeeds, check the data:

```bash
# Check the row count of each table
python query/query_table.py "SELECT count(*) as total FROM ethereum.blocks LIMIT 1"
python query/query_table.py "SELECT count(*) as total FROM ethereum.transactions LIMIT 1"
python query/query_table.py "SELECT count(*) as total FROM ethereum.logs LIMIT 1"
python query/query_table.py "SELECT count(*) as total FROM ethereum_decoded.erc20_evt_transfer LIMIT 1"
python query/query_table.py "SELECT count(*) as total FROM ethereum_contract.erc20_tokens LIMIT 1"
python query/query_table.py "SELECT count(*) as total FROM ethereum_token.erc20_transfer LIMIT 1"

# View the schema and sample data
python query/get_example_table.py ethereum.blocks
python query/get_example_table.py ethereum.transactions
```

## Ethereum DAG dependency graph

```
origin.transaction_blocks → origin.blocks_receipt
origin.blocks_receipt → [blocks, transactions, logs]
logs → decoded.erc20_evt_transfer
decoded.erc20_evt_transfer → contract.erc20_tokens
[transactions, decoded.erc20_evt_transfer, contract.erc20_tokens] → token.erc20_transfer
```

8 tasks, running sequentially under LocalExecutor.

## Notes / Gotchas

### Airflow CLI
The script uses `docker exec` to call the `airflow` CLI inside the `chainslake-onprem-node01-1` container.
- The container must be running (`docker ps | grep node01`)
- Executing user: `hadoop`
- No HTTP auth or credentials needed — the CLI uses local auth automatically

### Limitation: Cancelling a run
The Airflow CLI **has no direct command** to cancel a DAG run.
- `--cancel-all` will **pause the DAG** + report the active runs
- Running tasks will finish on their own; they cannot be force-stopped via the CLI
- If you really need to cancel, use the Airflow UI on port 58080

### RPC rate limiting
If there are only 1-2 RPCs, the origin job may fail with errors:
- `Max number retry` — RPC is rate limited
- `Expected BEGIN_ARRAY but was BEGIN_OBJECT` — RPC returned a JSON-RPC error

**Solutions:**
1. Run `check_rpcs.py` with more RPCs
2. Increase `wait_miliseconds` in `application.properties` (default 100 → try 500)
3. Reduce `max_concurrent_blocks` (default 100 → try 10)

### DAG auto-backfill
When unpausing the DAG, Airflow may automatically create scheduled runs for the period the DAG was paused.
- Old scheduled runs may fail due to missing `.env`
- Solution: cancel all runs before triggering a manual run

### LocalExecutor
Airflow standalone uses LocalExecutor — it only runs **1 task at a time**.
- The 8 Ethereum tasks can take 30-60 minutes depending on RPC speed
- Tasks run sequentially according to the dependency graph

## Real-World Example
- Date: 2026-07-11
- 12 RPCs passed (check_rpcs.py with relaxed conditions)
- 8/8 tasks succeeded
- 301 blocks, 163k transactions, 190k logs, 120k ERC20 transfers
