---
name: install-chainslake-onprem
description: Guide to installing the Chainslake Data Warehouse system on a local machine or private server using Docker Compose
---

# Skill: Install Chainslake On-Premises

## Description
Guide to installing the Chainslake Data Warehouse system on a local machine or private server using Docker Compose.

## When to Use
- User requests installing Chainslake on-prem from scratch
- No Docker services are currently running

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

## Step 1: Create `.env` File

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

## Step 2: Initialize System Directories

```bash
bash init_dir.sh
```

Script performs:
1. Starts temporary container `lakechain/chainslake` → copies `/home/hadoop` to `docker/home/`
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

## Step 3: Start Services

```bash
docker compose up -d
docker compose ps          # all should be in Up state
```

## Step 4: Verify Supervisord

Access `http://localhost:59001`

| Field | Value |
|---|---|
| Username | `supervisord` |
| Password | `supervisord@password` |

7 services must be RUNNING: `airflow`, `hdfs-namenode`, `hdfs-secondarynamenode`, `hdfs-datanode`, `hive-metastore`, `spark-thriftserver`, `trino`.

> If some services are `STARTING`, wait 1-2 minutes and refresh.

## Step 5: Verify Airflow

Access `http://localhost:58080`

| Field | Value |
|---|---|
| Username | `admin` |
| Password | Read from file (see below) |

Get the password:

```bash
cat docker/home/projects/chainslake/airflow/standalone_admin_password.txt
```

Or via container:

```bash
docker exec chainslake-onprem-node01-1 cat /home/hadoop/projects/chainslake/airflow/standalone_admin_password.txt
```

> This file only appears after Airflow finishes its first startup. If not present, wait another 1-2 minutes.

## Step 6: Set Up Metabase

### 6.1. Prepare Credentials

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

### 6.2. Run Setup Script

```bash
python script/setup_metabase.py
```

Script automatically: waits for Metabase to be ready → creates admin → creates API key → adds SparkSQL/Trino → authenticates CLI.

Options:
```bash
python script/setup_metabase.py --skip-databases   # skip adding databases
python script/setup_metabase.py --skip-cli          # bypass CLI auth
```

### 6.3. Verify

- Login to `http://localhost:53000`
- **Settings → Admin → Databases** — Spark and Trino have been added
- `query/.env` has `METABASE_API_KEY=...`

---

## Stop / Restart

```bash
docker compose down        # stop
docker compose up -d       # start
docker compose logs -f node01   # view logs
```

---

## Troubleshooting

| Issue | Solution |
|---|---|
| Supervisord missing RUNNING services | Wait 2-3 minutes after `docker compose up -d`, refresh again |
| Missing `standalone_admin_password.txt` | `docker exec chainslake-onprem-node01-1 tail -50 /tmp/airflow.log` — wait for Airflow to finish starting |
| Metabase can't connect to SparkSQL | Check Spark Thrift Server on Supervisord, restart if not RUNNING |