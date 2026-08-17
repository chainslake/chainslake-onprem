---
name: metabase-cli
description: Use Metabase CLI (`mb`) to manage databases, cards, dashboards, collections, transforms, and search content on on-premise Metabase
---

# Skill: Metabase CLI (`mb`) — Manage Metabase Content

## Description
Use Metabase CLI (`mb`) to manage databases, cards, dashboards, collections, transforms, and search content on on-premise Metabase. The CLI is the primary tool for agents to interact with Metabase instead of calling APIs directly.

## When to Use
- Metabase CLI installed: `npm install -g @metabase/cli`
- Authenticated: `mb auth login --url http://localhost:53000 --api-key <KEY>`
- Metabase v0.58+ (currently v0.62.4.3)

## General Rules

### Output Format
- Default: human-readable text
- Add `--json` for JSON output (for scripts/agents)
- `--full` for complete fields
- `--fields a,b,c` for specific projections

### Check Auth Before Operations
```bash
mb auth status --json
```
If not authenticated → `mb auth login --url http://localhost:53000 --api-key <KEY>`

---

## Implementation Steps

### 1. Database Operations

```bash
# List all databases
mb db list

# View database details (including table list)
mb db get <db-id> --include tables

# List schemas in a database
mb db schemas <db-id>

# List tables in a schema
mb db schema-tables <db-id> <schema-name>

# Manually sync schema (when new tables are added)
mb db sync-schema <db-id>

# Rescan field values (when data changes)
mb db rescan-values <db-id>
```

**In Chainslake projects:**
- SparkSQL Database = id 2
- Trino Database = id 3

```bash
# Sync schema for Spark
mb db sync-schema 2

# View all schemas in Spark
mb db schemas 2

# View tables in ethereum schema
mb db schema-tables 2 ethereum
```

### 2. Table & Field Metadata

```bash
# List tables (can filter by database)
mb table list --db-id 2

# View table details with fields
mb table get <table-id> --include fields

# List table fields
mb table fields <table-id>

# Update table display name, description
mb table update <table-id> --body '{"display_name":"Blocks","description":"Ethereum blocks data"}'

# View field details
mb field get <field-id>

# Update field metadata (semantic type, description)
mb field update <field-id> --body '{"semantic_type":"type/PK","description":"Block number"}'

# View cached distinct values
mb field values <field-id>

# View cardinality
mb field summary <field-id>
```

### 3. Cards (Questions, Models, Metrics)

```bash
# List cards
mb card list

# View card details
mb card get <card-id>

# Create new card (native SQL question)
mb card create --body '{
  "name": "Top 10 Tokens",
  "dataset_query": {
    "type": "native",
    "native": {
      "query": "SELECT token_address, COUNT(*) as transfers FROM ethereum_token.erc20_transfer GROUP BY token_address ORDER BY transfers DESC LIMIT 10",
      "template-tags": {}
    },
    "database": 2
  },
  "display": "table",
  "visualization_settings": {}
}'

# Create card (MBQL question)
mb card create --body '{
  "name": "Recent Blocks",
  "dataset_query": {
    "type": "query",
    "query": {
      "source-table": 10,
      "order-by": [["desc", ["field", 100]]],
      "limit": 20
    },
    "database": 2
  },
  "display": "table"
}'

# Run card and get JSON results
mb card query <card-id> --export-format json

# Export card to CSV
mb card query <card-id> --export-format csv > result.csv

# Update card
mb card update <card-id> --body '{"name":"Updated Name"}'

# Archive card (soft-delete)
mb card archive <card-id>
```

### 4. Dashboards

```bash
# List dashboards
mb dashboard list

# View dashboard with dashcards
mb dashboard get <dashboard-id>

# Create new dashboard
mb dashboard create --body '{
  "name": "Ethereum Overview",
  "description": "Overview of Ethereum blockchain data"
}'

# Add dashcard to dashboard
mb dashboard update <dashboard-id> --body '{
  "dashcards": [
    {
      "card_id": 1,
      "col": 0, "row": 0,
      "size_x": 12, "size_y": 6
    },
    {
      "card_id": 2,
      "col": 12, "row": 0,
      "size_x": 12, "size_y": 6
    }
  ]
}'
# Grid is 24 columns. size_x=24 = full width, size_x=12 = half

# Update specific dashcard
mb dashboard update-dashcard <dashboard-id> <dashcard-id> --body '{
  "col": 0, "row": 6, "size_x": 24, "size_y": 4
}'

# Add filter (parameter) to dashboard
mb dashboard update <dashboard-id> --body '{
  "parameters": [
    {
      "id": "chain_filter",
      "name": "Chain",
      "type": "string/=",
      "sectionId": "string"
    }
  ]
}'

# View selectable values for parameter
mb dashboard parameter-values <dashboard-id> <parameter-id>

# Archive dashboard
mb dashboard archive <dashboard-id>
```

### 5. Collections

```bash
# List collections
mb collection list

# View tree hierarchy (JSON only)
mb collection tree --json

# View items in collection
mb collection items <collection-id>

# Create new collection
mb collection create --body '{
  "name": "Ethereum Analytics",
  "description": "Dashboards and questions for Ethereum"
}'

# Archive collection
mb collection archive <collection-id>
```

### 6. Search

```bash
# Search content
mb search "ethereum"

# Search by type
mb search "blocks" --models card
mb search "overview" --models dashboard
mb search "ethereum" --models collection
```

### 7. Settings

```bash
# List all settings
mb setting list

# View specific setting
mb setting get site-name

# Change setting
mb setting set site-name '"Chainslake Warehouse"'
# Note: value must be valid JSON — strings need double quotes
```

### 8. Snippets (Native Query)

```bash
# List snippets
mb snippet list

# Create new snippet
mb snippet create --body '{
  "name": "ethereum_tables",
  "description": "List of ethereum tables",
  "content": "SELECT table_name FROM information_schema.tables WHERE table_schema = '\''ethereum'\''"
}'

# Update snippet
mb snippet update <snippet-id> --body '{"content":"..."}'

# Archive snippet
mb snippet archive <snippet-id>
```

### 9. Segments & Measures

```bash
# Segments (saved filters)
mb segment list
mb segment create --body '{
  "name": "High Value Transfers",
  "description": "Transfers > 100 ETH",
  "definition": {
    "filter": [">", ["field", 100], 100000000000000000000]
  }
}'

# Measures (saved aggregations)
mb measure list
mb measure create --body '{
  "name": "Total Transfer Volume",
  "definition": {
    "aggregation": ["sum", ["field", 101]]
  }
}'
```

### 10. Upload CSV

```bash
# Upload new CSV (create table + model)
mb upload csv --file data.csv

# Append to existing table
mb upload append <table-id> --file new_data.csv

# Replace table data
mb upload replace <table-id> --file updated_data.csv
```

---

## Common Workflows

### Check New Data After Pipeline Run
```bash
# 1. Sync schema
mb db sync-schema 2

# 2. Find new table
mb search "blocks" --models table

# 3. View table fields
mb table get <table-id> --include fields
```

### Create Dashboard from Scratch
```bash
# 1. Create collection
COLLECTION_ID=$(mb collection create --body '{"name":"My Dashboard"}' --json | jq -r '.id')

# 2. Create cards
CARD1=$(mb card create --body '{"name":"Card 1",...}' --json | jq -r '.id')
CARD2=$(mb card create --body '{"name":"Card 2",...}' --json | jq -r '.id')

# 3. Create dashboard with dashcards
mb dashboard create --body "{
  \"name\": \"My Dashboard\",
  \"collection_id\": $COLLECTION_ID,
  \"dashcards\": [
    {\"card_id\": $CARD1, \"col\": 0, \"row\": 0, \"size_x\": 12, \"size_y\": 6},
    {\"card_id\": $CARD2, \"col\": 12, \"row\": 0, \"size_x\": 12, \"size_y\": 6}
  ]
}"
```

### Export Query Results
```bash
# Run card and export CSV
mb card query 42 --export-format csv > result.csv

# Run native SQL via query command
mb query --body '{
  "type": "native",
  "native": {"query": "SELECT * FROM ethereum.blocks LIMIT 10"},
  "database": 2
}' --json
```

---

## Notes / Gotchas

### Grid Layout for Dashboards
- Dashboard grid is **24 columns** wide
- `size_x = 24` → full width
- `size_x = 12` → half width
- `col + size_x ≤ 24`, no overlap

### `mb setup` Only Works Once
- `mb setup` only runs on instances **not yet set up**
- If admin already exists → error

### API Key vs Browser OAuth
- `mb auth login --api-key <KEY>` — headless, suitable for CI/agent
- `mb auth login` (without --api-key) — opens browser OAuth (requires v0.62+)

### Body JSON Format
- Create/update accepts body via `--body '<JSON>'` or `--file <path>`
- String values need double quotes: `'"value"'`
- Boolean: `true`/`false`
- Number: bare

### Entity ID
- Metabase uses entity_id (NanoID) for many resources
- Use `mb eid --model <model> <eid>` to convert to numeric id
- Entity IDs may start with `-` → use `--body` instead of positional arg

---

## Real-world Example
- Date: 2026-07-12
- Metabase v0.62.4.3 OSS
- Metabase CLI v0.2.1
- Used for: schema sync, table search, card creation, dashboard management