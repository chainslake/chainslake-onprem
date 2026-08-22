---
name: develop-new-tables
description: Develop new pipeline jobs (.sh/.sql/ABI) from the Data Architect's design in docs/<problem>/design — clone template, shallow clone inputs to _dev, test with small data via run_job.py, update development.md
---

# Skill: Develop New Tables

## Description
Guide to developing pipeline jobs that create tables according to the Data Architect's design: clone a similar existing job, shallow clone input tables to `_dev`, write code with `_dev` output, test with small data, and record results in `development.md`.

## When to Use
- Problem folder `docs/<problem-name>/design/` contains tables that need developing.
- **Check specialized skills FIRST** — if the task matches one below, use that skill instead of this generic process:
  - `add-contract-decode-job` — decode smart contract events → `<chain>_decoded.<table>`
  - `add-contract-info-job` — contract metadata (name, symbol, decimals) → `<chain>_contract.<table>`
  - `add-new-chain-pipeline` — complete pipeline for a new EVM chain

## Input
- Problem folder `docs/<problem-name>/design/` — table designs from Data Architect.

## Implementation Steps

### Step 1: Read the Design
- Read all files in `docs/<problem-name>/design/` to understand tables to develop (schema, columns, sources, lineage).
- If the directory is empty or no tables need developing → return "No tables to develop".

### Step 2: Check Specialized Skills
- If any table's task matches `add-contract-decode-job` / `add-contract-info-job` / `add-new-chain-pipeline` → invoke that skill for those tables; only fall back to this generic flow when no skill matches.

### Step 3: Clone a Similar Existing Job
- Find an existing `.sh`/`.sql` of the same job type (origin / extract / contract decode / token aggregation) and clone it, then modify according to design.
- **Clone, do NOT edit old files in place** during development.

### Step 4: Shallow Clone Input Tables
Dev jobs do NOT read production tables directly:
```bash
python query/shallow_clone.py <schema>.<source_table>          # creates <schema>.<source_table>_dev
python query/shallow_clone.py <schema>.<source_table> --limit 1000   # only N rows (faster tests)
python query/shallow_clone.py <schema>.<source_table> --target <other_name>_dev
```

### Step 5: Write Code with `_dev` Suffix
- Output table must have `_dev` suffix: e.g. `arbitrum.erc20_transfer_dev`.
- `list_input_tables` must point to `_dev` versions of inputs.
- `.sh` calls `chainslake-run.sh` with `--class`, `--name` (`<ChainName><JobName>` PascalCase), `--conf`.
- `.sql` has header (key=value) + `===` + body; variables `${chain_name}`, `${from}`, `${to}`, `${table_name}`.

### Step 6: Test with Small Data
- Configure the job to run a small amount of data (1 hour / 1 day) instead of everything — via `--conf` overrides or TBLPROPERTIES on `_dev` tables.
- Run via the job runner tool (do NOT call `docker exec` directly):
```bash
python script/run_job.py <chain>/<category>/<job>.sh --timeout 600
```

### Step 7: Verify Output and Iterate
```bash
python query/query_table.py "SELECT count(*) FROM <schema>.<table>_dev"
python query/query_table.py "SELECT * FROM <schema>.<table>_dev LIMIT 5"
```
- Success → move to the next table.
- Failure → analyze logs yourself, fix, rerun before escalating.

### Step 8: Update development.md
- Update `docs/<problem-name>/development.md` following `template/development.md`: per table list job run script, input `_dev` tables, output `_dev` table.

## Mandatory Rules

- **`_dev` suffix**: ALL output tables during development have `_dev` suffix.
- **Shallow clone inputs**: never read production tables from dev jobs.
- **Small data test**: always test with 1 hour / 1 day of data first.
- **Clone old files**: updating an existing table → clone to new file, don't edit production code directly.

## Tools Used

- `python script/run_job.py <job_ref>` — run test jobs
- `python query/shallow_clone.py <source>` — shallow clone production table to `_dev`
- `python query/query_table.py "<SQL>"` — verify data (SELECT with LIMIT)
- `python query/set_table_property.py "<SQL>"` — adjust properties on `_dev` tables if needed

## Notes / Gotchas

- **MUST read `CODING_CONVENTIONS.md`** before writing code — pipeline structure, naming conventions, DAG structure.
- `guide_book.md` covers job mechanics (properties, `run_mode`, partition, backward/forward) — read ONLY relevant sections, not the whole file.
- Directory structure: `chainslake/jobs/<chain_name>/{origin,extract,contract,token}/`.
- If design turns out infeasible (missing columns, wrong types, insufficient source data) → report DESIGN issue back to team-lead, do NOT improvise the design yourself.

## Real-world Example

- Problem `daily_dex_token_volume`: developed DEX swap decoded tables + `ethereum_token.erc20_transfer` using this flow — cloned templates, shallow cloned `ethereum.logs` / `ethereum.transactions`, tested each job on 1 hour of data, then recorded all jobs in `development.md` before handing over to Tester.
