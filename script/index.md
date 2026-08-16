# Script Index

This directory contains Python scripts written by the Agent to serve recurring tasks or tasks that need special tools.

> **Guidance for the Agent**: Before writing a new script, check this index to avoid duplication. After writing a new script, update this index immediately.

> **Credentials configuration**: All credentials live in `script/.env` (gitignored). Copy `script/env_example` to `script/.env` and fill in the actual values.

---

## check_rpcs.py
- **Purpose**: Check the RPC list of any EVM chain from chainlist.org. Verify that each RPC fully supports the 3 required APIs (eth_blockNumber, eth_getBlockByNumber, eth_getBlockReceipts) and print a `<ENV_VAR>=...` string to paste into `.env`.
- **Input**:
  - Positional: `chain` — chain ID (number, e.g. `56`) or chain name (substring, e.g. `"BNB Smart Chain Mainnet"`)
  - `--timeout` — per-request timeout (seconds, default 10)
  - `--workers` — number of parallel threads (default 10)
  - `--env-var` — output environment variable name (default: inferred from the chain name, e.g. `BNB_RPCS`)
- **Output**: PASS/FAIL per RPC + a `<ENV_VAR>=<rpc1,rpc2,...>` line to copy into `chainslake-run/.env`
- **Example**:
  - `python script/check_rpcs.py 56`
  - `python script/check_rpcs.py 1 --env-var ETHEREUM_RPCS`

---

## setup_metabase.py
- **Purpose**: Set up Metabase on-premise from scratch: create admin account, create API key, add SparkSQL/Trino database connections, authenticate Metabase CLI (`mb`).
- **Config**: Read from `script/.env` — `METABASE_URL`, `METABASE_EMAIL`, `METABASE_PASSWORD`, `METABASE_SITE_NAME`
- **Input**:
  - `--skip-databases` — Skip the database-adding step
  - `--skip-cli` — Skip the Metabase CLI setup step
  - `--api-key-file` — Path to write the `.env` file containing the API key (default: `query/.env`)
- **Output**: Admin account, API key in `query/.env`, database connections, CLI authenticated
- **Example**:
  - `python script/setup_metabase.py`
  - `python script/setup_metabase.py --skip-databases`
  - `python script/setup_metabase.py --skip-cli`

---

## trigger_dag.py
- **Purpose**: Trigger and monitor Airflow DAG runs via the Airflow CLI (docker exec). Supports checking status and pausing DAGs.
- **Config**: No credentials needed — runs the CLI directly inside the `chainslake-onprem-node01-1` container
- **Input**:
  - Positional: `dag_id` — DAG name (e.g. `Ethereum`)
  - `--cancel-all` — Pause the DAG and view active runs
  - `--status` — View status of the most recent DAG runs
  - `--no-wait` — Trigger then exit immediately
  - `--poll-interval` — Poll interval (seconds, default 30)
  - `--max-wait` — Maximum wait time (seconds, default 3600)
- **Output**: Trigger DAG, display task states in real-time, return exit code 0 on success
- **Example**:
  - `python script/trigger_dag.py Ethereum`
  - `python script/trigger_dag.py Ethereum --status`
  - `python script/trigger_dag.py Ethereum --cancel-all`

---

## build_catalog.py
- **Purpose**: Collect metadata from all tables in the data warehouse and generate markdown catalog documentation (per-table + lineage graph)
- **Config**: Read `METABASE_API_KEY` and `METABASE_URL` from `query/.env`
- **Input**:
  - `--output-dir` — Output directory (default: `catalog/`)
  - `--skip-count` — Skip counting rows (runs faster)
  - `--skip-example` — Skip fetching example data
- **Output**: `catalog/` directory containing a `[schema].[table].md` file for each table + `lineage.md` with a Mermaid graph
- **Example**:
  - `python script/build_catalog.py`
  - `python script/build_catalog.py --skip-count`
  - `python script/build_catalog.py --output-dir /tmp/catalog`
