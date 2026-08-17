---
name: build-catalog
description: Create markdown catalog documentation for all tables in the data warehouse — metadata, schema, data examples, and lineage graph
---

# Skill: Build Data Warehouse Catalog

## Description
Create markdown catalog documentation for all tables in the data warehouse, including metadata, schema, data examples, and lineage graph.

## When to Use
- When the user requests creating/updating the warehouse catalog
- When you need to snapshot the current state of all tables in the DWH
- After adding a new pipeline to update the catalog

## Implementation Steps

### Step 1: Run build_catalog.py Script
```bash
python script/build_catalog.py
```

Optional parameters:
- `--skip-count`: Skip row counting (faster, useful for large warehouses)
- `--skip-example`: Skip fetching data examples
- `--output-dir <path>`: Specify different output directory (default: `catalog/`)

### Step 2: Check Output
The `catalog/` directory will contain:
- `lineage.md`: Mermaid graph showing upstream/downstream relationships
- `[schema].[table].md`: Per-table markdown file with:
  - Status (creation date, update, rows, files, size, block range)
  - Lineage (upstream/downstream)
  - Schema (columns + types)
  - Data examples
  - SQL Transform (if present in tblproperties)
  - ABI (if present in tblproperties)

### Step 3: Review and Commit
```bash
git add catalog/
git commit -m "Update DWH catalog"
```

## Notes / Gotchas
- The script reads `METABASE_API_KEY` from `query/.env` — ensure this file exists and is valid
- The script uses the Spark engine (not Trino) for queries
- If the warehouse has many tables, the script will run slowly due to querying each table individually
- `sqlSource` and `abi` only appear in tblproperties if the pipeline has written them there
- If tblproperties don't have `sqlSource`/`abi`, the markdown file won't have SQL Transform/ABI sections

## Real-world Example
Script was created per request for the first warehouse catalog build.