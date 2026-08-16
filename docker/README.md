# Chainslake Warehouse — Docker Installation Guide

This document provides step-by-step instructions for installing the **Chainslake Data Warehouse** on a local machine using Docker Compose.

---

## System Requirements

- **Docker** >= 20.10
- **Docker Compose** >= 2.0
- Minimum RAM: 8 GB (16 GB recommended)
- Free disk space: at least 20 GB

---

## System Architecture

The system consists of 4 main Docker services:

| Service    | Description                                                                           | Port          |
|------------|---------------------------------------------------------------------------------------|---------------|
| `postgres`  | PostgreSQL database — stores metadata for Airflow, Hive Metastore and Metabase       | 5432 (internal) |
| `node01`   | Main Hadoop node: runs HDFS NameNode + DataNode, Airflow, Trino, Hive, Spark         | 58080, 59870, 59001 |
| `node02`   | Second Hadoop node: runs HDFS DataNode                                                | —             |
| `metabase` | Metabase application for querying data and creating charts                            | 53000         |

---

## Step 1: Prepare the environment configuration

### 1.1. Create the `.env` file

Copy the template file and edit it to match your environment:

```bash
cp env_example .env
```

Contents of the `.env` file:

```env
# PostgreSQL password (replace with a stronger password for production deployments)
POSTGRES_PASSWORD=postgresexamplepassword

# Directory to store PostgreSQL data 
POSTGRES_DATA_DIR=./postgres_data

# HDFS data directory for each node
NODE01_DATA_DIR=./hadoop_data_node01
NODE02_DATA_DIR=./hadoop_data_node02

# Paths inside the container
CHAINSLAKE_HOME_DIR=/home/hadoop/projects/chainslake
CHAINSLAKE_RUN_DIR=/home/hadoop/projects/chainslake-run
```

---

## Step 2: Initialize the system directories

Run the `init_dir.sh` script to create the required directories:

```bash
bash init_dir.sh
```

This script performs the following:

1. Temporarily starts a `lakechain/chainslake` container and copies the `/home/hadoop` directory out to a `home/` directory — this is the directory that holds all of the system's code, configuration and runtime data.
2. Creates the `hadoop_data_node01/` directory — stores node01's HDFS data.
3. Creates the `hadoop_data_node02/` directory — stores node02's HDFS data.

After running, the directory structure will look like this:

```
docker/
├── home/                    # Home directory of the hadoop user, mounted into node01
├── hadoop_data_node01/      # HDFS data of node01
├── hadoop_data_node02/      # HDFS data of node02
├── postgres_data/           # PostgreSQL data (created automatically if missing)
├── etc/                     # Configuration files of the services
├── docker-compose.yml
├── .env
└── init_dir.sh
```

> **Note:** If you do not have `sudo` privileges, the `chown` command in the script may be skipped. The directories will still be created with ownership of the current user and will work normally.

---

## Step 3: Start the services

```bash
docker compose up -d
```

Docker Compose will create and start all services. Expected result:

```
✔ Network chainslake-onprem-network  Created
✔ Container chainslake-onprem-postgres-1  Started
✔ Container chainslake-onprem-node02-1    Started
✔ Container chainslake-onprem-node01-1    Started
✔ Container chainslake-onprem-metabase-1  Started
```

Check the status of the containers:

```bash
docker compose ps
```

All containers must be in the `Up` state:

```
NAME                           SERVICE    STATUS    PORTS
chainslake-onprem-postgres-1   postgres   Up        5432/tcp
chainslake-onprem-node02-1     node02     Up
chainslake-onprem-node01-1     node01     Up        0.0.0.0:58080->8080/tcp, 0.0.0.0:59001->9001/tcp, 0.0.0.0:59870->9870/tcp
chainslake-onprem-metabase-1   metabase   Up        0.0.0.0:53000->3000/tcp
```

---

## Step 4: Check Supervisord (localhost:59001)

**Supervisord** is the tool that manages the processes running inside `node01`. After startup, access:

```
http://localhost:59001
```

### Login credentials

Find the username and password in the `etc/supervisord_node01.conf` file:

```ini
[inet_http_server]
port=0.0.0.0:9001
username=supervisord
password=supervisord@password
```

| Field    | Value                |
|----------|----------------------|
| Username | `supervisord`        |
| Password | `supervisord@password` |

### Managed services

After logging in, you will see the list of services and their status. All must be in the **RUNNING** state:

| Service                 | Description                                   |
|-------------------------|-----------------------------------------------|
| `airflow`               | Airflow scheduler & web server                |
| `hdfs-namenode`         | HDFS NameNode                                 |
| `hdfs-secondarynamenode`| HDFS Secondary NameNode                       |
| `hdfs-datanode`         | HDFS DataNode on node01                       |
| `hive-metastore`        | Hive Metastore service                        |
| `spark-thriftserver`    | Spark Thrift Server (JDBC/ODBC)               |
| `trino`                 | Trino query engine                            |

> **Note:** The services may take 1–2 minutes to fully start after the container starts. If some services are in the `STARTING` state, wait a bit longer and refresh the page.

---

## Step 5: Check Airflow (localhost:58080)

**Apache Airflow** is used to schedule and manage the data pipelines. Access:

```
http://localhost:58080
```

### Login credentials

| Field    | Value                                  |
|----------|----------------------------------------|
| Username | `admin`                                |
| Password | See the description below              |

The password is auto-generated by Airflow on first startup. Read the password with the command:

```bash
cat home/projects/chainslake/airflow/standalone_admin_password.txt
```

Or from inside the container:

```bash
docker exec chainslake-onprem-node01-1 cat /home/hadoop/projects/chainslake/airflow/standalone_admin_password.txt
```

> **Note:** The `standalone_admin_password.txt` file only appears after Airflow has started successfully for the first time. If the file does not exist yet, wait 1–2 more minutes and re-check the `airflow` service status on Supervisord.

---

## Step 6: Set up Metabase (localhost:53000)

**Metabase** is a BI tool for querying data and creating visual charts. After all containers have fully started, run the automatic setup script from the project root directory:

### 6.1. Prepare credentials

```bash
cp script/env_example script/.env
```

Edit `script/.env` with the actual information:

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

The script automatically performs the following:
1. Waits for Metabase to be ready
2. Creates the admin account
3. Creates an API key and writes it to `query/.env`
4. Adds the SparkSQL and Trino connections
5. Authenticates the Metabase CLI (`mb`)

**Optional parameters:**

```bash
python script/setup_metabase.py --skip-databases    # Skip adding databases
python script/setup_metabase.py --skip-cli          # Bypass CLI auth
```

### 6.3. Verify the result

- Access `http://localhost:53000` — log in with the admin credentials
- Go to **Settings** → **Admin** → **Databases** — verify Spark and Trino have been added
- The `query/.env` file now contains `METABASE_API_KEY=...`

> **Note:** For detailed steps and common errors, see `skill/setup-metabase.md`.

---

## Stopping and restarting the system

Stop all services:

```bash
docker compose down
```

Restart:

```bash
docker compose up -d
```

View the logs of a service:

```bash
docker compose logs -f node01
docker compose logs -f metabase
```

---

## Common troubleshooting

**Supervisord does not show all 7 services in the RUNNING state**

The services in node01 need time to start in order. Wait 2–3 minutes after `docker compose up -d`, then refresh the Supervisord page.

---

**Cannot find the Airflow `standalone_admin_password.txt` file**

This file is only created after Airflow starts successfully for the first time. Check the Airflow logs:

```bash
docker exec chainslake-onprem-node01-1 tail -50 /tmp/airflow.log
```

---

**Metabase cannot connect to SparkSQL**

Check the Spark Thrift Server on Supervisord. If the service is not `RUNNING` yet, wait a bit longer. You can try restarting the service from the Supervisord interface.
