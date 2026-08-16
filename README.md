# Chainslake On-Premises — Blockchain Data Warehouse

**Chainslake** is a blockchain data warehouse that lets users manage and operate their own blockchain data analytics infrastructure in a secure and private way. Chainslake provides both **On-Cloud** and **On-Premises** solutions to suit the needs of different customers.

This repository introduces the **Onprem** solution, suitable for customers who already have hardware infrastructure or want to run a trial on a local machine.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [System Installation](#system-installation)
3. [Directory Structure](#directory-structure)
4. [The `chainslake-run` Directory](#the-chainslake-run-directory)
5. [The `chainslake` Directory](#the-chainslake-directory)
   - [jobs — Execution Scripts](#jobs--execution-scripts)
   - [sql — Data Transformation Logic](#sql--data-transformation-logic)
   - [evm/abi — Contract ABI](#evmabi--contract-abi)
   - [airflow/dags — Pipeline & Scheduling](#airflowdags--pipeline--scheduling)
   - [application.properties — Pipeline Configuration](#applicationproperties--pipeline-configuration)
6. [Data Flow](#data-flow)
7. [Detailed Example: Ethereum Pipeline](#detailed-example-ethereum-pipeline)
8. [Data Warehouse Query Tools](#data-warehouse-query-tools)
9. [Contact](#contact)

---

## Architecture Overview

Chainslake Onprem is built on open-source Big Data technologies:

- **HDFS** — Distributed data storage (Delta Lake format)
- **Apache Spark** — Batch data processing and transformation
- **Apache Hive Metastore** — Table metadata management
- **Trino** — High-speed query engine for data queries
- **Apache Airflow** — Pipeline scheduling and management
- **Metabase** — BI interface for data analysis and visualization

The entire system is packaged in Docker, enabling fast deployment on any environment.

---

## System Installation

To install and start the Chainslake Onprem system on a local machine or dedicated server, read and follow the detailed instructions in:

📄 **[docker/README.md](./docker/README.md)**

That guide covers all the steps:
- System requirements
- Environment configuration
- Initializing and starting the services
- Checking Supervisord, Airflow, Metabase
- Troubleshooting common issues

---

## Directory Structure

```
chainslake-onprem/
├── chainslake-run/             # Executable files and dependency libraries
│   ├── .env                    # Environment variables (copy from env_example)
│   ├── env_example             # Environment variable template file
│   ├── chainslake-run.sh       # spark-submit command to run jobs
│   ├── chainslake-deps.jar     # Dependency libraries
│   └── chainslake.jar          # Main executable (contact Admin to obtain)
│
├── chainslake/                 # Source code for configuring and executing jobs
│   ├── jobs/                   # .sh scripts for each job
│   │   └── ethereum/
│   │       ├── application.properties
│   │       ├── origin/
│   │       ├── extract/
│   │       └── contract/
│   ├── sql/                    # .sql files for the sql.transformer app
│   │   ├── evm/
│   │   └── evm_contract/
│   ├── evm/
│   │   └── abi/                # ABIs of EVM smart contracts
│   └── airflow/
│       └── dags/               # Airflow DAGs to build pipelines and schedule
│
└── docker/                     # Docker Compose configuration
    ├── README.md               # Installation guide
    ├── docker-compose.yml
    └── ...
```

> **Note:** Both the `chainslake-run` and `chainslake` directories are mounted into `home/projects/` inside the `node01` container. See details in [docker/README.md](./docker/README.md).

---

## The `chainslake-run` Directory

This directory contains the components required to execute Spark jobs.

### Structure

| File/Directory | Description |
|---|---|
| `env_example` | Template file containing environment variables; copy it to `.env` and edit |
| `.env` | Actual environment variable file (must not be committed to git) |
| `chainslake-run.sh` | Wrapper script for `spark-submit`, the foundation for every job |
| `chainslake-deps.jar` | Dependency libraries (Delta Lake, Hadoop connector, etc.) |
| `chainslake.jar` | Chainslake's main executable — **not included in the repo**, contact Admin to obtain it |

### Setting up `.env`

```bash
cp chainslake-run/env_example chainslake-run/.env
# Open and edit the values to match your environment
```

The `.env` file contains variables such as the list of RPC endpoints for the blockchains:

```env
ETHEREUM_RPCS=https://rpc.nodeflare.app/eth/public,...
```

These variables are loaded into the environment before running jobs that call RPC directly (e.g., the jobs in the `origin/` directory).

### `chainslake-run.sh`

This script is a wrapper for `spark-submit` and pre-configures the default Spark settings:

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

## The `chainslake` Directory

This directory contains all the source code to configure and orchestrate the data processing jobs.

---

### `jobs` — Execution Scripts

Each `.sh` file in the `jobs/` directory represents **one job**, and each job writes data to **one table** in the data warehouse.

The `jobs/` directory is organized by chain and job type:

```
jobs/
└── ethereum/
    ├── application.properties   # Common configuration for the Ethereum pipeline
    ├── origin/                  # Jobs that fetch raw data from the RPC node
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
- `--class`: The Java/Scala class to execute
- `--name`: The Spark application name (used for identification on the Spark UI)
- `--conf spark.app_properties.app_name`: **Which app** to call (each app has its own logic)
- `--conf spark.app_properties.config_file`: The pipeline's `application.properties` file

**Example — `extract/blocks.sh`:**

```bash
$CHAINSLAKE_RUN_DIR/chainslake-run.sh --class chainslake.sql.Main \
    --name EthereumBlocks \
    --conf "spark.app_properties.app_name=sql.transformer" \
    --conf "spark.app_properties.config_file=ethereum/application.properties" \
    --conf "spark.app_properties.sql_file=evm/blocks.sql"
```

**Example — `origin/blocks_receipt.sh`** (needs to load `.env` because it uses RPC):

```bash
export $(cat $CHAINSLAKE_RUN_DIR/.env) && $CHAINSLAKE_RUN_DIR/chainslake-run.sh --class chainslake.evm.Main \
    --name EthereumOriginBlocksReceipt \
    --conf "spark.app_properties.app_name=evm_origin.blocks_receipt" \
    --conf "spark.app_properties.rpc_list=$ETHEREUM_RPCS" \
    --conf "spark.app_properties.config_file=ethereum/application.properties"
```

#### The `sql.transformer` app

This is a special app that performs a data transformation purely with SQL. Instead of writing Spark code, you only need to:
1. Write a `.sql` file containing the transformation logic
2. Point the job to that `.sql` file via the `sql_file` parameter

This app reads the input tables, executes the SQL, and writes the result to the output table — all configuration lives in the `.sql` file.

---

### `sql` — Data Transformation Logic

The `sql/` directory contains the `.sql` files used by the `sql.transformer` app. Each `.sql` file consists of **two parts** separated by `===`:

```
<header part — job configuration>
===
<body part — SQL logic>
```

#### Header Part

The header part contains `key=value` configuration entries. The two most important ones:

| Config | Description |
|---|---|
| `output_table` | The table the job writes data to |
| `list_input_tables` | The list of tables the job reads data from (comma-separated) |

There are also other configs such as `partition_by`, `write_mode`, `number_index_columns`, etc.

#### Body Part

The body part contains the SQL statement that transforms the input tables into the output table.

#### `${}` Dynamic Variables

In the `.sql` file, dynamic values are placed inside the `${}` syntax. These variables come from:
- The job configuration (`--conf` parameters)
- The `application.properties` file used by the job

Two special variables are computed automatically by the system:

| Variable | Description |
|---|---|
| `${from}` | The starting block processed in the current run |
| `${to}` | The ending block processed in the current run |

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
- The `${chain_name}` variable comes from `application.properties` (value: `ethereum`)
- The `${from}` and `${to}` variables are computed by the system based on processing progress

---

### `evm/abi` — Contract ABI

The `evm/abi/` directory contains ABI (Application Binary Interface) files of smart contracts on EVM blockchains. These ABI files are used to decode log data according to each contract's business logic.

**Example:** The `erc20.json` file contains the standard ERC-20 token ABI, which allows decoding events such as `Transfer` and `Approval` from raw log data.

When adding a new contract to decode, you only need to:
1. Add the contract's ABI file to this directory
2. Create the corresponding `decoded_log.sh` job and the `.sql` file to handle the decode logic

---

### `airflow/dags` — Pipeline & Scheduling

The `airflow/dags/` directory contains the **Airflow DAGs** used to define pipelines and schedule job runs. Typically, all jobs of a blockchain are placed together in one DAG.

Airflow is accessible at:

```
http://localhost:58080
```

(See login credentials in [docker/README.md](./docker/README.md))

**Example — `dags/ethereum.py`:**

```python
with DAG(
    "Ethereum",
    schedule="10 0 * * *",   # Runs at 0:10 every day
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

The dependencies between tasks (using the `>>` operator) form a clear dependency graph. Tasks that do not depend on each other can run in parallel (limited by `max_active_tasks`).

Enabling/disabling each DAG or task is done directly on the Airflow UI.

---

### `application.properties` — Pipeline Configuration

Each pipeline (the job directory of a chain) has its own `application.properties` file. This file contains the common configuration that every job in the pipeline reads at startup.

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

#### Configuration explanations

| Config | Description |
|---|---|
| `chain_name` | The name of the blockchain. Usually used as the **schema** for the data warehouse tables. For example: `output_table=${chain_name}.blocks` → table `ethereum.blocks` |
| `number_block_per_partition` | Number of blocks in each partition. Each partition is processed by one thread/process. Choose it so that each partition corresponds to roughly 1 hour of data |
| `max_number_partition` | Maximum number of partitions processed in **one loop**. They can run in parallel or sequentially depending on the number of cores and executors allocated in Spark. After each loop, the job writes data to the table once |
| `max_time_run` | Maximum number of loops in **one job run** |
| `run_mode` | `backward` or `forward`. Determines the data processing direction: **backward** (from present to past, prioritizing the newest data) or **forward** (from past to present). Each backward loop still processes both new and old data (in reverse order) |
| `start_number` / `end_number` | The range of blocks to process. `-1` means no limit |
| `max_retry` | Maximum number of retries when a partition fails |
| `is_alert` | Enables/disables alerts when a job fails |

> In addition to the above, each job may have additional specific configurations described in that job's documentation.

---

## Data Flow

Below is the overall data processing flow in a Chainslake pipeline:

```
RPC Node (Blockchain)
        │
        ▼
  [origin jobs]          ← Fetch raw data, store in the *_origin schema
        │
        ▼
  [extract jobs]         ← Transform and normalize data (using sql.transformer)
        │
        ▼
  [contract/decode jobs] ← Decode smart contract events according to the ABI
        │
        ▼
  Data Warehouse (HDFS / Delta Lake)
        │
        ▼
  Trino / SparkSQL → Metabase (BI & Visualization)
```

The entire flow is orchestrated by **Airflow DAGs**, runs on a predefined schedule, and ensures the dependency order between the steps.

---

## Detailed Example: Ethereum Pipeline

### Tables produced

| Schema | Table | Description |
|---|---|---|
| `ethereum_origin` | `transaction_blocks` | Raw block and transaction data from RPC |
| `ethereum_origin` | `blocks_receipt` | Raw block receipt data from RPC |
| `ethereum` | `blocks` | Normalized block table |
| `ethereum` | `transactions` | Normalized transaction table |
| `ethereum` | `logs` | Normalized raw logs table |
| `ethereum_decoded` | `erc20_evt_transfer` | Decoded Transfer event of ERC-20 tokens |

### Running a job manually

To run a job manually (e.g., the `blocks` job), SSH into `node01` or exec into the container:

```bash
docker exec -it chainslake-onprem-node01-1 bash
```

Then:

```bash
cd /home/hadoop/projects/chainslake/jobs/ethereum
./extract/blocks.sh
```

Or call it directly from outside with the following command:

```bash
docker exec -u hadoop chainslake-onprem-node01-1 bash -c "export PS1='something' && source /etc/bash.bashrc && cd /home/hadoop/projects/chainslake/jobs/ethereum && ./extract/blocks.sh" 2>&1
```

### Adding a new pipeline (e.g., BNB Chain)

1. Create the directory `chainslake/jobs/bnb/`
2. Create an `application.properties` file with `chain_name=bnb`
3. Create the `.sh` scripts for each job (origin, extract, contract)
4. Create a new DAG `chainslake/airflow/dags/bnb.py`
5. If a new contract needs decoding, add its ABI to `chainslake/evm/abi/`

---

## Data Warehouse Query Tools

To use the Data Warehouse query tools, refer to the following documentation:

📄 **[query/README.md](./query/README.md)**

That guide covers:
- Library installation
- API Key configuration
- The list of scripts and how to use them:
    - `get_example_table.py` — Fetch a sample record from a table
    - `query_table.py` — Execute a SQL query
    - `drop_table.py` — Drop a table

---

## Contact

The `chainslake.jar` file (the main executable) is **not distributed in this repository**. To obtain this file, please contact the Chainslake Admin.

For technical issues or installation support, please create an issue on this repository.
