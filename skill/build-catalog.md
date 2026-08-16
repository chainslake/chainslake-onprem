# Skill: Build Data Warehouse Catalog

## Description
Create markdown catalog documentation for all tables in the data warehouse, including metadata, schema, sample data, and the lineage graph.

## Applicability Conditions
- When the user requests to create/update the warehouse catalog
- When a snapshot of the current state of all tables in the DWH is needed
- After adding a new pipeline to update the catalog

## Steps

### Step 1: Run the build_catalog.py script
```bash
python script/build_catalog.py
```

Optional parameters:
- `--skip-count`: Skip row counting (runs faster, useful when the warehouse is large)
- `--skip-example`: Skip fetching sample data
- `--output-dir <path>`: Specify a different output directory (default: `catalog/`)

### Step 2: Verify the output
The `catalog/` directory will contain:
- `lineage.md`: Mermaid graph showing upstream/downstream
- `[schema].[table].md`: Per-table markdown file with:
  - Status (created date, updated, rows, files, size, block range)
  - Lineage (upstream/downstream)
  - Schema (columns + types)
  - Sample data
  - SQL Transform (if present in tblproperties)
  - ABI (if present in tblproperties)

### Step 3: Review and commit
```bash
git add catalog/
git commit -m "Update DWH catalog"
```

## Notes / Gotchas
- The script reads `METABASE_API_KEY` from `query/.env` — make sure this file exists and is valid
- The script uses the Spark engine (not Trino) to query
- If the warehouse has many tables, the script will run slowly because it queries each table individually
- `sqlSource` and `abi` only appear in tblproperties if the pipeline wrote them there
- If tblproperties has no `sqlSource`/`abi`, the markdown file will not have the SQL Transform/ABI sections

## Real-World Example
The script was created to fulfill the first warehouse catalog build request.
