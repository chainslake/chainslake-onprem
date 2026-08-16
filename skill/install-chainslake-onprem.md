# Skill: Install Chainslake On-Premises

## Description
Guide for installing the Chainslake Data Warehouse system on a local machine or a dedicated server using Docker Compose.

## Applicability Conditions
- The user requests a fresh Chainslake on-prem install
- The system does not have any Docker services running yet

---

## System Requirements

- Docker >= 20.10, Docker Compose >= 2.0
- RAM >= 8 GB (16 GB recommended)
- Free disk space >= 20 GB

## Service Architecture

| Service | Description | Port |
|---|---|---|
| `postgres` | PostgreSQL — metadata for Airflow, Hive, Metabase | 5432 (internal) |
| `node01` | HDFS NameNode + DataNode, Airflow, Trino, Hive, Spark | 58080, 59870, 59001 |
| `node02` | HDFS DataNode | — |
| `metabase` | BI tool | 53000 |

---

## Step 1: Create the `.env` file

```bash
cd docker
cp env_example .env
```

Default `.env` content:

```env
POSTGRES_PASSWORD=postgresexamplepassword
POSTGRES_DATA_DIR=./postgres_data
NODE01_DATA_DIR=./hadoop_data_node01
NODE02_DATA_DIR=./hadoop_data_node02
CHAINSLAKE_HOME_DIR=/home/hadoop/projects/chainslake
CHAINSLAKE_RUN_DIR=/home/hadoop/projects/chainslake-run
```

## Step 2: Initialize the system directories

```bash
bash init_dir.sh
```

The script does:
1. Temporarily starts the `lakechain/chainslake` container → copies `/home/hadoop` out to `docker/home/`
2. Creates `hadoop_data_node01/` and `hadoop_data_node02/`

Result:

```
docker/
├── home/                    # mounted into node01
├── hadoop_data_node01/
├── hadoop_data_node02/
├── postgres_data/
├── etc/
├── docker-compose.yml
├── .env
└── init_dir.sh
```

## Step 3: Start the services

```bash
docker compose up -d
docker compose ps          # all must be in the Up state
```

## Step 4: Check Supervisord

Access `http://localhost:59001`

| Field | Value |
|---|---|
| Username | `supervisord` |
| Password | `supervisord@password` |

7 services must be in the RUNNING state: `airflow`, `hdfs-namenode`, `hdfs-secondarynamenode`, `hdfs-datanode`, `hive-metastore`, `spark-thriftserver`, `trino`.

> If some services show `STARTING`, wait 1–2 minutes then refresh.

## Step 5: Check Airflow

Access `http://localhost:58080`

| Field | Value |
|---|---|
| Username | `admin` |
| Password | Read from the file (see below) |

Get the password:

```bash
cat docker/home/projects/chainslake/airflow/standalone_admin_password.txt
```

Or via the container:

```bash
docker exec chainslake-onprem-node01-1 cat /home/hadoop/projects/chainslake/airflow/standalone_admin_password.txt
```

> The file only appears after Airflow finishes starting up for the first time. If it is not there yet, wait another 1–2 minutes.

## Step 6: Set up Metabase

### 6.1. Prepare credentials

```bash
cp script/env_example script/.env
```

Edit `script/.env`:

```env
METABASE_URL=http://localhost:53000
METABASE_EMAIL=admin@chainslake.com
METABASE_PASSWORD=<your_password_here>
METABASE_SITE_NAME=Chainslake Warehouse
```

### 6.2. Run the setup script

```bash
python script/setup_metabase.py
```

The script automatically: waits for Metabase to be ready → creates admin → creates API key → adds SparkSQL/Trino → authenticates the CLI.

Optional:
```bash
python script/setup_metabase.py --skip-databases   # skip adding DBs
python script/setup_metabase.py --skip-cli          # bypass CLI auth
```

### 6.3. Verify

- Log in to `http://localhost:53000`
- **Settings → Admin → Databases** — Spark and Trino have been added
- `query/.env` now contains `METABASE_API_KEY=...`

---

## Stop / restart

```bash
docker compose down        # stop
docker compose up -d       # start
docker compose logs -f node01   # view logs
```

---

## Troubleshooting

| Issue | How to resolve |
|---|---|
| Supervisord missing RUNNING services | Wait 2–3 minutes after `docker compose up -d`, refresh again |
| `standalone_admin_password.txt` missing | `docker exec chainslake-onprem-node01-1 tail -50 /tmp/airflow.log` — wait for Airflow to finish starting |
| Metabase cannot connect to SparkSQL | Check the Spark Thrift Server in Supervisord, restart it if it is not RUNNING |
