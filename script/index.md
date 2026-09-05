# Script Index

This directory contains Python scripts written by Agents to serve repetitive tasks or special tooling needs.

> **Agent Instructions**: Before writing a new script, check this index to avoid duplicates. After writing a new script, update this index immediately.

> **Credentials Configuration**: All credentials are in `script/.env` (gitignored). Copy `script/env_example` to `script/.env` and fill in actual values.

---

## check_rpcs.py
- **Purpose**: Check RPC list for any EVM chain from chainlist.org. Validates that each RPC fully supports the 3 required APIs (eth_blockNumber, eth_getBlockByNumber, eth_getBlockReceipts) and outputs the `<ENV_VAR>=...` string to paste into `.env`.
- **Input**:
  - Positional: `chain` — chain ID (number, e.g., `56`) or chain name (substring, e.g., `"BNB Smart Chain Mainnet"`)
  - `--timeout` — timeout per request (seconds, default 10)
  - `--workers` — number of parallel threads (default 10)
  - `--env-var` — output environment variable name (default: auto-inferred from chain name, e.g., `BNB_RPCS`)
- **Output**: PASS/FAIL per RPC + `<ENV_VAR>=<rpc1,rpc2,...>` line to copy into `chainslake-run/.env`
- **Examples**:
  - `python script/check_rpcs.py 56`
  - `python script/check_rpcs.py 1 --env-var ETHEREUM_RPCS`

---

## setup_metabase.py
- **Purpose**: Set up on-premise Metabase from scratch: create admin account, create API key, add SparkSQL/Trino database connections, authenticate Metabase CLI (`mb`).
- **Config**: Reads from `script/.env` — `METABASE_URL`, `METABASE_EMAIL`, `METABASE_PASSWORD`, `METABASE_SITE_NAME`
- **Input**:
  - `--skip-databases` — Skip adding databases
  - `--skip-cli` — Skip Metabase CLI setup
  - `--api-key-file` — Path to write `.env` file containing API key (default: `query/.env`)
- **Output**: Admin account, API key in `query/.env`, database connections, CLI authenticated
- **Examples**:
  - `python script/setup_metabase.py`
  - `python script/setup_metabase.py --skip-databases`
  - `python script/setup_metabase.py --skip-cli`

---

## trigger_dag.py
- **Purpose**: Trigger and monitor Airflow DAG runs via Airflow CLI (docker exec). Supports checking status, pausing DAG, and backfilling tasks / entire DAGs.
- **Config**: No credentials needed — runs CLI directly in `chainslake-onprem-node01-1` container
- **Input**:
  - Positional: `dag_id` — DAG name (e.g., `Ethereum`)
  - `--cancel-all` — Pause DAG and view active runs
  - `--status` — View status of recent DAG runs
  - `--no-wait` — Trigger and exit immediately
  - `--poll-interval` — Poll interval (seconds, default 30)
  - `--max-wait` — Maximum wait time (seconds, default 3600)
  - `--backfill-task DAG_ID TASK_ID EXECUTION_DATE` — Run a single task instance (backfill one task)
  - `--backfill-dag DAG_ID START_DATE END_DATE [--run-backwards]` — Backfill an entire DAG
- **Output**: Trigger DAG, display real-time task states, return exit code 0 on success
- **Examples**:
  - `python script/trigger_dag.py Ethereum`
  - `python script/trigger_dag.py Ethereum --status`
  - `python script/trigger_dag.py Ethereum --cancel-all`
  - `python script/trigger_dag.py --backfill-task BNB bnb_origin.transaction_blocks 2025-10-11`
  - `python script/trigger_dag.py --backfill-dag BNB 2025-10-11 2025-11-11 --run-backwards`

---

## upload_hdfs.py
- **Purpose**: Upload CSV files from local `chainslake/ext_upload/` to HDFS — creates the target HDFS directory if needed and puts the file (wraps `docker exec` + `hdfs dfs` internally)
- **Input**:
  - Positional 1: `schema_table` — target table `<schema>.<table>` (e.g., `ext_upload.eth_etf_address`)
  - Positional 2: `file_name` — CSV file name inside `chainslake/ext_upload/` (e.g., `eth_etf_address.csv`)
  - `--no-mkdir` — Skip creating the HDFS directory
  - `--dry-run` — Print the docker command without executing
- **Output**: Streams `hdfs dfs` output, returns exit code 0 on success
- **Examples**:
  - `python script/upload_hdfs.py ext_upload eth_etf_address.csv`
  - `python script/upload_hdfs.py ext_upload eth_etf_address.csv --dry-run`

---

## run_job.py
- **Purpose**: Run a pipeline job via docker exec (instead of manual `docker exec ...`). Streams output directly to terminal, returns the job's actual exit code. Supports listing available jobs, dry-run, timeout.
- **Input**:
  - Positional: `job` — job reference, supports multiple formats:
    - `ethereum/extract/blocks.sh` or `ethereum.extract.blocks` — full chain/category/job
    - `extract/blocks --chain ethereum` — category + job, with `--chain`
    - `blocks --chain ethereum` — job name only, with `--chain`
    - `ethereum/origin` — chain + category (auto-infers if category has only 1 file)
  - `--chain` — chain name (needed when job_ref is missing chain)
  - `--list` — list all available job scripts (optionally with `--chain`)
  - `--dry-run` — only print docker command, don't execute
  - `--timeout <seconds>` — kill job if running too long
- **Output**: Spark job output streamed in real-time, exit code matches job's exit code
- **Examples**:
  - `python script/run_job.py ethereum/extract/blocks.sh`
  - `python script/run_job.py ethereum.extract.blocks`
  - `python script/run_job.py blocks --chain ethereum`
  - `python script/run_job.py --list`
  - `python script/run_job.py ethereum/origin/transaction_blocks.sh --timeout 600`

---

## build_catalog.py
- **Purpose**: Collect metadata from all tables in the data warehouse and generate markdown catalog documentation (per-table + lineage graph)
- **Config**: Reads `METABASE_API_KEY` and `METABASE_URL` from `query/.env`
- **Input**:
  - `--output-dir` — Output directory (default: `catalog/`)
  - `--skip-count` — Skip row counting (faster)
  - `--skip-example` — Skip fetching data examples
- **Output**: `catalog/` directory containing `[schema].[table].md` for each table + `lineage.md` with Mermaid graph
- **Examples**:
  - `python script/build_catalog.py`
  - `python script/build_catalog.py --skip-count`
  - `python script/build_catalog.py --output-dir /tmp/catalog`

---

## build_lineage_from_design.py
- **Purpose**: Read Data Architect's design files in `docs/<problem>/design/` directory and generate `lineage.md` (Mermaid graph + detail table) in the design directory — indicating which tables already exist in the warehouse, which have `_dev` versions, and which need to be created from scratch
- **Config**: Queries warehouse Spark via `query/.env` (`METABASE_API_KEY`) to determine existing tables; use `--offline` to use catalog directory instead
- **Input**:
  - Positional: `problem` — problem name (subdirectory of `docs/`, e.g., `daily_dex_token_volume`)
  - `--design-dir` — Direct path to design directory (replaces `problem`)
  - `--offline` — Don't query warehouse, use catalog directory to determine existing tables
  - `--catalog-dir` — Catalog directory for `--offline` mode (default: `catalog/`)
- **Output**: `docs/<problem>/design/lineage.md` — Mermaid graph colored by status (✅ EXISTS / 🔄 DEV / ❌ NEW), detail table with status, list of existing/needs-creation tables, root/leaf tables
- **Examples**:
  - `python script/build_lineage_from_design.py daily_dex_token_volume`
  - `python script/build_lineage_from_design.py daily_dex_token_volume --offline`
  - `python script/build_lineage_from_design.py --design-dir docs/foo/design`