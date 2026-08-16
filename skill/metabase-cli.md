# Skill: Metabase CLI (`mb`) — Managing Metabase Content

## Description
Using the Metabase CLI (`mb`) to manage databases, cards, dashboards, collections, transforms, and search content on the on-premise Metabase. The CLI is the primary tool for the Agent to interact with Metabase instead of calling the API directly.

## Applicability Conditions
- Metabase CLI installed: `npm install -g @metabase/cli`
- Authenticated: `mb auth login --url http://localhost:53000 --api-key <KEY>`
- Metabase v0.58+ (currently v0.62.4.3)

## General Rules

### Output format
- Default: human-readable text
- Add `--json` to get JSON (for scripts/agents)
- `--full` to get all fields
- `--fields a,b,c` to project specific fields

### Check auth before operating
```bash
mb auth status --json
```
If not authenticated → `mb auth login --url http://localhost:53000 --api-key <KEY>`

---

## Steps

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

# Manually sync schema (when adding a new table)
mb db sync-schema <db-id>

# Rescan field values (when data changes)
mb db rescan-values <db-id>
```

**For Chainslake projects:**
- SparkSQL database = id 2
- Trino database = id 3

```bash
# Sync schema for Spark
mb db sync-schema 2

# View all schemas in Spark
mb db schemas 2

# View tables in the ethereum schema
mb db schema-tables 2 ethereum
```

### 2. Table & Field Metadata

```bash
# List tables (can filter by database)
mb table list --db-id 2

# View table details with fields
mb table get <table-id> --include fields

# List fields of a table
mb table fields <table-id>

# Update display name, description for a table
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

# Create a new card (native SQL question)
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

# Create a card (MBQL question)
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

# Run a card and get JSON results
mb card query <card-id> --export-format json

# Export a card to CSV
mb card query <card-id> --export-format csv > result.csv

# Update a card
mb card update <card-id> --body '{"name":"Updated Name"}'

# Archive a card (soft-delete)
mb card archive <card-id>
```

### 4. Dashboards

```bash
# List dashboards
mb dashboard list

# View a dashboard with its dashcards
mb dashboard get <dashboard-id>

# Create a new dashboard
mb dashboard create --body '{
  "name": "Ethereum Overview",
  "description": "Overview of Ethereum blockchain data"
}'

# Add dashcards to a dashboard
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
# Grid 24 columns. size_x=24 = full width, size_x=12 = half

# Update a specific dashcard
mb dashboard update-dashcard <dashboard-id> <dashcard-id> --body '{
  "col": 0, "row": 6, "size_x": 24, "size_y": 4
}'

# Add a filter (parameter) to the dashboard
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

# View selectable values for a parameter
mb dashboard parameter-values <dashboard-id> <parameter-id>

# Archive a dashboard
mb dashboard archive <dashboard-id>
```

### 5. Collections

```bash
# List collections
mb collection list

# View the tree hierarchy (JSON only)
mb collection tree --json

# View items in a collection
mb collection items <collection-id>

# Create a new collection
mb collection create --body '{
  "name": "Ethereum Analytics",
  "description": "Dashboards and questions for Ethereum"
}'

# Archive a collection
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

# View a specific setting
mb setting get site-name

# Change a setting
mb setting set site-name '"Chainslake Warehouse"'
# Note: the value must be valid JSON — strings need double quotes
```

### 8. Snippets (Native Query)

```bash
# List snippets
mb snippet list

# Create a new snippet
mb snippet create --body '{
  "name": "ethereum_tables",
  "description": "List of ethereum tables",
  "content": "SELECT table_name FROM information_schema.tables WHERE table_schema = '\''ethereum'\''"
}'

# Update a snippet
mb snippet update <snippet-id> --body '{"content":"..."}'

# Archive a snippet
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
# Upload a new CSV (creates table + model)
mb upload csv --file data.csv

# Append to an existing table
mb upload append <table-id> --file new_data.csv

# Replace table data
mb upload replace <table-id> --file updated_data.csv
```

---

## Common Workflows

### Verifying new data after running a pipeline
```bash
# 1. Sync the schema
mb db sync-schema 2

# 2. Find the new table
mb search "blocks" --models table

# 3. View the table's fields
mb table get <table-id> --include fields
```

### Creating a dashboard from scratch
```bash
# 1. Create a collection
COLLECTION_ID=$(mb collection create --body '{"name":"My Dashboard"}' --json | jq -r '.id')

# 2. Create cards
CARD1=$(mb card create --body '{"name":"Card 1",...}' --json | jq -r '.id')
CARD2=$(mb card create --body '{"name":"Card 2",...}' --json | jq -r '.id')

# 3. Create a dashboard with dashcards
mb dashboard create --body "{
  \"name\": \"My Dashboard\",
  \"collection_id\": $COLLECTION_ID,
  \"dashcards\": [
    {\"card_id\": $CARD1, \"col\": 0, \"row\": 0, \"size_x\": 12, \"size_y\": 6},
    {\"card_id\": $CARD2, \"col\": 12, \"row\": 0, \"size_x\": 12, \"size_y\": 6}
  ]
}"
```

### Exporting query results
```bash
# Run a card and export CSV
mb card query 42 --export-format csv > result.csv

# Run native SQL via the query command
mb query --body '{
  "type": "native",
  "native": {"query": "SELECT * FROM ethereum.blocks LIMIT 10"},
  "database": 2
}' --json
```

---

## Notes / Gotchas

### Grid layout for dashboards
- Dashboard grid is **24 columns** wide
- `size_x = 24` → full width
- `size_x = 12` → half width
- `col + size_x ≤ 24`, no overlap

### `mb setup` is only used once
- `mb setup` only runs on an instance that **has not been set up**
- If an admin already exists → error

### API key vs Browser OAuth
- `mb auth login --api-key <KEY>` — headless, suitable for CI/agents
- `mb auth login` (without --api-key) — opens browser OAuth (requires v0.62+)

### Body JSON format
- Create/update accept the body via `--body '<JSON>'` or `--file <path>`
- String values need double quotes: `'"value"'`
- Boolean: `true`/`false`
- Number: bare

### Entity ID
- Metabase uses entity_id (NanoID) for many resources
- Use `mb eid --model <model> <eid>` to convert to a numeric id
- Entity IDs can start with `-` → use `--body` instead of a positional arg

---

## Real-World Example
- Date: 2026-07-12
- Metabase v0.62.4.3 OSS
- Metabase CLI v0.2.1
- Used for: syncing schemas, finding tables, creating cards, managing dashboards
