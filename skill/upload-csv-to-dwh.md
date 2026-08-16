# Skill: Upload CSV to Data Warehouse

## Description
Upload a CSV file from the local machine to the Data Warehouse via HDFS, then create an external table for querying.

## Applicability Conditions
- Need to import a CSV file into the data warehouse
- The CSV file is located in the `chainslake/ext_upload/` directory of the project

## Steps

### Step 1: Create the schema (if it does not exist)

```bash
python query/ddl_spark.py "CREATE SCHEMA IF NOT EXISTS <schema_name>"
```

### Step 2: Upload the file to HDFS

```bash
docker exec -u hadoop chainslake-onprem-node01-1 bash -c \
  "export PS1='something' && source /etc/bash.bashrc && \
   hdfs dfs -mkdir -p /user/hive/warehouse/<schema_name>.db/<table_name> && \
   hdfs dfs -put /home/hadoop/projects/chainslake/ext_upload/<file_name>.csv /user/hive/warehouse/<schema_name>.db/<table_name>/"
```

### Step 3: Create the external table

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

### Step 4: Verify the data

```bash
python query/query_table.py "SELECT * FROM <schema_name>.<table_name> LIMIT 10"
```

## Notes / Gotchas

- **ext_upload directory**: Located at `chainslake/ext_upload/` and already mounted into the node01 container at `/home/hadoop/projects/chainslake/ext_upload/`. The user only needs to drop the file into the `chainslake/ext_upload/` directory on the host machine.
- **Updating data**: If only the file content changes (not the column structure), just re-upload the file to HDFS; no need to drop and recreate the table.
- **Metabase API vs SparkSQL**: DDL must be run via `query/ddl_spark.py` (uses the Metabase API) or `spark-sql` directly on the node. `query/query_table.py` blocks DDL.
- **OpenCSVSerde**: Used for CSV files with a header. If the file has no header, add `"skip.header.line.count" = "1"` to the SERDEPROPERTIES.

## Real-World Example
- Uploaded `eth_etf_address.csv` to `ext_upload.eth_etf_address` (2026-07-11)
