# Chainslake On-Premises — Blockchain Data Warehouse

**Chainslake** is a blockchain data warehouse that allows users to self-manage and operate a secure, private blockchain data analytics infrastructure. Chainslake offers both **On-Cloud** and **On-Premises** solutions to meet diverse customer needs.

This repository presents the **Onprem** solution, suitable for customers who already have hardware infrastructure or want to run experiments on a local machine.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [System Installation](#system-installation)
3. [Directory Structure](#directory-structure)
4. [`chainslake-run` Directory](#chainslake-run-directory)
5. [`chainslake` Directory](#chainslake-directory)
   - [jobs — Execution Scripts](#jobs--execution-scripts)
   - [sql — Data Transformation Logic](#sql--data-transformation-logic)
   - [evm/abi — Contract ABI](#evmabi--contract-abi)
   - [airflow/dags — Pipeline & Scheduling](#airflowdags--pipeline--scheduling)
   - [application.properties — Pipeline Configuration](#applicationproperties--pipeline-configuration)
6. [Workflow](#workflow)
7. [Detailed Example: Ethereum Pipeline](#detailed-example-ethereum-pipeline)
8. [Data Query Tools in Data Warehouse](#data-query-tools-in-data-warehouse)
9. [Contact](#contact)

---

## Architecture Overview

Chainslake Onprem is built on open-source Big Data technologies:

- **HDFS** — Distributed data storage (Delta Lake format)
- **Apache Spark** — Batch data processing and transformation
- **Apache Hive Metastore** — Table metadata management
- **Trino** — High-speed query engine for data retrieval
- **Apache Airflow** — Pipeline scheduling and management
- **Metabase** — BI interface for data analysis and visualization

The entire system is containerized with Docker, enabling quick deployment on any environment.

---

## System Installation

To install and start the Chainslake Onprem system on a local machine or private server, please read and follow the detailed instructions in:

📄 **[docker/README.md](./docker/README.md)**

The guide covers all steps:
- System requirements
- Environment configuration
- Service initialization and startup
- Verifying Supervisord, Airflow, Metabase
- Troubleshooting common issues

---

## Directory Structure

```
chainslake-onprem/
├── chainslake-run/             # Execution files and dependencies
│   ├── .env                    # Environment variables (copy from env_example)
│   ├── env_example             # Example environment variables file
│   ├── chainslake-run.sh       # spark-submit wrapper script for running jobs
│   ├── chainslake-deps.jar     # Dependency libraries
│   └── chainslake.jar          # Main execution file (contact Admin to obtain)
│
├── chainslake/                 # Source code for job configuration and execution
│   ├── jobs/                   # Shell scripts for each job
│   │   └── ethereum/
│   │       ├── application.properties
│   │       ├── origin/
│   │       ├── extract/
│   │       └── contract/
│   ├── sql/                    # SQL files for sql.transformer app
│   │   ├── evm/
│   │   └── evm_contract/
│   ├── evm/
│   │   └── abi/                # ABI files for EVM smart contracts
│   └── airflow/
│       └── dags/               # Airflow DAGs for pipeline definition and scheduling
│
└── docker/                     # Docker Compose configuration
    ├── README.md               # Installation guide
    ├── docker-compose.yml
    └── ...
```

> **Note:** Both `chainslake-run` and `chainslake` directories are mounted into `home/projects/` inside the `node01` container. See details in [docker/README.md](./docker/README.md).

---

## `chainslake-run` Directory

This directory contains the necessary components for executing Spark jobs.

### Structure

| File/Directory | Description |
|---|---|
| `env_example` | Example environment variables file, copy to `.env` and edit |
| `.env` | Actual environment variables file (not committed to git) |
| `chainslake-run.sh` | Wrapper script for `spark-submit`, the foundation for all jobs |
| `chainslake-deps.jar` | Dependency libraries (Delta Lake, Hadoop connector, etc.) |
| `chainslake.jar` | Main Chainslake execution file — **not in repo**, contact Admin to obtain |

### Setting up `.env`

```bash
cp chainslake-run/env_example chainslake-run/.env
# Open and edit values to match your environment
```

The `.env` file contains variables such as RPC endpoint lists for blockchains:

```env
ETHEREUM_RPCS=https://rpc.nodeflare.app/eth/public,...
```

These variables are loaded into the environment before running jobs that need to call RPCs directly (e.g., jobs in the `origin/` directory).

### `chainslake-run.sh`

This script is a wrapper for `spark-submit`, pre-configured with default Spark settings:

```bash
spark-submit --master local[2] \
    --driver-memory 4g \
    --deploy-mode client \
    "$@" \
    --conf "spark.app_properties.chainslake_home_dir=$CHAINSLAKE_HOME_DIR" \
    --conf "spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension" \
    --conf "spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog" \
    --jars $CHAINSLAKE_RUN_DIR/chainslake-deps.jar \
    $CHAINSLAKE_RUN_DIR/chainslake.jar
```

Each job script calls `chainslake-run.sh` and adds its own `--class`, `--name`, and `--conf` parameters.

---

## `chainslake` Directory

This directory contains all source code for configuring and orchestrating data processing jobs.

---

### `jobs` — Execution Scripts

Each `.sh` file in the `jobs/` directory represents **one job**, and each job writes data to **one table** in the data warehouse.

The `jobs/` directory structure is organized by chain and job type:

```
jobs/
└── ethereum/
    ├── application.properties   # Common configuration for Ethereum pipeline
    ├── origin/                  # Jobs that fetch raw data from RPC nodes
    │   ├── blocks_receipt.sh
    │   └── transaction_blocks.sh
    ├── extract/                 # Jobs that transform raw data into structured tables
    │   ├── blocks.sh
    │   ├── transactions.sh
    │   └── logs.sh
    └── contract/                # Jobs that decode contract data
        └── decoded_log.sh
```

Each `.sh` script calls `chainslake-run.sh` and specifies:
- `--class`: Java/Scala class to execute
- `--name`: Spark application name (for identification on Spark UI)
- `--conf spark.app_properties.app_name`: Which **app** to invoke (each app has its own logic)
- `--conf spark.app_properties.config_file`: Pipeline `application.properties` file

**Example — `extract/blocks.sh`:**

```bash
$CHAINSLAKE_RUN_DIR/chainslake-run.sh --class chainslake.sql.Main \
    --name EthereumBlocks \
    --conf "spark.app_properties.app_name=sql.transformer" \
    --conf "spark.app_properties.config_file=ethereum/application.properties" \
    --conf "spark.app_properties.sql_file=evm/blocks.sql"
```

**Example — `origin/blocks_receipt.sh`** (needs `.env` loaded because it uses RPC):

```bash
export $(cat $CHAINSLAKE_RUN_DIR/.env) && $CHAINSLAKE_RUN_DIR/chainslake-run.sh --class chainslake.evm.Main \
    --name EthereumOriginBlocksReceipt \
    --conf "spark.app_properties.app_name=evm_origin.blocks_receipt" \
    --conf "spark.app_properties.rpc_list=$ETHEREUM_RPCS" \
    --conf "spark.app_properties.config_file=ethereum/application.properties"
```

#### The `sql.transformer` App

This is a special app that allows performing data transformations purely with SQL. Instead of writing Spark code, you only need to:
1. Write a `.sql` file containing the transformation logic
2. Point the job to that `.sql` file via the `sql_file` parameter

This app reads input tables, executes the SQL, and writes results to an output table — all configuration is contained in the `.sql` file.

---

### `sql` — Data Transformation Logic

The `sql/` directory contains `.sql` files used by the `sql.transformer` app. Each `.sql` file has **two sections** separated by `===`:

```
<header section — job configuration>
===
<body section — SQL logic>
```

#### Header Section

The header contains `key=value` configurations. The two most important ones:

| Configuration | Description |
|---|---|
| `output_table` | The table where the job will write data |
| `list_input_tables` | List of tables the job reads data from (comma-separated) |

Other configurations include `partition_by`, `write_mode`, `number_index_columns`, etc.

#### Body Section

The body contains SQL statements to transform data from input tables to the output table.

#### Dynamic Variables `${}`

In `.sql` files, dynamic values use the `${}` syntax. These variables are sourced from:
- Job configuration (via `--conf` parameters)
- The `application.properties` file the job is using

Two special variables are calculated automatically by the system:

| Variable | Description |
|---|---|
| `${from}` | Starting block to process in the current run |
| `${to}` | Ending block to process in the current run |

**Example — `sql/evm/blocks.sql`:**

```sql
frequent_type=block
list_input_tables=${chain_name}_origin.transaction_blocks,${chain_name}_origin.blocks_receipt
output_table=${chain_name}.blocks
partition_by=block_date
write_mode=Append
number_index_columns=3

===

with transaction_blocks as (
    select block_date, block_number, block_time, number_tx
    from ${transaction_blocks}
    where block_number >= ${from} and block_number <= ${to}
)
, blocks_receipt as (
    select block_date, block_number, block_time, number_logs
    from ${blocks_receipt}
    where block_number >= ${from} and block_number <= ${to}
)

select t.block_date
    , t.block_number
    , t.block_time
    , t.number_tx
    , l.number_logs
from transaction_blocks t
inner join blocks_receipt l
on t.block_number = l.block_number
```

In this example:
- Input: `ethereum_origin.transaction_blocks` and `ethereum_origin.blocks_receipt`
- Output: `ethereum.blocks`
- Variable `${chain_name}` comes from `application.properties` (value: `ethereum`)
- Variables `${from}` and `${to}` are auto-calculated by the system based on processing progress

---

### `evm/abi` — Contract ABI

The `evm/abi/` directory contains ABI (Application Binary Interface) files for smart contracts on EVM blockchains. These ABI files are used to decode log data according to each contract's business logic.

**Example:** The `erc20.json` file contains the standard ERC-20 token ABI, enabling decoding of events like `Transfer` and `Approval` from raw log data.

To add a new contract for decoding, you only need to:
1. Add the contract's ABI file to this directory
2. Create a corresponding `decoded_log.sh` job and `.sql` file for the decode logic

---

### `airflow/dags` — Pipeline & Scheduling

The `airflow/dags/` directory contains **Airflow DAGs** used to define pipelines and schedule jobs. Typically, all jobs for a blockchain are grouped in a single DAG.

Airflow is accessible at:

```
http://localhost:58080
```

(See login credentials in [docker/README.md](./docker/README.md))

**Example — `dags/ethereum.py`:**

```python
with DAG(
    "Ethereum",
    schedule="10 0 * * *",   # Run at 0:10 daily
    max_active_runs=1,
    max_active_tasks=10,
    is_paused_upon_creation=True,
) as dag:

    # ORIGIN: Fetch raw data from RPC
    ethereum_origin_transaction_blocks = BashOperator(...)
    ethereum_origin_blocks_receipt = BashOperator(...)
    ethereum_origin_transaction_blocks >> ethereum_origin_blocks_receipt

    # EXTRACT: Transform into structured tables
    ethereum_blocks = BashOperator(...)
    ethereum_origin_blocks_receipt >> ethereum_blocks

    ethereum_transactions = BashOperator(...)
    ethereum_logs = BashOperator(...)
    ethereum_origin_blocks_receipt >> [ethereum_transactions, ethereum_logs]

    # DECODED: Decode contract events
    ethereum_decoded_erc20_evt_transfer = BashOperator(...)
    ethereum_logs >> ethereum_decoded_erc20_evt_transfer
```

Task dependencies (using the `>>` operator) create a clear dependency graph. Independent tasks can run in parallel (limited by `max_active_tasks`).

Enabling/disabling individual DAGs or tasks is done directly on the Airflow UI.

---

### `application.properties` — Pipeline Configuration

Each pipeline (job directory for a chain) has its own `application.properties` file. This file contains common configurations read by all jobs in the pipeline at startup.

**Example — `jobs/ethereum/application.properties`:**

```properties
chain_name=ethereum
max_number_partition=1
max_time_run=1
run_mode=backward
number_block_per_partition=300
max_retry=10
wait_miliseconds=100
```

#### Configuration Explanations

| Configuration | Description |
|---|---|
| `chain_name` | Blockchain name. Typically used as the **schema** for data warehouse tables. Example: `output_table=${chain_name}.blocks` → table `ethereum.blocks` |
| `number_block_per_partition` | Number of blocks per partition. Each partition is processed by one thread/process. Choose a value so each partition represents approximately 1 hour of data |
| `max_number_partition` | Maximum partitions processed in **one iteration**. Can run in parallel or sequentially depending on the number of cores and executors allocated in Spark. After each iteration, the job writes data to the table once |
| `max_time_run` | Maximum number of iterations in **one job run** |
| `run_mode` | `backward` or `forward`. Determines data processing direction: **backward** (from present to past, prioritizing newer data) or **forward** (from past to present). Each backward iteration still processes both new and old data (in reverse order) |
| `start_number` / `end_number` | Block range to process. `-1` means no limit |
| `max_retry` | Maximum retry count when a partition encounters an error |
| `is_alert` | Enable/disable alerts on job failures |

> In addition to the above configurations, individual jobs may have specific configurations described in their own documentation.

---

## Workflow

Below is the general data processing workflow in a Chainslake pipeline:

```
RPC Node (Blockchain)
        │
        ▼
  [origin jobs]          ← Fetch raw data, save to *_origin schema
        │
        ▼
  [extract jobs]         ← Transform and normalize data (using sql.transformer)
        │
        ▼
  [contract/decode jobs] ← Decode smart contract events using ABI
        │
        ▼
  Data Warehouse (HDFS / Delta Lake)
        │
        ▼
  Trino / SparkSQL → Metabase (BI & Visualization)
```

The entire workflow is orchestrated by **Airflow DAGs**, running on a predefined schedule and ensuring proper task dependencies.

---

## Detailed Example: Ethereum Pipeline

### Tables Created

| Schema | Table | Description |
|---|---|---|
| `ethereum_origin` | `transaction_blocks` | Raw block and transaction data from RPC |
| `ethereum_origin` | `blocks_receipt` | Raw block receipt data from RPC |
| `ethereum` | `blocks` | Normalized block table |
| `ethereum` | `transactions` | Normalized transaction table |
| `ethereum` | `logs` | Normalized raw logs table |
| `ethereum_decoded` | `erc20_evt_transfer` | Decoded ERC-20 token Transfer event |

### Running a Job Manually

To run a job manually (e.g., the `blocks` job), SSH into `node01` or exec into the container:

```bash
docker exec -it chainslake-onprem-node01-1 bash
```

Then:

```bash
cd /home/hadoop/projects/chainslake/jobs/ethereum
./extract/blocks.sh
```

Or call directly from outside with:

```bash
docker exec -u hadoop chainslake-onprem-node01-1 bash -c "export PS1='something' && source /etc/bash.bashrc && cd /home/hadoop/projects/chainslake/jobs/ethereum && ./extract/blocks.sh" 2>&1
```

### Adding a New Pipeline (Example: BNB Chain)

1. Create directory `chainslake/jobs/bnb/`
2. Create `application.properties` with `chain_name=bnb`
3. Create `.sh` scripts for each job (origin, extract, contract)
4. Create new DAG `chainslake/airflow/dags/bnb.py`
5. If new contract decoding is needed, add ABI to `chainslake/evm/abi/`

---

## Data Query Tools in Data Warehouse

To use the data query tools in the Data Warehouse, refer to:

📄 **[query/README.md](./query/README.md)**

The guide covers:
- Library installation
- API Key configuration
- Script list and usage:
    - `get_example_table.py` — Fetch sample records from a table
    - `query_table.py` — Execute SQL queries
    - `drop_table.py` — Drop a table

---

## Contact

The `chainslake.jar` file (main execution file) **is not distributed in this repository**. To obtain this file, please contact the Chainslake Admin.

For technical issues or installation support, please create an issue on this repository.