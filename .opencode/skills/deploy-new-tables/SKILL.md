---
name: deploy-new-tables
description: Deploy new tables/jobs from dev environment (_dev suffix) to production — remove _dev suffix, reset properties, clean up _dev tables, run UAT for 5 days, add to DAG
---

# Skill: Deploy New Tables

## Description
Guide to deploying tables/jobs that have completed the DEV-TEST loop from `_dev` tables to production: prepare code to remove `_dev`, reset properties, clean up `_dev` tables, create UAT.md, run 5-day trial according to lineage, and configure daily run + add to DAG.

## When to Use

- Problem folder `docs/<problem-name>/` has completed the DEV-TEST loop:
  - `design/` — design from Data Architect
  - `development.md` — job information from Developer
  - `test/` — test cases that PASSED from Tester
- Tables have been developed with `_dev` suffix (created by Developer)

## Input

- Problem folder `docs/<problem-name>/` — completed DEV-TEST loop:
  - `design/` — design from Data Architect
  - `development.md` — job information from Developer (list of developed jobs, input/output _dev tables, job run scripts)
  - `test/` — test cases that PASSED from Tester

## Background Knowledge

- Directory structure: `chainslake/jobs/<chain_name>/{origin,extract,contract,token}/`
- Naming conventions, SQL format, application.properties
- Properties: `fromBlock/toBlock` (block) vs `fromEpochSecond/toEpochSecond` (time), `frequenceType`, `run_mode` `backward`/`forward`
- `chainslake/` is automatically mounted into the container (volume `../chainslake` → `/home/hadoop/projects/chainslake`) — deploying a DAG only requires writing files, NO docker operations needed

## Implementation Steps

### Step 1: Prepare Code (Remove _dev suffix)

- Read `development.md` to get the list of developed jobs.
- For each job, remove `_dev` suffix:
  - Rename output table: `arbitrum.erc20_transfer_dev` → `arbitrum.erc20_transfer`
  - Rename input tables (if inputs are also `_dev`)
  - Rename `.sh` files to remove `_dev`
  - Edit `.sh`/`.sql` content: replace `_dev` table names with correct names
- **If file name conflicts with existing file** (updating old table): overwrite old file with new file.
- **IMPORTANT**: Do NOT drop old tables, only update properties.

### Step 2: Reset Properties (to re-run from beginning)

After renaming, update properties so tables re-run from the beginning:

- **Tables running `backward`**:
  - `fromBlock = toBlock + 1` (or `fromEpochSecond = toEpochSecond`)
  - → Next run will process from toBlock backwards
- **Tables running `forward`**:
  - `toBlock = fromBlock - 1` (or `toEpochSecond = fromEpochSecond`)
  - → Next run will process from the beginning

Run on production table:
```bash
python query/ddl_spark.py "ALTER TABLE <schema>.<table> SET TBLPROPERTIES (fromBlock=<value>)"
```

### Step 3: Clean Up _dev Tables

Drop `_dev` data tables from the data warehouse:
```bash
python query/drop_table.py <schema>.<table>_dev
```

### Step 4: Create UAT.md File

- Create `docs/<problem-name>/UAT.md` following the `template/UAT.md` template
- Leave Resource config and results sections empty (to be filled after running)

### Step 5: Run 5-Day Trial

- Configure job in `.sh` to run 5 days of data (instead of all).
- Trigger manually following the **lineage order** designed by the Architect (read lineage from `design/`: upstream must run before downstream).
- **Resource shortage** error → adjust: reduce `max_number_partition` + increase `max_time_run`.
- **Logic** error → return to team-lead for Developer to handle.
- After completion, collect:
  - Run time
  - Data range processed (from-to)
  - Output size (record count, file size)
- Update information in `docs/<problem-name>/UAT.md`.

### Step 6: Configure Daily Run

- Readjust job configuration: process 1 day of data per run.
- Add job to DAG following the designed lineage: create/edit file `chainslake/airflow/dags/<chain>.py` (the `chainslake/` directory is automatically mounted into the container — NO docker operations needed).

## Tools Used

- `python query/query_table.py "<SQL>"` — verify data (SELECT with LIMIT only)
- `python query/ddl_spark.py "<SQL>"` — set TBLPROPERTIES / DDL on production table
- `python query/drop_table.py <table>` — drop `_dev` table
- `python query/check_table_properties.py <table>` — check tblproperties
- `python script/run_job.py <job_ref>` — run job
- `python script/trigger_dag.py <dag>` — trigger DAG

## Notes / Gotchas

- **Do NOT drop old tables when updating**: only update properties, don't drop production tables that have data
- **Reset properties with correct run_mode**: `backward` → set `fromBlock = toBlock+1`; `forward` → set `toBlock = fromBlock-1` (setting opposite will process wrong range)
- **Run in lineage order**: upstream must finish before downstream, otherwise downstream jobs won't have data to process
- **Resource shortage ≠ logic error**: reduce `max_number_partition` + increase `max_time_run` for RAM/thread issues; logic errors go back to Developer
- **DAG deployment doesn't need docker**: `chainslake/` is already mounted in the container, just write files to `chainslake/airflow/dags/<chain>.py`

## Real-world Example

- Problem daily_dex_token_volume: after Developer completed `_dev` jobs and Tester PASSED, DataOps removed `_dev`, reset properties according to design (`backward`), created UAT.md, ran 5-day trial following lineage, then added jobs to `chainslake/airflow/dags/ethereum.py`.