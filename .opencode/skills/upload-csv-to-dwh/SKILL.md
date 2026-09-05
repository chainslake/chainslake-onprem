---
name: upload-csv-to-dwh
description: Upload CSV files from local machine to Data Warehouse via HDFS, create external tables for querying
---

# Skill: Upload CSV to Data Warehouse

## Description
Upload CSV files from local machine to Data Warehouse via HDFS, create external tables for querying.

## When to Use
- Need to import CSV files into the data warehouse
- CSV file is in the `chainslake/ext_upload/` project directory

## Implementation Steps

### Step 1: Create Schema (if not exists)

```bash
python query/ddl_spark.py "CREATE SCHEMA IF NOT EXISTS <schema_name>"
```

### Step 2: Upload File to HDFS

Use the upload helper (wraps `docker exec` + `hdfs dfs` internally — do NOT call `docker exec` directly):

```bash
python script/upload_hdfs.py <schema_name>.<table_name> <file_name>.csv
```

This creates the HDFS directory if it does not exist, then puts the CSV file into it.

Options:
```bash
# Skip creating the directory (already exists)
python script/upload_hdfs.py <schema_name>.<table_name> <file_name>.csv --no-mkdir

# Print the docker command without executing
python script/upload_hdfs.py <schema_name>.<table_name> <file_name>.csv --dry-run
```

### Step 3: Create External Table

```bash
python query/ddl_spark.py "
CREATE EXTERNAL TABLE <schema_name>.<table_name> (
    col1 STRING,
    col2 STRING,
    ...
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
    \"separatorChar\" = \",\",
    \"quoteChar\"     = \"\"\"
)
STORED AS TEXTFILE
LOCATION 'hdfs:///user/hive/warehouse/<schema_name>.db/<table_name>/'
"
```

### Step 4: Verify Data

```bash
python query/query_table.py "SELECT * FROM <schema_name>.<table_name> LIMIT 10"
```

## Notes / Gotchas

- **ext_upload directory**: Located at `chainslake/ext_upload/` and already mounted into container node01 at `/home/hadoop/projects/chainslake/ext_upload/`. Users only need to place files in the `chainslake/ext_upload/` directory on the host machine.
- **Updating data**: If only changing file content (without changing column structure), just re-upload the file to HDFS — no need to drop and recreate the table.
- **Metabase API vs SparkSQL**: DDL must be run via `query/ddl_spark.py` (uses Metabase API) or `spark-sql` directly on the node. `query/query_table.py` blocks DDL.
- **OpenCSVSerde**: Used for CSV files with headers. If the file has no headers, add `"skip.header.line.count" = "1"` to SERDEPROPERTIES.

## Real-world Example
- Uploaded `eth_etf_address.csv` to `ext_upload.eth_etf_address` (2026-07-11)